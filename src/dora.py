# ai-generated: 90% - Lab 2 DORA metrics implementation aligned to METRIC-SPEC.md and the published R-01..R-21 rulebook

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from src.validation import RequestValidationError

SPEC_VERSION = "1.0.0"


def _parse_rfc3339(value: Any) -> datetime:
    if not isinstance(value, str):
        raise RequestValidationError("invalid RFC3339 timestamp")
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RequestValidationError("invalid RFC3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise RequestValidationError("invalid RFC3339 timestamp")
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _median_seconds(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    total = Decimal(ordered[midpoint - 1]) + Decimal(ordered[midpoint])
    return int((total / Decimal(2)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _quantize_rate(value: Decimal, *, places: int = 6) -> float:
    quantum = Decimal("1").scaleb(-places)
    return float(value.quantize(quantum, rounding=ROUND_HALF_UP))


def _seconds_duration(start: datetime, end: datetime) -> int:
    return int((end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).total_seconds())


def _resolve_change_id(commit: dict[str, Any], commits_by_sha: dict[str, dict[str, Any]], memo: dict[str, str]) -> str:
    sha = commit["sha"]
    if sha in memo:
        return memo[sha]
    if commit.get("reverts") is None:
        change_id = commit["change_id"]
        memo[sha] = change_id
        return change_id
    parent_sha = commit["reverts"]
    if parent_sha not in commits_by_sha:
        raise RequestValidationError("reverts names a sha that is not in the log")
    parent = commits_by_sha[parent_sha]
    memo[sha] = _resolve_change_id(parent, commits_by_sha, memo)
    return memo[sha]


def _incident_interval(incident: dict[str, Any], end_of_window: datetime) -> tuple[datetime, datetime]:
    opened = incident["opened"]
    resolved = incident.get("resolved")
    if resolved is None:
        return opened, end_of_window
    return opened, resolved


def _round_to_int(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _validate_log(events: list[Any]) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    if not isinstance(events, list):
        raise RequestValidationError("events must be an array")

    deduped: dict[str, dict[str, Any]] = {}
    for raw in events:
        if not isinstance(raw, dict):
            raise RequestValidationError("event must be an object")
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or len(event_id) < 1 or len(event_id) > 64:
            raise RequestValidationError("event_id must be a string between 1 and 64 characters")
        if event_id in deduped:
            continue
        etype = raw.get("type")
        if etype not in {"commit", "deployment", "incident"}:
            raise RequestValidationError("event type must be commit, deployment, or incident")
        try:
            instant = _parse_rfc3339(raw.get("at"))
        except RequestValidationError as exc:
            raise RequestValidationError("event at must be an RFC3339 instant") from exc

        item = {"event_id": event_id, "type": etype, "at": instant, "raw": raw}
        deduped[event_id] = item

    commit_by_sha: dict[str, dict[str, Any]] = {}
    deployment_by_id: dict[str, dict[str, Any]] = {}
    incident_by_id: dict[str, dict[str, Any]] = {}

    for event in deduped.values():
        raw = event["raw"]
        if event["type"] == "commit":
            sha = raw.get("sha")
            if not isinstance(sha, str) or sha == "":
                raise RequestValidationError("commit sha is required")
            if sha in commit_by_sha:
                raise RequestValidationError("duplicate commit sha in log")
            change_id = raw.get("change_id")
            reverts = raw.get("reverts")
            if (reverts is None) != (change_id is not None):
                raise RequestValidationError("commit change_id must be present iff reverts is null")
            commit_by_sha[sha] = {"sha": sha, "at": event["at"], "branch": raw.get("branch"), "change_id": change_id, "reverts": reverts}
        elif event["type"] == "deployment":
            deployment_id = raw.get("deployment_id")
            if not isinstance(deployment_id, str) or deployment_id == "":
                raise RequestValidationError("deployment deployment_id is required")
            if deployment_id in deployment_by_id:
                raise RequestValidationError("duplicate deployment_id in log")
            deployment_by_id[deployment_id] = {
                "deployment_id": deployment_id,
                "at": event["at"],
                "environment": raw.get("environment"),
                "outcome": raw.get("outcome"),
                "commits": raw.get("commits", []),
                "unplanned": raw.get("unplanned"),
                "caused_by": raw.get("caused_by"),
            }
        elif event["type"] == "incident":
            incident_id = raw.get("incident_id")
            if not isinstance(incident_id, str) or incident_id == "":
                raise RequestValidationError("incident incident_id is required")
            phase = raw.get("phase")
            if phase not in {"opened", "resolved"}:
                raise RequestValidationError("incident phase must be opened or resolved")
            info = incident_by_id.setdefault(
                incident_id,
                {"incident_id": incident_id, "opened": None, "resolved": None, "deployments": set()},
            )
            if phase == "opened":
                if info["opened"] is not None:
                    raise RequestValidationError("incident opened more than once")
                info["opened"] = event["at"]
            else:
                if info["resolved"] is not None:
                    raise RequestValidationError("incident resolved more than once")
                info["resolved"] = event["at"]
            for dep_id in raw.get("deployments", []):
                info["deployments"].add(dep_id)

    all_shas = set(commit_by_sha)
    for commit in commit_by_sha.values():
        if commit["reverts"] is not None and commit["reverts"] not in all_shas:
            raise RequestValidationError("reverts names a sha that is not in the log")
        if commit["reverts"] is not None and commit["change_id"] is not None:
            raise RequestValidationError("revert commits must not carry a change_id")

    for deployment in deployment_by_id.values():
        commits = deployment["commits"]
        if commits is None:
            commits = []
        if not isinstance(commits, list):
            raise RequestValidationError("deployment commits must be an array")
        for sha in commits:
            if sha not in all_shas:
                raise RequestValidationError("deployment commits names a sha that is not in the log")
        if deployment["caused_by"] is not None and deployment["caused_by"] not in incident_by_id:
            raise RequestValidationError("caused_by must reference an incident_id in the log")

    for incident_id, info in incident_by_id.items():
        if info["opened"] is None:
            raise RequestValidationError(f"incident {incident_id} has no opened event")
        if info["resolved"] is not None and info["resolved"] < info["opened"]:
            raise RequestValidationError(f"incident {incident_id} resolved before it opened")
        for deployment_id in info["deployments"]:
            if deployment_id not in deployment_by_id:
                raise RequestValidationError("incident deployments names a deployment_id that is not in the log")

    return {
        "commits": commit_by_sha,
        "deployments": deployment_by_id,
        "incidents": incident_by_id,
        "incident_groups": incident_by_id,
    }, {"commits": list(commit_by_sha.values()), "deployments": list(deployment_by_id.values()), "incidents": list(incident_by_id.values())}


def _compute_metrics(window: dict[str, str], events: list[Any]) -> dict[str, Any]:
    if not isinstance(window, dict):
        raise RequestValidationError("window is required")
    if "from" not in window or "to" not in window:
        raise RequestValidationError("window must include from and to")
    window_from = _parse_rfc3339(window["from"])
    window_to = _parse_rfc3339(window["to"])
    if window_to <= window_from:
        raise RequestValidationError("window to must be after from")

    if events is None or not isinstance(events, list):
        raise RequestValidationError("events must be an array")

    context, _ = _validate_log(events)
    commits_by_sha = context["commits"]
    deployments_by_id = context["deployments"]
    incident_groups = context["incident_groups"]

    normalized_commits = list(commits_by_sha.values())
    in_window_production = [
        deployment for deployment in deployments_by_id.values()
        if deployment.get("environment") == "production" and window_from <= deployment["at"] < window_to
    ]

    if not normalized_commits and not in_window_production:
        return {
            "spec_version": SPEC_VERSION,
            "window": {"from": window["from"], "to": window["to"]},
            "deployment_frequency_per_day": 0.0,
            "change_lead_time_seconds_p50": None,
            "failed_deployment_recovery_time_seconds_p50": None,
            "change_fail_rate": None,
            "deployment_rework_rate": None,
            "counts": {
                "deployments": 0,
                "successful_deployments": 0,
                "failed_deployments": 0,
                "recovered_failures": 0,
                "open_failures": 0,
                "rework_deployments": 0,
                "lead_time_pairs": 0,
                "changes": 0,
            },
            "anomalies": {
                "negative_lead_time_pairs": 0,
                "deployments_without_commits": 0,
                "commits_never_on_main": 0,
                "revert_chains_collapsed": 0,
                "overlapping_incident_pairs": 0,
            },
            "ground_truth": {"changes_delivered": 0, "true_change_lead_time_seconds_p50": None},
        }

    all_changes: dict[str, list[datetime]] = {}
    change_memo: dict[str, str] = {}
    for commit in normalized_commits:
        resolved_change = _resolve_change_id(commit, commits_by_sha, change_memo)
        all_changes.setdefault(resolved_change, []).append(commit["at"])

    total_divisions = (window_to - window_from).total_seconds() / 86400.0
    total_deployments = len(in_window_production)

    successful_deployments = [d for d in in_window_production if d.get("outcome") == "success"]
    failed_deployments = [d for d in in_window_production if d.get("outcome") == "failure"]

    lead_values: list[int] = []
    negative_lead_pairs = 0
    used_commits: set[str] = set()
    for deployment in sorted(successful_deployments, key=lambda item: item["at"]):
        for sha in deployment.get("commits") or []:
            if sha in used_commits:
                continue
            commit = commits_by_sha.get(sha)
            if commit is None:
                continue
            used_commits.add(sha)
            delta_seconds = _seconds_duration(commit["at"], deployment["at"])
            if delta_seconds < 0:
                negative_lead_pairs += 1
                delta_seconds = 0
            lead_values.append(delta_seconds)

    lead_time_p50 = _median_seconds(lead_values)

    # recovery times (recovered failures only)
    recovered_failures: list[int] = []
    open_failures = 0
    for deployment in sorted(failed_deployments, key=lambda item: item["at"]):
        covering = None
        matching_incidents = []
        for incident_id, info in incident_groups.items():
            opened = info.get("opened")
            resolved = info.get("resolved")
            if opened is None:
                continue
            deployment_ids = set(info.get("deployments", []))
            if deployment["deployment_id"] not in deployment_ids:
                continue
            matching_incidents.append((incident_id, opened, resolved))
        if matching_incidents:
            matching_incidents.sort(key=lambda tpl: (tpl[1], tpl[0]))
            _, opened_at, resolved_at = matching_incidents[0]
            if resolved_at is None:
                open_failures += 1
                continue
            covering = resolved_at
        else:
            open_failures += 1
            continue
        recovered_failures.append(_seconds_duration(deployment["at"], covering))

    recovery_time_p50 = _median_seconds(recovered_failures)

    # rework rate denominator
    rework_deployments = sum(
        1
        for deployment in in_window_production
        if deployment.get("unplanned") is True and deployment.get("caused_by") is not None
    )

    # open failure count is as above; recovered total = len(recovered_failures)
    counts = {
        "deployments": total_deployments,
        "successful_deployments": len(successful_deployments),
        "failed_deployments": len(failed_deployments),
        "recovered_failures": len(recovered_failures),
        "open_failures": open_failures,
        "rework_deployments": rework_deployments,
        "lead_time_pairs": len(lead_values),
        "changes": len(all_changes),
    }

    # anomalies
    deployments_without_commits = sum(1 for deployment in in_window_production if not (deployment.get("commits") or []))
    revert_chains_collapsed = sum(1 for commit in normalized_commits if commit.get("reverts") is not None)
    commits_never_on_main = len({
        sha
        for deployment in in_window_production
        for sha in (deployment.get("commits") or [])
        if commits_by_sha.get(sha, {}).get("branch") != "main"
    })

    incident_intervals: list[tuple[datetime, datetime]] = []
    for incident_id, info in incident_groups.items():
        opened = info.get("opened")
        if opened is None:
            continue
        resolved = info.get("resolved")
        end = resolved if resolved is not None else window_to
        incident_intervals.append((opened, end))
    overlapping_pairs = 0
    for i in range(len(incident_intervals)):
        for j in range(i + 1, len(incident_intervals)):
            a_start, a_end = incident_intervals[i]
            b_start, b_end = incident_intervals[j]
            if a_start < b_end and b_start < a_end:
                overlapping_pairs += 1

    anomalies = {
        "negative_lead_time_pairs": negative_lead_pairs,
        "deployments_without_commits": deployments_without_commits,
        "commits_never_on_main": commits_never_on_main,
        "revert_chains_collapsed": revert_chains_collapsed,
        "overlapping_incident_pairs": overlapping_pairs,
    }

    # ground truth
    change_ids_delivered = {
        _resolve_change_id(commits_by_sha[sha], commits_by_sha, change_memo)
        for deployment in successful_deployments
        for sha in (deployment.get("commits") or [])
        if sha in commits_by_sha
    }
    ground_truth_changes_delivered = len(change_ids_delivered)

    true_change_lead_times: list[int] = []
    for change_id in sorted(change_ids_delivered):
        change_commits = [commit["at"] for commit in normalized_commits if _resolve_change_id(commit, commits_by_sha, change_memo) == change_id]
        if not change_commits:
            continue
        earliest_commit = min(change_commits)
        first_successful_deployment = min(
            (
                deployment["at"]
                for deployment in successful_deployments
                if any(_resolve_change_id(commits_by_sha[sha], commits_by_sha, change_memo) == change_id for sha in (deployment.get("commits") or []))
            ),
            default=None,
        )
        if first_successful_deployment is None:
            continue
        delta = _seconds_duration(earliest_commit, first_successful_deployment)
        if delta < 0:
            delta = 0
        true_change_lead_times.append(delta)
    true_change_lead_time_p50 = _median_seconds(true_change_lead_times)

    deployment_frequency = None if total_deployments == 0 else Decimal(total_deployments) / Decimal(total_divisions)
    change_fail_rate = None if total_deployments == 0 else Decimal(len(failed_deployments)) / Decimal(total_deployments)
    deployment_rework_rate = None if total_deployments == 0 else Decimal(rework_deployments) / Decimal(total_deployments)

    return {
        "spec_version": SPEC_VERSION,
        "window": {"from": window["from"], "to": window["to"]},
        "deployment_frequency_per_day": float(_quantize_rate(deployment_frequency, places=6)) if deployment_frequency is not None else 0.0,
        "change_lead_time_seconds_p50": lead_time_p50,
        "failed_deployment_recovery_time_seconds_p50": recovery_time_p50,
        "change_fail_rate": _quantize_rate(change_fail_rate, places=6) if change_fail_rate is not None else None,
        "deployment_rework_rate": _quantize_rate(deployment_rework_rate, places=6) if deployment_rework_rate is not None else None,
        "counts": counts,
        "anomalies": anomalies,
        "ground_truth": {
            "changes_delivered": ground_truth_changes_delivered,
            "true_change_lead_time_seconds_p50": true_change_lead_time_p50,
        },
    }


def compute_dora_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RequestValidationError("request body must be an object")
    window = payload.get("window")
    events = payload.get("events")
    return _compute_metrics(window, events)

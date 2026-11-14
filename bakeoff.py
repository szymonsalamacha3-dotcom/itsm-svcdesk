# ai-generated: 100% - OpenAI Copilot implemented standard-library SARIF matching per Lab 5 CI-SPEC P-14..P-24
"""Compute the Lab 5 per-tool confusion matrix from SARIF and labelled defects."""

import argparse
import json
import re
from urllib.parse import unquote


CLASSES = {
    "secret",
    "injection",
    "deserialization",
    "weak-crypto",
    "insecure-transport",
    "path-traversal",
    "ssrf",
    "vulnerable-dependency",
    "misconfiguration",
    "access-control",
}

CWE_CLASSES = {
    259: "secret",
    260: "secret",
    321: "secret",
    798: "secret",
    74: "injection",
    77: "injection",
    78: "injection",
    79: "injection",
    80: "injection",
    88: "injection",
    89: "injection",
    90: "injection",
    91: "injection",
    94: "injection",
    95: "injection",
    96: "injection",
    611: "injection",
    776: "injection",
    917: "injection",
    943: "injection",
    1336: "injection",
    502: "deserialization",
    261: "weak-crypto",
    326: "weak-crypto",
    327: "weak-crypto",
    328: "weak-crypto",
    330: "weak-crypto",
    331: "weak-crypto",
    338: "weak-crypto",
    759: "weak-crypto",
    760: "weak-crypto",
    916: "weak-crypto",
    295: "insecure-transport",
    297: "insecure-transport",
    319: "insecure-transport",
    322: "insecure-transport",
    757: "insecure-transport",
    22: "path-traversal",
    23: "path-traversal",
    35: "path-traversal",
    36: "path-traversal",
    73: "path-traversal",
    918: "ssrf",
    937: "vulnerable-dependency",
    1035: "vulnerable-dependency",
    1104: "vulnerable-dependency",
    1395: "vulnerable-dependency",
    16: "misconfiguration",
    215: "misconfiguration",
    250: "misconfiguration",
    489: "misconfiguration",
    668: "misconfiguration",
    732: "misconfiguration",
    1188: "misconfiguration",
    284: "access-control",
    285: "access-control",
    639: "access-control",
    862: "access-control",
    863: "access-control",
}

SEMGREP_NAMES = {
    "semgrep",
    "semgrep oss",
    "semgrep ce",
    "semgrep community edition",
    "semgrep pro",
}


def _array(value):
    return value if isinstance(value, list) else []


def _tool_id(run):
    tool = run.get("tool")
    driver = tool.get("driver") if isinstance(tool, dict) else None
    name = driver.get("name") if isinstance(driver, dict) else None
    if not isinstance(name, str):
        return "unknown"

    normalized = name.strip().lower()
    if not normalized:
        return "unknown"
    if normalized in SEMGREP_NAMES:
        return "semgrep"
    if normalized in {"trivy", "grype", "osv-scanner", "gitleaks"}:
        return normalized
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "unknown"


def _empty_suppressions(value):
    if value is None or value is False:
        return True
    if isinstance(value, (int, float)) and value == 0:
        return True
    if isinstance(value, (str, list, dict)) and not value:
        return True
    return False


def _path_in_set(uri, set_root):
    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    parts = path.split("/")
    root_positions = [index for index, part in enumerate(parts) if part == set_root]
    if not root_positions:
        return None
    return "/".join(parts[root_positions[-1]:])


def _location(result, set_root):
    locations = _array(result.get("locations"))
    if not locations or not isinstance(locations[0], dict):
        return None
    physical = locations[0].get("physicalLocation")
    artifact = physical.get("artifactLocation") if isinstance(physical, dict) else None
    uri = artifact.get("uri") if isinstance(artifact, dict) else None
    if not isinstance(uri, str) or not uri:
        return None

    file_name = _path_in_set(uri, set_root)
    if file_name is None:
        return None

    region = physical.get("region")
    start = region.get("startLine") if isinstance(region, dict) else None
    if type(start) is not int or start < 1:
        start = None
        end = None
    else:
        end = region.get("endLine")
        if type(end) is not int or end < start:
            end = start
    return file_name, start, end


def _matching_rule(run, result):
    result_rule_id = result.get("ruleId")
    if result_rule_id is None:
        return None
    tool = run.get("tool")
    driver = tool.get("driver") if isinstance(tool, dict) else None
    rules = _array(driver.get("rules")) if isinstance(driver, dict) else []
    for rule in rules:
        if isinstance(rule, dict) and rule.get("id") is not None:
            if type(rule.get("id")) is type(result_rule_id) and rule.get("id") == result_rule_id:
                return rule
    return None


def _tags(properties):
    if not isinstance(properties, dict):
        return []
    return [tag for tag in _array(properties.get("tags")) if isinstance(tag, str)]


def _result_classes(tool_id, result, rule):
    result_properties = result.get("properties")
    own_class = result_properties.get("class") if isinstance(result_properties, dict) else None
    if isinstance(own_class, str) and own_class in CLASSES:
        return {own_class}

    if tool_id == "gitleaks":
        return {"secret"}
    if tool_id in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}
    if tool_id == "trivy":
        rule_properties = rule.get("properties") if isinstance(rule, dict) else None
        trivy_classes = {
            {"vulnerability": "vulnerable-dependency", "secret": "secret", "misconfiguration": "misconfiguration"}[tag.lower()]
            for tag in _tags(rule_properties)
            if tag.lower() in {"vulnerability", "secret", "misconfiguration"}
        }
        if trivy_classes:
            return trivy_classes

    result_tags = _tags(result_properties)
    rule_properties = rule.get("properties") if isinstance(rule, dict) else None
    rule_tags = _tags(rule_properties)
    found = set()
    for tag in result_tags + rule_tags:
        for match in re.finditer(r"(?<![A-Za-z0-9])CWE-([0-9]+)", tag, re.IGNORECASE):
            cwe_class = CWE_CLASSES.get(int(match.group(1)))
            if cwe_class:
                found.add(cwe_class)
    return found or {"other"}


def _normalized_package(name):
    return re.sub(r"[-_.]+", "-", name.lower())


def _names_package(message, package):
    if not isinstance(message, dict) or not isinstance(message.get("text"), str):
        return False
    expected = _normalized_package(package)
    for token in re.findall(r"[A-Za-z0-9._-]+", message["text"]):
        normalized = _normalized_package(token.strip("._-"))
        if normalized and normalized == expected:
            return True
    return False


def _matches(result_record, defect):
    if result_record["file"] != defect["file"]:
        return False
    if defect["class"] not in result_record["classes"]:
        return False
    if defect["class"] == "vulnerable-dependency":
        return _names_package(result_record["message"], defect["package"])
    start = result_record["start"]
    end = result_record["end"]
    return (
        start is not None
        and end is not None
        and start <= defect["end_line"]
        and defect["start_line"] <= end
    )


def _accepted_result(result):
    kind = result.get("kind")
    if kind is not None and kind != "fail":
        return False
    return _empty_suppressions(result.get("suppressions"))


def _result_record(run, result, set_root):
    if not isinstance(result, dict) or not _accepted_result(result):
        return None
    location = _location(result, set_root)
    if location is None:
        return None
    tool_id = _tool_id(run)
    rule = _matching_rule(run, result)
    rule_id = result.get("ruleId")
    if not isinstance(rule_id, str):
        rule_id = None
    return {
        "tool": tool_id,
        "rule_id": rule_id,
        "file": location[0],
        "start": location[1],
        "end": location[2],
        "classes": _result_classes(tool_id, result, rule),
        "message": result.get("message"),
    }


def calculate(labels, sarif_documents):
    set_root = labels["set"]
    defects = labels["defects"]
    per_tool = {}

    for document in sarif_documents:
        for run in _array(document.get("runs")):
            if not isinstance(run, dict):
                continue
            tool_id = _tool_id(run)
            counts = per_tool.setdefault(tool_id, {"matched": set(), "false_positives": set()})
            for result in _array(run.get("results")):
                record = _result_record(run, result, set_root)
                if record is None:
                    continue
                matched = {
                    index
                    for index, defect in enumerate(defects)
                    if _matches(record, defect)
                }
                if matched:
                    counts["matched"].update(matched)
                else:
                    counts["false_positives"].add(
                        (record["rule_id"], record["file"], record["start"], record["end"])
                    )

    tools = {}
    for tool_id in sorted(per_tool):
        counts = per_tool[tool_id]
        tp = len(counts["matched"])
        fn = len(defects) - tp
        fp = len(counts["false_positives"])
        precision_denominator = tp + fp
        recall_denominator = tp + fn
        f1_denominator = 2 * tp + fp + fn
        tools[tool_id] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(tp / precision_denominator, 4) if precision_denominator else None,
            "recall": round(tp / recall_denominator, 4) if recall_denominator else None,
            "f1": round(2 * tp / f1_denominator, 4) if f1_denominator else None,
        }

    return {"set": set_root, "defects": len(defects), "tools": tools}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", required=True, help="path to the labelled defects JSON file")
    parser.add_argument("sarif", nargs="+", help="one or more SARIF 2.1.0 files")
    arguments = parser.parse_args()

    with open(arguments.labels, encoding="utf-8") as labels_file:
        labels = json.load(labels_file)
    documents = []
    for path in arguments.sarif:
        with open(path, encoding="utf-8") as sarif_file:
            documents.append(json.load(sarif_file))
    print(json.dumps(calculate(labels, documents), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

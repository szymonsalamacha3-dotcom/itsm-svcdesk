# ai-generated: 90% - Lab 2 regression tests covering the published practice fixture, API contract, and ticket event export

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from src import main
from src.persistence import TicketStore


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "svcdesk.db"
    monkeypatch.setenv("SVCDESK_DB_PATH", str(db_path))
    monkeypatch.setenv("SVCDESK_TEST_CLOCK", "1")
    main.store = TicketStore(str(db_path))
    main.store.init_db()
    return TestClient(main.app)


def _read_fixture(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_metrics_fixture_matches_service(client):
    fixture = _read_fixture("fixtures/metrics-practice.json")
    with open("fixtures/events-practice.jsonl", "r", encoding="utf-8") as handle:
        events = [json.loads(line) for line in handle if line.strip()]

    response = client.post(
        "/dora/metrics",
        json={"window": fixture["window"], "events": events},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for key in [
        "deployment_frequency_per_day",
        "change_lead_time_seconds_p50",
        "failed_deployment_recovery_time_seconds_p50",
        "change_fail_rate",
        "deployment_rework_rate",
    ]:
        assert body[key] == fixture[key]
    assert body["counts"] == fixture["counts"]
    assert body["anomalies"] == fixture["anomalies"]
    assert body["ground_truth"] == fixture["ground_truth"]
    assert body["window"] == fixture["window"]
    assert body["spec_version"] == "1.0.0"


def test_ticket_events_export_contains_lifecycle_stream(client):
    created = client.post(
        "/tickets",
        json={
            "title": "Ticket export",
            "description": "example",
            "reporter": {"name": "Anna"},
            "impact": 1,
            "urgency": 2,
        },
    )
    ticket = created.json()
    ticket_id = ticket["id"]

    client.post(f"/tickets/{ticket_id}/ack")
    client.post(f"/tickets/{ticket_id}/start")
    client.post(f"/tickets/{ticket_id}/resolve")
    client.post(f"/tickets/{ticket_id}/close")

    response = client.get("/dora/ticket-events")
    assert response.status_code == 200
    stream = response.json()
    assert any(event["ticket_id"] == ticket_id and event["phase"] == "created" for event in stream)
    assert any(event["ticket_id"] == ticket_id and event["phase"] == "acknowledged" for event in stream)
    assert any(event["ticket_id"] == ticket_id and event["phase"] == "resolved" for event in stream)
    assert any(event["ticket_id"] == ticket_id and event["phase"] == "closed" for event in stream)

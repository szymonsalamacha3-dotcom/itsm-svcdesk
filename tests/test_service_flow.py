# ai-generated: 90% - end-to-end service checks for T04-T12 covering create, list, transition, and SLA behavior

from __future__ import annotations

import os

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


def test_create_and_list_ticket(client):
    payload = {
        "title": "Printer down",
        "description": "Floor 2 printer is down",
        "reporter": {"name": "Anna Nowak", "email": "anna@example.com", "vip": False},
        "impact": 1,
        "urgency": 2,
    }
    response = client.post("/tickets", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["priority"] == "P2"
    assert body["state"] == "new"
    assert body["sla"]["ack_due_at"]

    listed = client.get("/tickets?state=new")
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())


def test_state_machine_and_reopen(client):
    create = client.post(
        "/tickets",
        json={
            "title": "VPN outage",
            "reporter": {"name": "John"},
            "impact": 2,
            "urgency": 1,
        },
    )
    ticket_id = create.json()["id"]

    ack = client.post(f"/tickets/{ticket_id}/ack")
    assert ack.status_code == 200
    assert ack.json()["state"] == "acknowledged"

    start = client.post(f"/tickets/{ticket_id}/start")
    assert start.status_code == 200
    assert start.json()["state"] == "in_progress"

    resolve = client.post(f"/tickets/{ticket_id}/resolve")
    assert resolve.status_code == 200
    assert resolve.json()["state"] == "resolved"

    close = client.post(f"/tickets/{ticket_id}/close")
    assert close.status_code == 200
    assert close.json()["state"] == "closed"

    reopen = client.post(f"/tickets/{ticket_id}/reopen")
    assert reopen.status_code == 409


def test_sla_and_test_clock(client):
    response = client.post(
        "/tickets",
        headers={"X-Test-Clock": "2026-10-14T10:00:00Z"},
        json={
            "title": "P1 ticket",
            "reporter": {"name": "Admin"},
            "impact": 1,
            "urgency": 1,
        },
    )
    ticket = response.json()
    assert ticket["created_at"] == "2026-10-14T10:00:00Z"
    assert ticket["sla"]["ack_due_at"] == "2026-10-14T10:15:00Z"
    assert ticket["sla"]["resolve_due_at"] == "2026-10-14T14:00:00Z"

    sla = client.get(f"/tickets/{ticket['id']}/sla")
    assert sla.status_code == 200
    body = sla.json()
    assert body["priority"] == "P1"
    assert body["ack_due_at"] == "2026-10-14T10:15:00Z"
    assert body["resolve_due_at"] == "2026-10-14T14:00:00Z"

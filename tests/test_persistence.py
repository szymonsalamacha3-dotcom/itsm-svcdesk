# ai-generated: 80% - persistence tests focused on SQLite durability and storage behavior only for T02

from __future__ import annotations

from src.persistence import TicketStore


def test_database_bootstrap_creates_schema(tmp_path):
    db_path = tmp_path / "svcdesk.db"
    store = TicketStore(str(db_path))

    store.init_db()

    assert db_path.exists()
    assert store.list_tickets() == []


def test_ticket_id_is_unique_and_persisted(tmp_path):
    db_path = tmp_path / "svcdesk.db"
    store = TicketStore(str(db_path))
    store.init_db()

    first = store.create_ticket({
        "title": "Printer issue",
        "description": "Printer is down",
        "reporter": {"name": "Anna Nowak", "email": "anna@example.com", "vip": False},
        "impact": 2,
        "urgency": 1,
        "priority": "P2",
        "state": "new",
        "created_at": "2026-10-14T10:00:00Z",
        "sla": {"ack_due_at": "2026-10-14T10:15:00Z", "resolve_due_at": "2026-10-14T14:00:00Z"},
    })
    second = store.create_ticket({
        "title": "VPN issue",
        "description": "VPN stops working",
        "reporter": {"name": "John Smith", "email": "john@example.com", "vip": True},
        "impact": 1,
        "urgency": 1,
        "priority": "P1",
        "state": "new",
        "created_at": "2026-10-15T10:00:00Z",
        "sla": {"ack_due_at": "2026-10-15T10:15:00Z", "resolve_due_at": "2026-10-15T14:00:00Z"},
    })

    assert first["id"]
    assert second["id"]
    assert first["id"] != second["id"]
    assert first["title"] == "Printer issue"
    assert second["priority"] == "P1"

    reloaded = store.get_ticket(first["id"])
    assert reloaded is not None
    assert reloaded["title"] == "Printer issue"
    assert reloaded["sla"]["resolve_due_at"] == "2026-10-14T14:00:00Z"


def test_store_survives_reopen_with_same_db_path(tmp_path):
    db_path = tmp_path / "svcdesk.db"
    first_store = TicketStore(str(db_path))
    first_store.init_db()

    created = first_store.create_ticket({
        "id": "ticket-123",
        "title": "Database issue",
        "description": "Slow database",
        "reporter": {"name": "Kasia", "email": None, "vip": False},
        "impact": 3,
        "urgency": 2,
        "priority": "P4",
        "state": "new",
        "created_at": "2026-10-16T12:00:00Z",
        "sla": {"ack_due_at": "2026-10-16T16:00:00Z", "resolve_due_at": "2026-10-20T12:00:00Z"},
    })

    second_store = TicketStore(str(db_path))
    reloaded = second_store.get_ticket(created["id"])
    listed = second_store.list_tickets(state="new")

    assert reloaded is not None
    assert reloaded["description"] == "Slow database"
    assert reloaded["state"] == "new"
    assert any(item["id"] == "ticket-123" for item in listed)

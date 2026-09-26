# ai-generated: 90% - SQLite-backed ticket repository for T02; storage-only, no business rules or endpoint logic

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_db_path(db_path: str | None = None) -> str:
    if db_path:
        target = Path(db_path)
    else:
        configured = os.getenv("SVCDESK_DB_PATH")
        if configured:
            target = Path(configured)
        else:
            target = Path(__file__).resolve().parent.parent / "data" / "svcdesk.db"
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)


def _serialize_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _ticket_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "reporter": json.loads(row["reporter_json"] or "{}"),
        "impact": row["impact"],
        "urgency": row["urgency"],
        "priority": row["priority"],
        "state": row["state"],
        "created_at": row["created_at"],
        "acknowledged_at": row["acknowledged_at"],
        "resolved_at": row["resolved_at"],
        "closed_at": row["closed_at"],
        "related_to": row["related_to"],
        "sla": json.loads(row["sla_json"] or "{}"),
    }


class TicketStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = resolve_db_path(db_path)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    reporter_json TEXT,
                    impact INTEGER,
                    urgency INTEGER,
                    priority TEXT,
                    state TEXT,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    closed_at TEXT,
                    related_to TEXT,
                    sla_json TEXT
                )
                """
            )

    def create_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        ticket = dict(payload or {})
        ticket_id = str(ticket.get("id") or uuid.uuid4())
        ticket["id"] = ticket_id
        ticket.setdefault("title", "")
        ticket.setdefault("description", "")
        ticket.setdefault("reporter", {})
        ticket.setdefault("impact", None)
        ticket.setdefault("urgency", None)
        ticket.setdefault("priority", None)
        ticket.setdefault("state", "new")
        ticket.setdefault("created_at", _utc_now())
        ticket.setdefault("acknowledged_at", None)
        ticket.setdefault("resolved_at", None)
        ticket.setdefault("closed_at", None)
        ticket.setdefault("related_to", None)
        ticket.setdefault("sla", {})

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tickets (
                    id, title, description, reporter_json, impact, urgency, priority, state,
                    created_at, acknowledged_at, resolved_at, closed_at, related_to, sla_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket["id"],
                    str(ticket.get("title") or ""),
                    str(ticket.get("description") or ""),
                    _serialize_json(ticket.get("reporter") or {}),
                    ticket.get("impact"),
                    ticket.get("urgency"),
                    ticket.get("priority"),
                    ticket.get("state"),
                    str(ticket.get("created_at") or _utc_now()),
                    ticket.get("acknowledged_at"),
                    ticket.get("resolved_at"),
                    ticket.get("closed_at"),
                    ticket.get("related_to"),
                    _serialize_json(ticket.get("sla") or {}),
                ),
            )

        return self.get_ticket(ticket_id)

    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?",
                (ticket_id,),
            ).fetchone()
        if row is None:
            return None
        return _ticket_row_to_dict(row)

    def list_tickets(self, state: str | None = None, priority: str | None = None) -> list[dict[str, Any]]:
        clauses = []
        parameters: list[Any] = []
        if state is not None:
            clauses.append("state = ?")
            parameters.append(state)
        if priority is not None:
            clauses.append("priority = ?")
            parameters.append(priority)

        sql = "SELECT * FROM tickets"
        if clauses:
            sql = f"{sql} WHERE {' AND '.join(clauses)}"
        sql = f"{sql} ORDER BY created_at ASC"

        with self._connect() as connection:
            rows = connection.execute(sql, tuple(parameters)).fetchall()
        return [_ticket_row_to_dict(row) for row in rows]


def init_db(db_path: str | None = None) -> str:
    store = TicketStore(db_path)
    return store.db_path


def get_db_path() -> str:
    return resolve_db_path()

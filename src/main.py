# ai-generated: 95% - full FastAPI implementation for T04-T12 while preserving the T01-T03 foundation and C1/C2/C3 decisions
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.dora import compute_dora_metrics
from src.persistence import TicketStore
from src.service import (
    compute_ticket_sla,
    parse_request_clock,
    priority_from_matrix,
    resolve_ticket_transition,
    sla_payload_for_ticket,
)
from src.validation import RequestValidationError as DomainRequestValidationError, parse_ticket_payload

app = FastAPI(title="svcdesk", version="0.1.0")
store = TicketStore()


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@app.on_event("startup")
async def startup_event() -> None:
    store.init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets")
async def create_ticket(request: Request) -> JSONResponse:
    raw = await request.body()
    try:
        payload = await request.json()
    except Exception:
        return error_response(400, "validation", "invalid request body")

    try:
        now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
        normalized = parse_ticket_payload(payload, test_clock=now, test_clock_enabled=bool(request.headers.get("X-Test-Clock")))
    except DomainRequestValidationError as exc:
        return error_response(exc.status_code, exc.code, exc.message)

    ticket = {
        "id": normalized["id"],
        "title": normalized["title"],
        "description": normalized["description"],
        "reporter": normalized["reporter"],
        "impact": normalized["impact"],
        "urgency": normalized["urgency"],
        "priority": priority_from_matrix(normalized["impact"], normalized["urgency"]),
        "state": normalized["state"],
        "created_at": normalized["created_at"],
        "acknowledged_at": normalized["acknowledged_at"],
        "resolved_at": normalized["resolved_at"],
        "closed_at": normalized["closed_at"],
        "related_to": normalized["related_to"],
        "sla": compute_ticket_sla(normalized["created_at"], priority_from_matrix(normalized["impact"], normalized["urgency"])),
    }
    created = store.create_ticket(ticket)
    return JSONResponse(status_code=201, content=created)


@app.post("/dora/metrics")
async def dora_metrics(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return error_response(400, "validation", "invalid request body")
    try:
        result = compute_dora_metrics(payload)
    except DomainRequestValidationError as exc:
        return error_response(exc.status_code, exc.code, exc.message)
    except ValueError as exc:
        return error_response(400, "validation", str(exc))
    return JSONResponse(content=result)


@app.get("/dora/ticket-events")
async def dora_ticket_events() -> JSONResponse:
    items = []
    for ticket in store.list_tickets():
        for phase, key in (("created", "created_at"), ("acknowledged", "acknowledged_at"), ("resolved", "resolved_at"), ("closed", "closed_at")):
            value = ticket.get(key)
            if value is None:
                continue
            state = "new" if phase == "created" else phase
            items.append({
                "ticket_id": ticket["id"],
                "at": value,
                "phase": phase,
                "priority": ticket.get("priority"),
                "state": state,
            })
    items.sort(key=lambda item: (item["at"], item["ticket_id"]))
    return JSONResponse(content=items)


@app.get("/tickets")
async def list_tickets(
    request: Request,
    state: str | None = Query(default=None),
    priority: str | None = Query(default=None),
) -> JSONResponse:
    items = store.list_tickets(state=state, priority=priority)
    return JSONResponse(content=items)


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    return JSONResponse(content=item)


@app.get("/tickets/{ticket_id}/sla")
async def get_ticket_sla(ticket_id: str, request: Request) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
    payload = sla_payload_for_ticket(item, now)
    return JSONResponse(content=payload)


@app.post("/tickets/{ticket_id}/ack")
async def ack_ticket(ticket_id: str, request: Request) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
    try:
        updated = resolve_ticket_transition(item, "ack", now)
    except ValueError as exc:
        return error_response(409, "invalid_transition", str(exc))
    stored = store.update_ticket(ticket_id, updated)
    return JSONResponse(content=stored)


@app.post("/tickets/{ticket_id}/start")
async def start_ticket(ticket_id: str, request: Request) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
    try:
        updated = resolve_ticket_transition(item, "start", now)
    except ValueError as exc:
        return error_response(409, "invalid_transition", str(exc))
    stored = store.update_ticket(ticket_id, updated)
    return JSONResponse(content=stored)


@app.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, request: Request) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
    try:
        updated = resolve_ticket_transition(item, "resolve", now)
    except ValueError as exc:
        return error_response(409, "invalid_transition", str(exc))
    stored = store.update_ticket(ticket_id, updated)
    return JSONResponse(content=stored)


@app.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, request: Request) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
    try:
        updated = resolve_ticket_transition(item, "close", now)
    except ValueError as exc:
        return error_response(409, "invalid_transition", str(exc))
    stored = store.update_ticket(ticket_id, updated)
    return JSONResponse(content=stored)


@app.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, request: Request) -> JSONResponse:
    item = store.get_ticket(ticket_id)
    if item is None:
        return error_response(404, "not_found", "ticket not found")
    now = parse_request_clock(request.headers.get("X-Test-Clock"), request)
    try:
        updated = resolve_ticket_transition(item, "reopen", now)
    except ValueError as exc:
        return error_response(409, "invalid_transition", str(exc))
    stored = store.update_ticket(ticket_id, updated)
    return JSONResponse(content=stored)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return error_response(404, "not_found", f"{request.url.path} not found")
    if exc.status_code == 405:
        return error_response(405, "method_not_allowed", "method not allowed")
    return error_response(exc.status_code, "http_error", exc.detail)


@app.exception_handler(DomainRequestValidationError)
async def validation_exception_handler(request: Request, exc: DomainRequestValidationError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


@app.exception_handler(FastAPIRequestValidationError)
async def fastapi_validation_exception_handler(request: Request, exc: FastAPIRequestValidationError) -> JSONResponse:
    return error_response(422, "validation", "invalid request body")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=False)

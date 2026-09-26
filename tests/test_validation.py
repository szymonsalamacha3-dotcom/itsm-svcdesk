# ai-generated: 80% - T03 validation tests covering malformed payloads and test clock parsing without endpoint-level logic

from __future__ import annotations

import os

import pytest

from src.validation import RequestValidationError, parse_ticket_payload, parse_test_clock


def test_parse_ticket_payload_accepts_valid_ticket():
    payload = {
        "title": "Printer not working",
        "description": "Floor 2 printer is down.",
        "reporter": {"name": "Anna Nowak", "email": "anna@example.com", "vip": True},
        "impact": 2,
        "urgency": 1,
        "related_to": "ticket-123",
        "priority": "P9",
        "unknown": "ignore me",
    }

    parsed = parse_ticket_payload(payload, test_clock="2026-10-14T10:00:00Z", test_clock_enabled=True)

    assert parsed["title"] == "Printer not working"
    assert parsed["description"] == "Floor 2 printer is down."
    assert parsed["reporter"]["name"] == "Anna Nowak"
    assert parsed["reporter"]["vip"] is True
    assert parsed["impact"] == 2
    assert parsed["urgency"] == 1
    assert parsed["related_to"] == "ticket-123"
    assert parsed["id"] is not None
    assert parsed["priority"] is None
    assert parsed["created_at"] == "2026-10-14T10:00:00Z"
    assert "unknown" not in parsed


def test_missing_title_is_rejected():
    with pytest.raises(RequestValidationError) as exc_info:
        parse_ticket_payload({"reporter": {"name": "Anna"}, "impact": 1, "urgency": 1})

    assert exc_info.value.to_error() == {"error": {"code": "validation", "message": "title is required"}}


def test_impact_out_of_range_is_rejected():
    with pytest.raises(RequestValidationError):
        parse_ticket_payload({
            "title": "Broken printer",
            "reporter": {"name": "Anna"},
            "impact": 5,
            "urgency": 1,
        })


def test_urgency_invalid_type_is_rejected():
    with pytest.raises(RequestValidationError):
        parse_ticket_payload({
            "title": "Broken printer",
            "reporter": {"name": "Anna"},
            "impact": 1,
            "urgency": "high",
        })


def test_title_length_201_is_rejected():
    too_long = "x" * 201
    with pytest.raises(RequestValidationError):
        parse_ticket_payload({
            "title": too_long,
            "reporter": {"name": "Anna"},
            "impact": 1,
            "urgency": 1,
        })


def test_invalid_test_clock_is_rejected():
    old_env = os.environ.get("SVCDESK_TEST_CLOCK")
    os.environ["SVCDESK_TEST_CLOCK"] = "1"
    try:
        with pytest.raises(RequestValidationError):
            parse_ticket_payload({
                "title": "Broken printer",
                "reporter": {"name": "Anna"},
                "impact": 1,
                "urgency": 1,
            }, test_clock="yesterday", test_clock_enabled=True)

        with pytest.raises(RequestValidationError):
            parse_test_clock("yesterday")
    finally:
        if old_env is None:
            os.environ.pop("SVCDESK_TEST_CLOCK", None)
        else:
            os.environ["SVCDESK_TEST_CLOCK"] = old_env

# ai-generated: 100% - OpenAI Copilot wrote behavioural boundary tests for the course module per Lab 5 P-29
from datetime import datetime, timedelta

import pytest

import slaclock


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 1, "P2"),
        (1, 3, "P3"),
        (2, 2, "P3"),
        (3, 1, "P3"),
        (2, 3, "P4"),
        (3, 2, "P4"),
        (3, 3, "P4"),
    ],
)
def test_priority_matrix(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency) == expected


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 2, "P2"),
        (3, 3, "P2"),
    ],
)
def test_vip_priorities_are_promoted_only_as_needed(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency, vip=True) == expected


@pytest.mark.parametrize("bad_value", [0, 4, -1, 2.0, True, "1"])
def test_priority_rejects_non_integer_or_out_of_range_inputs(bad_value):
    with pytest.raises(ValueError):
        slaclock.priority_of(bad_value, 1)
    with pytest.raises(ValueError):
        slaclock.priority_of(1, bad_value)


@pytest.mark.parametrize(
    ("priority", "expected"),
    [
        ("P1", (15, 240)),
        ("P2", (60, 480)),
        ("P3", (240, 1440)),
        ("P4", (480, 4320)),
    ],
)
def test_priority_targets(priority, expected):
    assert slaclock.targets(priority) == expected


@pytest.mark.parametrize("priority", ["p1", " P1", "P5", ""])
def test_targets_requires_an_exact_known_priority(priority):
    with pytest.raises(ValueError):
        slaclock.targets(priority)


@pytest.mark.parametrize(
    ("elapsed", "target", "expected"),
    [
        (0, 15, "ok"),
        (11, 15, "ok"),
        (12, 15, "warning"),
        (15, 15, "warning"),
        (16, 15, "breached"),
    ],
)
def test_sla_threshold_boundaries(elapsed, target, expected):
    assert slaclock.sla_state(elapsed, target) == expected


@pytest.mark.parametrize(("elapsed", "target"), [(-1, 15), (0, 0), (0, -1)])
def test_sla_state_rejects_invalid_clock_values(elapsed, target):
    with pytest.raises(ValueError):
        slaclock.sla_state(elapsed, target)


def test_business_time_uses_weekdays_and_half_open_eight_to_four_window():
    monday = datetime(2026, 11, 16)
    assert slaclock.is_business_time(monday.replace(hour=8, minute=0))
    assert slaclock.is_business_time(monday.replace(hour=15, minute=59))
    assert not slaclock.is_business_time(monday.replace(hour=7, minute=59))
    assert not slaclock.is_business_time(monday.replace(hour=16, minute=0))
    assert not slaclock.is_business_time(datetime(2026, 11, 14, 10, 0))
    assert not slaclock.is_business_time(datetime(2026, 11, 15, 10, 0))


def test_business_time_ignores_seconds_and_microseconds():
    assert slaclock.is_business_time(datetime(2026, 11, 16, 8, 0, 59, 999999))
    assert not slaclock.is_business_time(datetime(2026, 11, 16, 16, 0, 0, 1))


def test_add_business_minutes_inside_window_and_rounds_to_minute():
    start = datetime(2026, 11, 16, 9, 17, 42, 123456)
    assert slaclock.add_business_minutes(start, 0) == datetime(2026, 11, 16, 9, 17)
    assert slaclock.add_business_minutes(start, 1) == datetime(2026, 11, 16, 9, 18)


@pytest.mark.parametrize(
    ("start", "minutes", "expected"),
    [
        (datetime(2026, 11, 16, 7, 0), 0, datetime(2026, 11, 16, 8, 0)),
        (datetime(2026, 11, 16, 7, 0), 5, datetime(2026, 11, 16, 8, 5)),
        (datetime(2026, 11, 16, 16, 0), 0, datetime(2026, 11, 17, 8, 0)),
        (datetime(2026, 11, 16, 15, 0), 60, datetime(2026, 11, 16, 16, 0)),
        (datetime(2026, 11, 16, 15, 0), 61, datetime(2026, 11, 17, 8, 1)),
        (datetime(2026, 11, 13, 16, 0), 1, datetime(2026, 11, 16, 8, 1)),
        (datetime(2026, 11, 14, 10, 0), 0, datetime(2026, 11, 16, 8, 0)),
        (datetime(2026, 11, 15, 10, 0), 1, datetime(2026, 11, 16, 8, 1)),
    ],
)
def test_add_business_minutes_adjusts_opening_and_closing(start, minutes, expected):
    assert slaclock.add_business_minutes(start, minutes) == expected


def test_add_business_minutes_rejects_negative_and_due_dates_beyond_limit():
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(datetime(2026, 11, 16, 8), -1)
    start = datetime(2024, 1, 1, 8)
    assert slaclock.add_business_minutes(start, 263 * 480) == datetime(2025, 1, 1, 16)
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(start, 264 * 480)


def test_business_minutes_between_counts_half_open_weekday_windows():
    monday = datetime(2026, 11, 16)
    assert slaclock.business_minutes_between(
        monday.replace(hour=7), monday.replace(hour=17)
    ) == 480
    assert slaclock.business_minutes_between(
        monday.replace(hour=8), monday.replace(hour=16)
    ) == 480
    assert slaclock.business_minutes_between(
        monday.replace(hour=16), monday.replace(hour=16)
    ) == 0


def test_business_minutes_between_excludes_weekends_and_floors_seconds():
    friday = datetime(2026, 11, 13, 15, 30, 59)
    monday = datetime(2026, 11, 16, 8, 30, 1)
    assert slaclock.business_minutes_between(friday, monday) == 60
    assert slaclock.business_minutes_between(friday, friday) == 0


def test_business_minutes_between_rejects_reversed_or_too_wide_ranges():
    start = datetime(2026, 11, 16, 8)
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, start - timedelta(minutes=1))
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, start + timedelta(days=367))


def test_add_and_measure_business_minutes_are_inverses_across_a_weekend():
    start = datetime(2026, 11, 13, 15, 30)
    due = slaclock.add_business_minutes(start, 90)
    assert due == datetime(2026, 11, 16, 9)
    assert slaclock.business_minutes_between(start, due) == 90


@pytest.mark.parametrize(
    ("priority", "breached", "reopens", "expected"),
    [
        ("P1", False, 0, 1),
        ("P2", False, 0, 1),
        ("P3", False, 0, 0),
        ("P4", False, 2, 1),
        ("P2", True, 0, 2),
        ("P1", True, 0, 3),
        ("P3", True, 0, 1),
        ("P2", True, 2, 3),
        ("P1", True, 2, 3),
    ],
)
def test_escalation_tier_rules_and_cap(priority, breached, reopens, expected):
    assert slaclock.escalation_tier(priority, breached, reopens) == expected


@pytest.mark.parametrize(("priority", "reopens"), [("P5", 0), ("P1", -1)])
def test_escalation_rejects_unknown_priorities_and_negative_reopens(priority, reopens):
    with pytest.raises(ValueError):
        slaclock.escalation_tier(priority, False, reopens)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("90m", 90),
        ("4h", 240),
        ("1h30m", 90),
        ("2d", 2880),
        ("1d4h", 1680),
        ("1d0h5m", 1445),
        ("1h59m", 119),
        ("60m", 60),
        ("0h60m", 60),
        ("0d60m", 60),
        ("  1h30m  ", 90),
    ],
)
def test_parse_duration_accepts_documented_forms(text, expected):
    assert slaclock.parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "0m",
        "0h",
        "1.5h",
        "30m1h",
        "-5m",
        "1 h",
        "1h60m",
        "1d60m",
        "1d2h60m",
        "1H",
    ],
)
def test_parse_duration_rejects_invalid_or_zero_forms(text):
    with pytest.raises(ValueError):
        slaclock.parse_duration(text)

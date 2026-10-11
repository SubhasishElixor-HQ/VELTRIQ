from __future__ import annotations

import json

from app.database import initialize, session
from app.ingest import import_jsonl
from app.query_service import answer_query, identify_intent
from tools.generate_demo_data import build_records


def load_demo(db_path):
    initialize(db_path)
    records, _ = build_records()
    text = "\n".join(json.dumps(record) for record in records)
    with session(db_path) as conn:
        result = import_jsonl(conn, text)
    return result


def test_demo_import_is_complete_and_idempotent(tmp_path):
    db_path = tmp_path / "demo.db"
    first = load_demo(db_path)
    assert first["rejected"] == 0
    assert first["inserted"]["trip"] == 6
    assert first["inserted"]["event"] == 5

    all_records, _ = build_records()
    with session(db_path) as conn:
        second = import_jsonl(conn, "\n".join(json.dumps(record) for record in all_records))
    assert second["duplicates"] == len(all_records)


def test_warning_timeline_returns_timestamped_signal_and_log_evidence(tmp_path):
    db_path = tmp_path / "demo.db"
    load_demo(db_path)
    with session(db_path) as conn:
        result = answer_query(conn, "What happened before this battery warning?")
    assert result["intent"] == "warning_timeline"
    assert result["simulated_data"] is True
    assert any(item["record_type"] == "signal" for item in result["evidence"])
    assert any(item["record_type"] == "log" for item in result["evidence"])
    assert all(item["timestamp_utc"].endswith("Z") for item in result["evidence"])


def test_recurrence_intent_finds_repeated_battery_warning(tmp_path):
    db_path = tmp_path / "demo.db"
    load_demo(db_path)
    assert identify_intent("Has this battery warning happened before?") == "warning_recurrence"
    with session(db_path) as conn:
        result = answer_query(conn, "Has this battery warning happened before?")
    assert "2 recorded occurrence(s)" in result["answer"]
    assert len(result["evidence"]) == 2


def test_trip_comparison_is_computed_and_caveated(tmp_path):
    db_path = tmp_path / "demo.db"
    load_demo(db_path)
    with session(db_path) as conn:
        result = answer_query(conn, "How did this trip compare with another trip?")
    assert result["intent"] == "compare_trips"
    assert "kWh/100 km" in result["answer"]
    assert result["limitations"]


def test_invalid_or_orphan_records_are_rejected_without_crashing(tmp_path):
    db_path = tmp_path / "demo.db"
    initialize(db_path)
    orphan = {
        "schema_version": 1,
        "record_type": "event",
        "event_id": "orphan",
        "timestamp_utc": "2026-09-18T08:00:00Z",
        "trip_id": "missing-trip",
        "source": "test",
        "event_type": "test_warning",
        "severity": "warning",
        "description": "orphan event",
        "scenario_id": "test",
    }
    with session(db_path) as conn:
        result = import_jsonl(conn, "{bad json}\n" + json.dumps(orphan))
    assert result["rejected"] == 2
    assert len(result["errors"]) == 2

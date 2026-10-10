from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from .model_client import explain


def identify_intent(question: str) -> str:
    q = question.casefold()
    if any(word in q for word in ("compare", "versus", "vs ", "compared")) or "another trip" in q:
        return "compare_trips"
    if any(word in q for word in ("first", "when did", "first occur", "first appear")):
        return "warning_first_seen"
    if any(word in q for word in ("signal", "changed", "change before")):
        return "signal_changes"
    if any(word in q for word in ("happened before", "happened again", "occurred before", "occurred again", "how many times", "repeat warning")) and "what happened" not in q:
        return "warning_recurrence"
    if any(word in q for word in ("what happened", "before this", "before the warning", "before this warning")):
        return "warning_timeline"
    if "warning" in q or "fault" in q or "adas" in q or "battery" in q:
        return "warning_timeline"
    return "unsupported"


def _warning_filter(question: str) -> str | None:
    q = question.casefold()
    if "adas" in q or "disengage" in q:
        return "adas_disengagement"
    if "battery" in q or "temperature" in q:
        return "battery_temperature_warning"
    if "range" in q:
        return "range_drop"
    return None


def _target_event(conn: sqlite3.Connection, question: str, trip_id: str | None):
    event_type = _warning_filter(question)
    where = "WHERE (severity IN ('warning','critical') OR event_type LIKE ?)"
    params: list[Any] = ["%warning%"]
    if event_type:
        where = "WHERE event_type = ?"
        params = [event_type]
    if trip_id:
        where += " AND trip_id = ?"
        params.append(trip_id)
    return conn.execute(f"SELECT * FROM events {where} ORDER BY timestamp_utc DESC LIMIT 1", params).fetchone()


def _event_evidence(row: sqlite3.Row) -> dict[str, Any]:
    return {"evidence_id": row["event_id"], "record_type": "event", "timestamp_utc": row["timestamp_utc"], "source": row["source"], "label": row["description"], "value": row["severity"], "unit": None, "quality": "valid", "trip_id": row["trip_id"]}


def _signal_evidence(row: sqlite3.Row) -> dict[str, Any]:
    label = row["signal_id"].replace("_", " ").title()
    return {"evidence_id": row["record_id"], "record_type": "signal", "timestamp_utc": row["timestamp_utc"], "source": row["source"], "label": label, "value": row["value"], "unit": row["unit"], "quality": row["quality"], "trip_id": row["trip_id"]}


def _time_range(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "No matching records"
    times = sorted(item["timestamp_utc"] for item in evidence)
    return f"{times[0]} — {times[-1]}"


def _empty(intent: str) -> dict[str, Any]:
    return {"intent": intent, "answer": "No matching records were found. Import demo or recorded data first, or try a more specific warning name.", "time_range": "No matching records", "evidence": [], "limitations": ["The current local dataset may not contain the requested warning or time range."], "response_mode": "deterministic", "simulated_data": False}


def answer_query(conn: sqlite3.Connection, question: str, trip_id: str | None = None, trip_ids: list[str] | None = None) -> dict[str, Any]:
    intent = identify_intent(question)
    if intent == "unsupported":
        return {"intent": intent, "answer": "I can answer warning timelines, first occurrence, signal changes, recurrence, or trip comparisons. Try one of the example questions.", "time_range": "Not applicable", "evidence": [], "limitations": ["This question is outside the supported query set."], "response_mode": "deterministic", "simulated_data": False}
    if intent == "compare_trips":
        return _compare_trips(conn, question, trip_ids)
    target = _target_event(conn, question, trip_id)
    if target is None:
        return _empty(intent)
    event_type = target["event_type"]
    evidence: list[dict[str, Any]] = [_event_evidence(target)]
    limitations: list[str] = []
    target_time = datetime.fromisoformat(target["timestamp_utc"].replace("Z", "+00:00"))
    if intent == "warning_first_seen":
        first = conn.execute("SELECT * FROM events WHERE event_type=? ORDER BY timestamp_utc ASC LIMIT 1", (event_type,)).fetchone()
        evidence = [_event_evidence(first)] if first else evidence
        fallback = f"The first recorded {event_type.replace('_', ' ')} in this dataset was at {evidence[0]['timestamp_utc']}."
    elif intent == "warning_recurrence":
        rows = conn.execute("SELECT * FROM events WHERE event_type=? ORDER BY timestamp_utc ASC", (event_type,)).fetchall()
        evidence = [_event_evidence(row) for row in rows[:20]]
        fallback = f"This dataset contains {len(rows)} recorded occurrence(s) of {event_type.replace('_', ' ')} across {len({row['trip_id'] for row in rows})} trip(s)."
    else:
        start = (target_time - timedelta(minutes=10)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        end = target_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        event_rows = conn.execute("SELECT * FROM events WHERE trip_id=? AND timestamp_utc BETWEEN ? AND ? ORDER BY timestamp_utc", (target["trip_id"], start, end)).fetchall()
        signal_rows = conn.execute("SELECT * FROM signals WHERE trip_id=? AND timestamp_utc BETWEEN ? AND ? ORDER BY timestamp_utc", (target["trip_id"], start, end)).fetchall()
        log_rows = conn.execute("SELECT * FROM logs WHERE trip_id=? AND timestamp_utc BETWEEN ? AND ? ORDER BY timestamp_utc", (target["trip_id"], start, end)).fetchall()
        log_evidence = [{"evidence_id": row["log_id"], "record_type": "log", "timestamp_utc": row["timestamp_utc"], "source": row["source"], "label": row["text"], "value": row["level"], "unit": None, "quality": "valid", "trip_id": row["trip_id"]} for row in log_rows]
        evidence = [_event_evidence(row) for row in event_rows] + [_signal_evidence(row) for row in signal_rows] + log_evidence
        evidence.sort(key=lambda item: (item["timestamp_utc"], item["record_type"]))
        bad = [item for item in evidence if item["record_type"] == "signal" and item["quality"] != "valid"]
        if bad:
            limitations.append(f"{len(bad)} signal record(s) in this window are missing, delayed, or invalid.")
        if intent == "signal_changes":
            signals = [item for item in evidence if item["record_type"] == "signal" and item["quality"] == "valid" and isinstance(item["value"], (int, float))]
            by_name: dict[str, list[dict[str, Any]]] = {}
            for item in signals:
                by_name.setdefault(item["label"], []).append(item)
            changes = []
            for name, values in by_name.items():
                if len(values) >= 2:
                    changes.append((max(float(item["value"]) for item in values) - min(float(item["value"]) for item in values), name, values))
            changes.sort(reverse=True, key=lambda entry: entry[0])
            evidence = []
            for _, _, values in changes[:3]:
                low = min(values, key=lambda item: float(item["value"]))
                high = max(values, key=lambda item: float(item["value"]))
                evidence.append(low)
                if high["evidence_id"] != low["evidence_id"]:
                    evidence.append(high)
            fallback = "The largest measured signal changes in the 10-minute window are shown below. This describes correlation in the recorded data; it does not establish a root cause."
        else:
            fallback = f"In the 10 minutes before {event_type.replace('_', ' ')}, the recorded timeline contains {len(event_rows)} event(s), {len(signal_rows)} signal sample(s), and {len(log_rows)} log record(s). See the evidence below."
    summary, mode = explain(question, evidence, fallback)
    return {"intent": intent, "answer": summary, "time_range": _time_range(evidence), "evidence": evidence[:100], "limitations": limitations, "response_mode": mode, "simulated_data": any(item["trip_id"].startswith("SIM-") for item in evidence)}


def _compare_trips(conn: sqlite3.Connection, question: str, trip_ids: list[str] | None) -> dict[str, Any]:
    if trip_ids and len(trip_ids) == 2:
        rows = conn.execute("SELECT * FROM trips WHERE trip_id IN (?,?) ORDER BY started_at", trip_ids).fetchall()
    else:
        rows = conn.execute("SELECT * FROM trips ORDER BY started_at DESC LIMIT 2").fetchall()
        rows = list(reversed(rows))
    if len(rows) < 2:
        return _empty("compare_trips")
    evidence: list[dict[str, Any]] = []
    summaries = []
    for trip in rows:
        values = conn.execute("SELECT * FROM signals WHERE trip_id=? AND signal_id='energy_consumption' AND quality='valid' AND value IS NOT NULL ORDER BY timestamp_utc", (trip["trip_id"],)).fetchall()
        if not values:
            continue
        mean = sum(float(item["value"]) for item in values) / len(values)
        summaries.append((trip, mean, len(values)))
        evidence.extend(_signal_evidence(item) for item in values[:2])
        evidence.extend(_signal_evidence(item) for item in values[-2:])
    if len(summaries) < 2:
        result = _empty("compare_trips")
        result["answer"] = "Two trips with valid energy-consumption records are needed for this comparison."
        return result
    (first, first_mean, _), (second, second_mean, _) = summaries
    delta = second_mean - first_mean
    direction = "higher" if delta > 0 else "lower" if delta < 0 else "unchanged"
    fallback = f"Average recorded energy use was {first_mean:.1f} kWh/100 km on {first['trip_id']} and {second_mean:.1f} kWh/100 km on {second['trip_id']} ({abs(delta):.1f} kWh/100 km {direction} on the second trip). This comparison does not explain why it changed."
    summary, mode = explain(question, evidence, fallback)
    return {"intent": "compare_trips", "answer": summary, "time_range": _time_range(evidence), "evidence": evidence[:100], "limitations": ["Trip comparison reports recorded values and does not establish why energy use changed."], "response_mode": mode, "simulated_data": all(str(item["trip_id"]).startswith("SIM-") for item in evidence)}

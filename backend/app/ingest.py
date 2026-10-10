from __future__ import annotations

import json
import sqlite3
import psycopg
from datetime import datetime, timezone
from typing import Any

from .config import MAX_IMPORT_RECORDS

ALLOWED_TYPES = {"trip", "signal", "event", "log"}
ALLOWED_QUALITIES = {"valid", "missing", "invalid", "delayed"}


class ImportValidationError(ValueError):
    pass


def _required(record: dict[str, Any], fields: tuple[str, ...], line_number: int) -> None:
    missing = [field for field in fields if record.get(field) is None]
    if missing:
        raise ImportValidationError(f"line {line_number}: missing {', '.join(missing)}")


def _timestamp(value: Any, line_number: int) -> str:
    if not isinstance(value, str):
        raise ImportValidationError(f"line {line_number}: timestamp_utc must be text")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ImportValidationError(f"line {line_number}: invalid timestamp_utc") from exc
    if parsed.tzinfo is None:
        raise ImportValidationError(f"line {line_number}: timestamp_utc must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_line(line: str, line_number: int) -> dict[str, Any]:
    try:
        record = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ImportValidationError(f"line {line_number}: invalid JSON") from exc
    if not isinstance(record, dict):
        raise ImportValidationError(f"line {line_number}: record must be a JSON object")
    if record.get("schema_version") != 1:
        raise ImportValidationError(f"line {line_number}: schema_version must be 1")
    kind = record.get("record_type")
    if kind not in ALLOWED_TYPES:
        raise ImportValidationError(f"line {line_number}: unsupported record_type")
    if kind == "trip":
        _required(record, ("trip_id", "vehicle_alias", "started_at", "ended_at", "scenario"), line_number)
        record["started_at"] = _timestamp(record["started_at"], line_number)
        record["ended_at"] = _timestamp(record["ended_at"], line_number)
        record["distance_km"] = float(record.get("distance_km", 0))
    elif kind == "signal":
        _required(record, ("record_id", "timestamp_utc", "trip_id", "source", "signal_id", "unit", "quality", "scenario_id"), line_number)
        record["timestamp_utc"] = _timestamp(record["timestamp_utc"], line_number)
        if record["quality"] not in ALLOWED_QUALITIES:
            raise ImportValidationError(f"line {line_number}: quality must be one of {sorted(ALLOWED_QUALITIES)}")
        value = record.get("value")
        if value is not None and not isinstance(value, (int, float)):
            raise ImportValidationError(f"line {line_number}: signal value must be numeric or null")
    elif kind == "event":
        _required(record, ("event_id", "timestamp_utc", "trip_id", "source", "event_type", "severity", "description", "scenario_id"), line_number)
        record["timestamp_utc"] = _timestamp(record["timestamp_utc"], line_number)
    else:
        _required(record, ("log_id", "timestamp_utc", "trip_id", "source", "level", "text", "scenario_id"), line_number)
        record["timestamp_utc"] = _timestamp(record["timestamp_utc"], line_number)
    return record


def import_jsonl(conn: sqlite3.Connection, content: str, max_records: int = MAX_IMPORT_RECORDS) -> dict[str, Any]:
    inserted = {kind: 0 for kind in ALLOWED_TYPES}
    duplicates = 0
    rejected = 0
    errors: list[str] = []
    lines = [line for line in content.splitlines() if line.strip()]
    if len(lines) > max_records:
        raise ImportValidationError(f"Import has {len(lines)} records; maximum is {max_records}.")
    for line_number, line in enumerate(lines, 1):
        conn.execute("SAVEPOINT import_row")
        try:
            record = _parse_line(line, line_number)
            kind = record["record_type"]
            if kind == "trip":
                cursor = conn.execute(
                    "INSERT INTO trips(trip_id,vehicle_alias,started_at,ended_at,scenario,distance_km,data_origin) VALUES(?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                    (record["trip_id"], record["vehicle_alias"], record["started_at"], record["ended_at"], record["scenario"], record["distance_km"], record.get("data_origin", "simulated")),
                )
            elif kind == "signal":
                cursor = conn.execute(
                    "INSERT INTO signals(record_id,timestamp_utc,trip_id,source,signal_id,value,unit,quality,scenario_id) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                    (record["record_id"], record["timestamp_utc"], record["trip_id"], record["source"], record["signal_id"], record.get("value"), record["unit"], record["quality"], record["scenario_id"]),
                )
            elif kind == "event":
                cursor = conn.execute(
                    "INSERT INTO events(event_id,timestamp_utc,trip_id,source,event_type,severity,description,scenario_id) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                    (record["event_id"], record["timestamp_utc"], record["trip_id"], record["source"], record["event_type"], record["severity"], record["description"], record["scenario_id"]),
                )
            else:
                cursor = conn.execute(
                    "INSERT INTO logs(log_id,timestamp_utc,trip_id,source,level,text,scenario_id) VALUES(?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                    (record["log_id"], record["timestamp_utc"], record["trip_id"], record["source"], record["level"], record["text"], record["scenario_id"]),
                )
            if cursor.rowcount:
                inserted[kind] += 1
            else:
                duplicates += 1
            conn.execute("RELEASE SAVEPOINT import_row")
        except (ImportValidationError, sqlite3.IntegrityError, psycopg.IntegrityError, TypeError, ValueError) as exc:
            conn.execute("ROLLBACK TO SAVEPOINT import_row")
            conn.execute("RELEASE SAVEPOINT import_row")
            rejected += 1
            if len(errors) < 50:
                errors.append(str(exc))
    conn.commit()
    return {"inserted": inserted, "duplicates": duplicates, "rejected": rejected, "errors": errors}

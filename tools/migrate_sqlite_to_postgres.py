"""Copy VehicleGPT records from the old SQLite file into configured PostgreSQL.

The source SQLite file is read-only and left untouched. Existing PostgreSQL rows
with the same primary keys are retained, making the migration safe to rerun.
"""
import argparse
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.database import initialize, session

TABLES = {
    "trips": ("trip_id", "vehicle_alias", "started_at", "ended_at", "scenario", "distance_km", "data_origin"),
    "signals": ("record_id", "timestamp_utc", "trip_id", "source", "signal_id", "value", "unit", "quality", "scenario_id"),
    "events": ("event_id", "timestamp_utc", "trip_id", "source", "event_type", "severity", "description", "scenario_id"),
    "logs": ("log_id", "timestamp_utc", "trip_id", "source", "level", "text", "scenario_id"),
}

def migrate(source: Path) -> dict[str, int]:
    if not source.is_file():
        raise FileNotFoundError(f"SQLite source file not found: {source}")
    initialize()
    counts = {table: 0 for table in TABLES}
    old = sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True)
    old.row_factory = sqlite3.Row
    try:
        with session() as new:
            for table, columns in TABLES.items():
                names = ",".join(columns)
                markers = ",".join("?" for _ in columns)
                sql = f"INSERT INTO {table}({names}) VALUES({markers}) ON CONFLICT DO NOTHING"
                for row in old.execute(f"SELECT {names} FROM {table}"):
                    cursor = new.execute(sql, tuple(row[column] for column in columns))
                    counts[table] += max(cursor.rowcount, 0)
    finally:
        old.close()
    return counts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy VehicleGPT SQLite records into PostgreSQL without deleting the source.")
    parser.add_argument("--sqlite", type=Path, default=ROOT / "data" / "vehiclegpt.db")
    args = parser.parse_args()
    print("Rows copied to PostgreSQL:", migrate(args.sqlite))
    print("The SQLite source was left unchanged.")

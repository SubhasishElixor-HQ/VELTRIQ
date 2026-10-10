from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL

SCHEMA_VERSION = 1


class Connection:
    """PostgreSQL application connection; accepts SQLite paths for isolated tests."""
    def __init__(self, target: str | Path | None = None):
        self.sqlite = isinstance(target, Path) or (isinstance(target, str) and "://" not in target)
        if self.sqlite:
            path = Path(target or "vehiclegpt-test.db")
            path.parent.mkdir(parents=True, exist_ok=True)
            self.raw = sqlite3.connect(path, timeout=10.0)
            self.raw.row_factory = sqlite3.Row
            self.raw.execute("PRAGMA foreign_keys = ON")
            self.raw.execute("PRAGMA busy_timeout = 10000")
        else:
            self.raw = psycopg.connect(str(target or DATABASE_URL), row_factory=dict_row)

    def execute(self, sql: str, params: Any = ()):
        return self.raw.execute(sql.replace("?", "%s"), params) if not self.sqlite else self.raw.execute(sql.replace("%s", "?"), params)

    def executescript(self, sql: str):
        if self.sqlite:
            return self.raw.executescript(sql)
        cursor = self.raw.cursor()
        for statement in sql.split(";"):
            if statement.strip(): cursor.execute(statement)
        return cursor

    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()


def connect(target: str | Path | None = None) -> Connection:
    return Connection(target)


@contextmanager
def session(target: str | Path | None = None) -> Iterator[Connection]:
    conn = connect(target)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_COMMON_SCHEMA = """
CREATE TABLE IF NOT EXISTS trips(trip_id TEXT PRIMARY KEY,vehicle_alias TEXT NOT NULL,started_at TEXT NOT NULL,ended_at TEXT NOT NULL,scenario TEXT NOT NULL,distance_km DOUBLE PRECISION NOT NULL DEFAULT 0,data_origin TEXT NOT NULL DEFAULT 'simulated');
CREATE TABLE IF NOT EXISTS signals(record_id TEXT PRIMARY KEY,timestamp_utc TEXT NOT NULL,trip_id TEXT NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,source TEXT NOT NULL,signal_id TEXT NOT NULL,value DOUBLE PRECISION,unit TEXT NOT NULL,quality TEXT NOT NULL,scenario_id TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_signals_trip_time ON signals(trip_id,timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_signals_name_time ON signals(signal_id,timestamp_utc);
CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,timestamp_utc TEXT NOT NULL,trip_id TEXT NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,source TEXT NOT NULL,event_type TEXT NOT NULL,severity TEXT NOT NULL,description TEXT NOT NULL,scenario_id TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_events_trip_time ON events(trip_id,timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type,timestamp_utc);
CREATE TABLE IF NOT EXISTS logs(log_id TEXT PRIMARY KEY,timestamp_utc TEXT NOT NULL,trip_id TEXT NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,source TEXT NOT NULL,level TEXT NOT NULL,text TEXT NOT NULL,scenario_id TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_logs_trip_time ON logs(trip_id,timestamp_utc);
"""


def initialize(target: str | Path | None = None) -> None:
    with session(target) as conn:
        if conn.sqlite:
            conn.execute("PRAGMA journal_mode = WAL")
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION: raise RuntimeError("Database schema is newer than this application supports.")
            if version == 0:
                conn.executescript(_COMMON_SCHEMA.replace("DOUBLE PRECISION", "REAL") + "CREATE VIRTUAL TABLE IF NOT EXISTS logs_fts USING fts5(log_id UNINDEXED,text);")
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        else:
            conn.executescript(_COMMON_SCHEMA + "CREATE TABLE IF NOT EXISTS vehiclegpt_schema_version(version INTEGER NOT NULL);")
            conn.execute("INSERT INTO vehiclegpt_schema_version(version) SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM vehiclegpt_schema_version)")


def reset_database(target: str | Path | None = None) -> None:
    with session(target) as conn:
        for table in ("logs", "events", "signals", "trips"): conn.execute(f"DELETE FROM {table}")

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import initialize, session  # noqa: E402
from app.ingest import import_jsonl  # noqa: E402


def main() -> None:
    default_database = os.getenv("VEHICLEGPT_DATABASE_URL", str(ROOT / "data" / "vehiclegpt.db"))
    parser = argparse.ArgumentParser(description="Import versioned VehicleGPT JSONL records into the configured database (SQLite or PostgreSQL).")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--database", default=default_database)
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Input file does not exist: {args.input}")

    database_target = args.database
    if "://" not in str(database_target):
        database_target = Path(database_target)

    initialize(database_target)
    content = args.input.read_text(encoding="utf-8")
    with session(database_target) as conn:
        result = import_jsonl(conn, content)
    print(result)
    if result["rejected"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

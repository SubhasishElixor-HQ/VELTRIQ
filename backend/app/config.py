from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("VEHICLEGPT_DATA_DIR", PROJECT_ROOT / "data")).resolve()
DATABASE_URL = os.getenv("VEHICLEGPT_DATABASE_URL", "postgresql://vehiclegpt:change_me@127.0.0.1:5432/vehiclegpt").strip()
DATABASE_NAME = urlsplit(DATABASE_URL).path.lstrip("/") or "vehiclegpt"
MAX_IMPORT_BYTES = int(os.getenv("VEHICLEGPT_MAX_IMPORT_BYTES", str(10 * 1024 * 1024)))
MAX_IMPORT_RECORDS = int(os.getenv("VEHICLEGPT_MAX_IMPORT_RECORDS", "100000"))
MODEL_URL = os.getenv("VEHICLEGPT_MODEL_URL", "").strip()
MODEL_TIMEOUT_SECONDS = float(os.getenv("VEHICLEGPT_MODEL_TIMEOUT_SECONDS", "3"))
ALLOWED_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv(
        "VEHICLEGPT_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
)

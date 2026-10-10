from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS, DATABASE_NAME, MAX_IMPORT_BYTES
from .database import initialize, session
from .ingest import ImportValidationError, import_jsonl
from .query_service import answer_query
from .schemas import ImportResponse, QueryRequest, QueryResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("vehiclegpt")

app = FastAPI(title="VehicleGPT Local API", version="1.0.0", docs_url="/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=list(ALLOWED_ORIGINS), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.on_event("startup")
def on_startup() -> None:
    initialize()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "offline-local"}


@app.get("/api/v1/settings")
def settings() -> dict[str, object]:
    with session() as conn:
        counts = {table: conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"] for table in ("trips", "signals", "events", "logs")}
    return {"mode": "offline-local", "model_configured": bool(os.getenv("VEHICLEGPT_MODEL_URL")), "database": DATABASE_NAME, "counts": counts, "embedded_hardware_validated": False}


@app.get("/api/v1/trips")
def trips() -> list[dict[str, object]]:
    with session() as conn:
        rows = conn.execute("SELECT t.*, (SELECT COUNT(*) FROM events e WHERE e.trip_id=t.trip_id) AS event_count FROM trips t ORDER BY started_at DESC LIMIT 100").fetchall()
    return [dict(row) for row in rows]


@app.get("/api/v1/events")
def events(limit: int = 100, trip_id: str | None = None) -> list[dict[str, object]]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    sql = "SELECT * FROM events"
    params: tuple[object, ...] = ()
    if trip_id:
        sql += " WHERE trip_id=?"
        params = (trip_id,)
    sql += " ORDER BY timestamp_utc DESC LIMIT ?"
    params += (limit,)
    with session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/v1/query", response_model=QueryResponse)
def query(request: QueryRequest) -> dict[str, object]:
    with session() as conn:
        return answer_query(conn, request.question, request.trip_id, request.trip_ids)


@app.post("/api/v1/import", response_model=ImportResponse)
async def import_data(request: Request) -> dict[str, object]:
    length = request.headers.get("content-length")
    if length:
        try:
            declared_length = int(length)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header") from exc
        if declared_length < 0:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header")
        if declared_length > MAX_IMPORT_BYTES:
            raise HTTPException(status_code=413, detail=f"Import exceeds {MAX_IMPORT_BYTES} bytes")
    content = await request.body()
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail=f"Import exceeds {MAX_IMPORT_BYTES} bytes")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Import must be UTF-8 JSONL") from exc
    try:
        with session() as conn:
            return import_jsonl(conn, text)
    except ImportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


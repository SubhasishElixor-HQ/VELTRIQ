from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    trip_id: str | None = Field(default=None, max_length=80)
    trip_ids: list[str] | None = Field(default=None, max_length=2)


class Evidence(BaseModel):
    evidence_id: str
    record_type: Literal["event", "signal", "log", "trip"]
    timestamp_utc: str
    source: str
    label: str
    value: float | str | None = None
    unit: str | None = None
    quality: str | None = None
    trip_id: str


class QueryResponse(BaseModel):
    intent: str
    answer: str
    time_range: str
    evidence: list[Evidence]
    limitations: list[str] = Field(default_factory=list)
    response_mode: Literal["deterministic", "local-model"] = "deterministic"
    simulated_data: bool = False


class ImportResponse(BaseModel):
    inserted: dict[str, int]
    duplicates: int
    rejected: int
    errors: list[str]


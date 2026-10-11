# Local API

Base URL: `http://127.0.0.1:8000`. Interactive OpenAPI UI is available at `/docs` while the backend runs. All APIs are local development interfaces, not production internet endpoints.

## `GET /health`

Returns `{"status":"ok","mode":"offline-local"}`.

## `GET /api/v1/settings`

Returns local mode, PostgreSQL database name, counts for trips/signals/events/logs, optional-model configuration, and a flag that embedded-hardware requirements are not validated.

## `GET /api/v1/trips`

Returns at most 100 recent trips with event counts.

## `GET /api/v1/events?limit=100&trip_id=SIM-001`

Returns event records; `limit` is 1–500. `trip_id` is optional.

## `POST /api/v1/query`

```json
{"question":"What happened before this battery warning?","trip_id":"SIM-003"}
```

`question` is 3–500 characters. `trip_id` is optional. For comparisons, optionally pass exactly two `trip_ids`. Response includes `intent`, `answer`, `time_range`, bounded `evidence`, `limitations`, `response_mode`, and `simulated_data`.

Supported intents: timeline, first occurrence, signal changes, recurrence, and comparison of average `energy_consumption` in kWh/100km. An unsupported question receives a safe explanation of the supported set.

## `POST /api/v1/import`

Body is UTF-8 JSONL text (`Content-Type: text/plain; charset=utf-8`), max 10 MiB and 100,000 records by default. Return counts for inserted rows, duplicate rows, rejected rows, and up to 50 error details. Import is idempotent by record ID. Foreign-key violations are rejected. Limits can be configured with `VEHICLEGPT_MAX_IMPORT_BYTES` and `VEHICLEGPT_MAX_IMPORT_RECORDS`. The current importer may insert valid lines while rejecting invalid lines; inspect all counts and errors before using the imported set.

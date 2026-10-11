# JSONL data contract (schema version 1)

Each non-empty line is one JSON object. Import trips before their signal, event, and log rows because child rows reference `trip_id`. Timestamps must include a timezone; they are normalized to UTC. Values and names shown here are illustrative. Keep the original source file and provenance under the data owner's retention rules.

## Trip

```json
{"schema_version":1,"record_type":"trip","trip_id":"SIM-001","vehicle_alias":"Demo EV 01","started_at":"2026-09-18T08:00:00Z","ended_at":"2026-09-18T08:10:00Z","scenario":"battery_warning","distance_km":22.7,"data_origin":"simulated"}
```

Required: `trip_id`, `vehicle_alias`, `started_at`, `ended_at`, `scenario`. `distance_km` defaults to 0 and `data_origin` to `simulated`. Use an opaque alias, not a VIN or owner name, in demo data.

## Signal sample

```json
{"schema_version":1,"record_type":"signal","record_id":"SIM-001-S-00-battery_temperature","timestamp_utc":"2026-09-18T08:00:00Z","trip_id":"SIM-001","source":"simulated_can","signal_id":"battery_temperature","value":32.0,"unit":"C","quality":"valid","scenario_id":"battery_warning"}
```

Required: `record_id`, `timestamp_utc`, `trip_id`, `source`, `signal_id`, `unit`, `quality`, `scenario_id`. `value` is numeric or null. Quality is one of `valid`, `missing`, `invalid`, `delayed`.

## Event

```json
{"schema_version":1,"record_type":"event","event_id":"SIM-001-E-BATT-01","timestamp_utc":"2026-09-18T08:10:00Z","trip_id":"SIM-001","source":"diagnostics","event_type":"battery_temperature_warning","severity":"warning","description":"Battery temperature reached the warning threshold","scenario_id":"battery_warning"}
```

Required: `event_id`, `timestamp_utc`, `trip_id`, `source`, `event_type`, `severity`, `description`, `scenario_id`.

## Log line

```json
{"schema_version":1,"record_type":"log","log_id":"SIM-001-L-01","timestamp_utc":"2026-09-18T08:10:00Z","trip_id":"SIM-001","source":"thermal_controller","level":"warning","text":"Battery temperature warning recorded","scenario_id":"battery_warning"}
```

Required: `log_id`, `timestamp_utc`, `trip_id`, `source`, `level`, `text`, `scenario_id`.

## Adapter guidance

Do not ingest raw OEM data directly into the demo. Build a source-specific adapter that documents signal names, units, scaling, event-code dictionaries, clock semantics, missing-value sentinels, and licensing. Preserve source timestamp and source identifier in a documented mapping; normalize to UTC while retaining provenance. Reject unknown or ambiguous units rather than silently converting them. Agree on pseudonymization, data minimization, retention, deletion, and permitted processing with the data owner before receiving a real trace.

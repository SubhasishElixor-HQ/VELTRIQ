# Contributing

Keep the first release narrow: offline, read-only, evidence-backed service investigation. Prefer explicit parsers, typed records, bounded queries, and transparent limitations over open-ended model behavior.

Before a change is ready:

1. Add or update tests for ingestion, query logic, and the API behavior touched.
2. Run `python -m pytest backend/tests -q` and `cd frontend && npm run build`.
3. Update the data/API docs for any contract changes; increment `schema_version` for incompatible JSONL changes and plan a database migration.
4. Confirm generated or test data is synthetic and labeled; never commit customer vehicle data, local databases, `.env`, or model weights.
5. Check the UI and API still run on loopback without network access after dependencies are installed.

The project is an MVP scaffold. Discuss breaking data changes before implementation because importing partners' data is the likely integration bottleneck.

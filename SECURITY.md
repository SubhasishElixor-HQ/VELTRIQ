# Security and safety

## Product boundary

VehicleGPT is a read-only investigation aid. It must not send commands to a vehicle, ECU, charger, ADAS stack, or safety controller. It must not present a statistical association as confirmed root cause, a repair instruction, or a safety determination. This demo is not certified for automotive use.

## Local deployment baseline

- Bind API and UI to `127.0.0.1`; do not expose the development server to a LAN or public network.
- Keep real data, PostgreSQL credentials, and database backups out of source control and cloud-synced folders unless the data owner explicitly approves that location.
- Restrict filesystem access and OS account access. Encrypt the host disk and backups when handling sensitive traces.
- Use only a model server bound to loopback. Do not configure a remote provider for confidential vehicle data.
- Treat imported log text as untrusted input. The model is prompted to regard evidence as data, but that is not a security boundary; deterministic query logic, parameterized SQL, output limits, and human review remain authoritative.
- Keep the import-size and record-count bounds configured. Validate the data source, schema version, timestamp timezone, units, data quality, and provenance before pilot use.

## Known MVP gaps before a real customer pilot

This prototype has no user authentication, tenant isolation, managed encryption/backup, formal audit log, signed imports, or production secrets management. Localhost is a deployment boundary for a single-user demo, not a multi-user access-control system. Implement and review these controls before handling production/customer data or binding beyond loopback.

## Reporting

Do not include customer traces, credentials, or personal data in bug reports. Report suspected security issues privately to the project maintainer.

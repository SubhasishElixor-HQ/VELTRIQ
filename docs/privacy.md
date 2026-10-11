# Data handling and privacy

The demo stores imported records in the configured PostgreSQL database. With the included Docker Compose setup, that database runs on the user's computer and persists in a Docker volume. Import filenames are not sent anywhere. The default query path does not call an external service. The optional explanation model accepts only a localhost URL; configure it only with a local runtime. The UI does not include analytics or telemetry.

The prototype does not authenticate users, isolate tenants, manage retention automatically, or provide a formal audit ledger. Secure the PostgreSQL password, host account, database volume, and backups. The machine, its OS account, backups, and any local model files remain part of the security boundary. Remove imported customer records only after confirming the data owner authorizes deletion; deleting records from the database does not remove backups or source files.

Before processing a partner's data, document the data controller/owner, lawful basis and contract, exact data fields, minimization and pseudonymization, processing location, model setting, authorized users, retention/deletion date, backup behavior, incident contact, and whether outputs may be used for repair decisions. Start with de-identified samples and no direct identifiers. Do not assume vehicle data is non-personal merely because it lacks a name.

## Reset local demo database

Stop the backend, then run:

```bash
set -a && source .env && set +a
.venv/Scripts/python.exe -c "import sys; sys.path.insert(0,'backend'); from app.database import reset_database; reset_database()"
```

This clears rows but keeps the PostgreSQL database and schema. To remove the Docker database and all its stored data permanently, first stop the app and then run `docker compose down -v`. Also check separately for imported/exported files and backups.

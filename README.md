# VELTRIQ

**Offline-First Vehicle Diagnostic Investigation Workbench**

VehicleGPT is a software-only diagnostic investigation workbench designed for vehicle service teams. It searches imported vehicle trips, signals, diagnostic events, and logs to generate evidence-linked summaries that help engineers investigate warnings, compare trips, identify abnormal signal patterns, and explore potential fault causes.

The system is designed to make vehicle diagnostic data easier to investigate without relying on a cloud-based AI service.

> **Project status:** Working MVP/demo. The bundled traces are synthetic. VehicleGPT is not a customer-validated or certified automotive product. Its results must not be used alone to make safety-critical repair decisions.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Example Investigation Questions](#example-investigation-questions)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Health Checks](#health-checks)
- [Environment Variables](#environment-variables)
- [Data Import](#data-import)
- [Safety and Limitations](#safety-and-limitations)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

## Overview

Vehicle diagnostic investigations often require engineers to examine multiple data sources, including trip histories, sensor signals, diagnostic events, and system logs.

VehicleGPT provides a unified investigation workflow that helps users:

1. Import vehicle telemetry and diagnostic records.
2. Search historical trips, signals, events, and logs.
3. Investigate what happened before a warning.
4. Compare warning events with previous trips.
5. Identify signal changes associated with an event.
6. Generate summaries linked to the available evidence.

The objective is to reduce the effort required to understand historical vehicle events while keeping diagnostic conclusions grounded in the imported data.

## Key Features

### 1. Vehicle Event Investigation

Investigate diagnostic warnings using historical telemetry, events, and logs.

### 2. Temporal Analysis

Explore which signals changed before an event and how the vehicle behaved in the preceding time window.

### 3. Historical Trip Comparison

Compare trips to identify differences in signal behavior, driving conditions, and diagnostic events.

### 4. Evidence-Linked Summaries

Present diagnostic findings with supporting records so users can inspect the underlying evidence.

### 5. Local Data Processing

Run the development environment locally using Docker, PostgreSQL, Python, and Node.js.

### 6. Read-Only Operation

VehicleGPT analyzes imported data. It does not send commands to vehicles, change vehicle settings, or control vehicle hardware.

## Example Investigation Questions

VehicleGPT is intended to support questions such as:

- What happened in the 10 minutes before this battery warning?
- When did the warning first occur?
- Which signals changed before the warning?
- Which abnormal signal appeared first?
- Has this warning happened on previous trips?
- How did this trip compare with another trip?
- What was different about this trip compared with trips without warnings?
- Which signals were outside their expected ranges?
- What evidence supports the suspected root cause?
- Which additional measurements are needed to investigate the event further?

The answers depend on the quality, completeness, and time resolution of the imported data.

## Architecture

The development environment consists of the following components:

```text
                  VehicleGPT Workbench
                          |
              +-----------+-----------+
              |                       |
          Frontend                 Backend API
        Node.js / npm             Python / FastAPI
                                      |
                         +------------+------------+
                         |                         |
                    Data Import             Investigation Logic
                         |                         |
                         +------------+------------+
                                      |
                                  PostgreSQL
                                      |
                           Trips, Signals, Events
                                  and Logs
```

This diagram represents the intended high-level workflow. The exact implementation depends on the modules available in the repository.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI |
| Package and environment management | uv |
| Database | PostgreSQL |
| Database runtime | Docker Compose |
| Frontend | Node.js and npm |
| API server | Uvicorn |
| Demo data generation | Python |
| Data ingestion | Python import utility |
| Local development | Windows and Git Bash |

## Requirements

Install the following tools before starting:

- Windows 10 or Windows 11
- Git Bash
- Docker Desktop
- Python 3.12 or later
- uv package manager
- Node.js 18 or later
- npm

Verify the installations:

```bash
git --version
docker --version
docker compose version
python --version
uv --version
node --version
npm --version
```

Ensure Docker Desktop is running before starting PostgreSQL.

## Project Structure

The following is a conceptual overview of the repository components referenced by the setup workflow.

```text
VehicleGPT/
├── backend/
│   ├── app/
│   │   └── main.py
│   └── requirements.txt
├── frontend/
├── tools/
│   ├── generate_demo_data.py
│   └── import_data.py
├── data/
│   └── generated/
├── .env
├── .env.example
├── compose.yaml
└── README.md
```

The actual repository may contain additional modules, configuration files, and tests.

## Installation and Setup

Run the following commands in **Git Bash** from your project root.

### Step 1: Open the project directory

```bash
cd /c/Users/subha/OneDrive/Desktop/VehicleGPT
```

### Step 2: Create the Python environment

```bash
uv venv
```

Install the backend dependencies:

```bash
uv pip install \
  --python .venv/Scripts/python.exe \
  -r backend/requirements.txt
```

### Step 3: Configure environment variables

Create a local `.env` file in the project root.

```dotenv
POSTGRES_DB=vehiclegpt
POSTGRES_USER=vehiclegpt
POSTGRES_PASSWORD=your_local_password

VEHICLEGPT_DATABASE_URL=postgresql://vehiclegpt:your_local_password@127.0.0.1:5432/vehiclegpt

VEHICLEGPT_DATA_DIR=./data
VEHICLEGPT_MAX_IMPORT_BYTES=10485760
VEHICLEGPT_MAX_IMPORT_RECORDS=100000

VEHICLEGPT_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

Replace `your_local_password` with a local development password. The PostgreSQL credentials and database URL must use matching values.

Do not commit `.env` or production credentials to Git.

### Step 4: Start PostgreSQL

From the project root:

```bash
docker compose up -d postgres
```

Check the service status:

```bash
docker compose ps
```

If the service has a different name in your Compose file, replace `postgres` with the actual service name.

Wait until PostgreSQL is healthy before importing data.

### Step 5: Load environment variables

Git Bash:

```bash
set -a
source .env
set +a
```

This exports variables from `.env` into the current shell session.

### Step 6: Generate synthetic demo data

```bash
.venv/Scripts/python.exe tools/generate_demo_data.py
```

This prepares the demonstration dataset using the repository's data generator.

### Step 7: Import the demo dataset

```bash
.venv/Scripts/python.exe tools/import_data.py \
  --input data/generated/demo.jsonl
```

The import utility should validate and ingest the generated records according to the implemented schema and validation rules.

### Step 8: Start the backend API

Open a Git Bash terminal in the project root:

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8000
```

Keep this terminal running.

### Step 9: Start the frontend

Open a second Git Bash terminal:

```bash
cd /c/Users/subha/OneDrive/Desktop/VehicleGPT/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Keep the frontend terminal running.

## Running the Application

Once the backend, database, and frontend are running, access the local services.

| Service | URL |
|---|---|
| Frontend | http://127.0.0.1:5173 |
| Backend health check | http://127.0.0.1:8000/health |
| Interactive API documentation, if enabled | http://127.0.0.1:8000/docs |

These addresses are for local development. They are not public deployment URLs.

## Health Checks

Check the backend:

```bash
curl -i http://127.0.0.1:8000/health
```

Check the frontend:

```bash
curl -I http://127.0.0.1:5173
```

Check PostgreSQL:

```bash
docker compose ps
docker compose logs postgres
```

A successful HTTP response confirms that the relevant endpoint is responding. It does not by itself prove that all investigation workflows or data imports are functioning correctly.

## Environment Variables

| Variable | Purpose |
|---|---|
| `VELTRIQ_DB` | PostgreSQL database name |
| `VELTRIQ_USER` | PostgreSQL username |
| `VELTRIQ_PASSWORD` | Local database password |
| `VELTRIQT_DATABASE_URL` | Backend database connection string |
| `VELTRIQ_DATA_DIR` | Local data directory |
| `VELTRIQT_MAX_IMPORT_BYTES` | Maximum permitted import size in bytes |
| `VELTRIQ_MAX_IMPORT_RECORDS` | Maximum permitted number of imported records |
| `VELTRIQ_ALLOWED_ORIGINS` | Allowed frontend origins for cross-origin requests |

The environment variable names must match those actually read by the backend and configured in Docker Compose.

## Data Import

VELTRIQ's demo workflow uses a generated JSON Lines dataset.

Example input path:

```text
data/generated/demo.jsonl
```

The import process should enforce:

- File-size limits
- Record-count limits
- Schema and data-type validation
- Timestamp validation
- Handling of missing or malformed fields
- Duplicate-event handling where required
- Clear reporting of rejected records
- Safe handling of untrusted imported files

Do not assume every check is implemented until the corresponding code and tests have been verified.

Use synthetic data for demonstrations unless you have appropriate authorization to process real vehicle telemetry.

## Safety and Limitations

VELTRIQ is a diagnostic investigation aid, not a certified automotive diagnostic instrument.

- Bundled traces are synthetic and may not reflect real-world vehicle behavior.
- A temporal relationship between a signal and a warning does not establish causation.
- Incomplete telemetry can lead to misleading conclusions.
- Diagnostic findings require verification against appropriate service documentation and measurements.
- Do not use generated summaries as the sole basis for safety-critical repair decisions.
- The software is read-only and does not control vehicle hardware.

## Development Workflow

Recommended development sequence:

1. Verify the local Python environment and dependencies.
2. Confirm PostgreSQL starts and accepts connections.
3. Validate demo data generation.
4. Test data import and error handling.
5. Start the FastAPI backend and verify health checks.
6. Start the frontend and verify API connectivity.
7. Test investigation queries against known synthetic events.
8. Confirm that generated findings link back to the relevant records.
9. Add automated tests for expected results and failure cases.
10. Document reproducible setup and troubleshooting procedures.

## Troubleshooting

### PostgreSQL does not start

Check Docker Desktop and inspect the container logs:

```bash
docker compose ps
docker compose logs postgres
```

Verify that the configured port is available and the database credentials are consistent.

### Python dependencies fail to install

Check the Python version:

```bash
python --version
uv --version
```

Recreate the virtual environment only if necessary, and reinstall from the project's requirements file.

### The backend cannot connect to PostgreSQL

Check the following:

- PostgreSQL is running and healthy.
- The database name, username, and password match.
- The connection string uses the correct hostname and port.
- The backend has loaded the intended environment variables.

When the backend runs directly on Windows, `127.0.0.1` is generally appropriate for a database port published by Docker. When it runs inside Compose, the database hostname should normally be the Compose service name.

### Demo data import fails

Confirm that the data generator completed successfully:

```bash
ls -l data/generated/demo.jsonl
```

Then rerun the import command and inspect the complete error output.

### The frontend cannot reach the backend

Confirm that both services are running and that the frontend's API base URL matches the backend address. Check the configured CORS origins if the browser reports a cross-origin request failure.

### A port is already in use

Inspect the process using the configured port, or select another port and update the corresponding application configuration.

## Roadmap

Potential future improvements, subject to implementation and validation:

- [ ] More robust telemetry ingestion and validation
- [ ] Advanced trip and event search
- [ ] Time-window-based signal analysis
- [ ] Historical warning comparison
- [ ] Explainable root-cause investigation
- [ ] Evidence-linked diagnostic reports
- [ ] Automated backend and frontend tests
- [ ] Import quality and data coverage metrics
- [ ] Improved logging and operational monitoring
- [ ] Evaluation against independently verified diagnostic cases

## License

No license has been specified yet. Add a `LICENSE` file before distributing the project or granting others permission to reuse its code.

---

**VELTRIQ — Investigate vehicle events through evidence, history, and signal analysis.**
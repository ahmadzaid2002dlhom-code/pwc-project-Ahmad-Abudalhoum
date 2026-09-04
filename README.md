# Commercial Lease Contract Extraction API

A small FastAPI backend that extracts structured metadata from commercial real
estate leases, validates it deterministically, and stores valid contracts in
SQLite.

## Architecture

```text
raw lease text
    -> OpenAI structured extraction
    -> nullable LLMExtractionCandidate
    -> required ValidatedContract and business rules
    -> Python duration calculation
    -> SQLAlchemy / SQLite persistence
    -> FastAPI response
```

- `app/extraction.py` makes one schema-constrained OpenAI request per attempt and
  owns transient retry behavior.
- `app/schemas.py` defines the Pydantic v2 extraction, validation, and response
  schemas. It normalizes currency, rejects negative rent and invalid date order,
  and calculates `contract_duration_days` with Python date arithmetic.
- `app/service.py` orchestrates extraction, validation, and persistence.
- `app/database.py` contains the SQLAlchemy model and the three persistence
  operations.
- `app/main.py` provides the HTTP API and maps application failures to readable
  status codes.

## Setup

Python 3.11 or newer is required.

```bash
python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy the example configuration and replace the placeholders:

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# macOS or Linux
cp .env.example .env
```

Configuration is loaded from environment variables or `.env`:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API credential; required for live extraction |
| `OPENAI_MODEL` | A Structured Outputs model; the example uses `gpt-4o-mini` |
| `DATABASE_URL` | SQLAlchemy URL; defaults to `sqlite:///./app.db` |
| `LLM_MAX_RETRIES` | Transient retries after the initial request; defaults to `3` |
| `LLM_TIMEOUT_SECONDS` | OpenAI request timeout; defaults to `30` |

Never commit `.env`; it is excluded by `.gitignore`.

## Run the API

```bash
uvicorn app.main:app --reload
```

The API creates the configured SQLite tables at startup. Health is available at
`GET /health`.

## Run tests

```bash
pytest -q
```

The automated suite mocks the OpenAI boundary and does not make live API calls.

## Example request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"Apex Holdings LLC leases the premises to Vertex Tech Solutions Corp from June 1, 2024 through May 31, 2026 for AED 12,500 per month. Termination requires 90 days notice."}'
```

Successful requests return `201 Created`:

```json
{
  "lessor": "Apex Holdings LLC",
  "lessee": "Vertex Tech Solutions Corp",
  "commencement_date": "2024-06-01",
  "expiration_date": "2026-05-31",
  "monthly_rent": "12500.00",
  "currency": "AED",
  "termination_notice_period_days": 90,
  "contract_duration_days": 729,
  "id": 1
}
```

Stored contracts are available from `GET /api/v1/contracts` and
`GET /api/v1/contracts/{id}`.

## Docker (bonus)

Build the backend image:

```bash
docker build -t lease-contract-api .
```

Run it on port 8000 using the same environment variables documented above:

```bash
docker run --rm -p 8000:8000 --env-file .env lease-contract-api
```

The `.env` file is excluded from the image and supplied only at runtime. To
persist SQLite data after the container is removed, use a named volume and
override the database path:

```bash
docker volume create lease-contract-data
docker run --rm -p 8000:8000 --env-file .env \
  -e DATABASE_URL=sqlite:////data/app.db \
  -v lease-contract-data:/data \
  lease-contract-api
```

Verify the running container with:

```bash
curl http://127.0.0.1:8000/health
```

## Optional React frontend

The separate React application is in `frontend/`. See
[`frontend/README.md`](frontend/README.md) for its setup, environment, and run
instructions.

## Extraction and validation boundaries

The short extraction instruction tells the model to use only the supplied
document, leave missing information absent, avoid business validation and
financial calculations, and never calculate contract duration.

The OpenAI SDK receives `LLMExtractionCandidate` as the `text_format` for
`responses.parse`. This uses [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
instead of manually parsing model-generated JSON. Missing candidate values are
allowed so the model is not encouraged to invent them. Pydantic then requires
the application fields and applies deterministic validation. Only successfully
validated contracts reach SQLite.

Transient connection, timeout, rate-limit, and server failures use bounded
exponential retries. Exhausted transient failures return `503`; unusable model
responses return `502`; deterministic contract validation failures return `422`;
and unknown contract IDs return `404`.

## Assumptions

- Dates use their stated calendar values. Duration is
  `(expiration_date - commencement_date).days`.
- Currency is normalized and validated as a three-letter uppercase code.
- All extracted fields are required before persistence; invalid candidates are
  not stored.
- The case-study background references a financial risk metric, but the detailed
  requirements provide no formula for such a metric. Therefore, no arbitrary
  financial-risk score was invented. The explicitly defined derived value —
  `contract_duration_days` — is implemented.

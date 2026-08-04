# Tradition Annotation Pipeline

Local review tool for AI-assisted annotations of the Indian traditional-art dataset. Existing `data/metadata.csv` is never re-derived: it is ingested as the canonical `images` record, and annotations/history are stored separately.

## Dataset layout (not stored in Git)

Place the dataset locally in the following structure before ingesting. The `data/` directory is intentionally ignored so image files, archives, and metadata provenance are not published with the application repository.

```text
data/
  metadata.csv
  dataset.zip              # optional source archive
  dataset/
    bhil/
    cheriyal/
    gond/
    kalamkari/
    kalighat/
    madhubani/
    pattachitra/
    phad/
    pichwai/
    saura/
    warli/
```

## Run locally

In one terminal:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY to .env before running annotation jobs
uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `https://t3.gokulp.online` (or `http://localhost:5003`), press **Ingest dataset**, then use **Run AI** in the gallery. The API is available at `https://t2.gokulp.online/docs` (or `http://localhost:5002/docs`).

## Workflow

1. `POST /api/ingest` loads CSV rows idempotently and reports missing CSV/file matches.
2. `POST /api/annotate/run` submits pending images to Gemini Flash Lite in a background task. It uses metadata style as context and persists a structured annotation.
3. Review/edit fields in the UI; each blur saves and records a field-level history entry.
4. Approve or reject records, optionally use bulk actions, then download JSON or CSV. CSV tag arrays are semicolon-separated.

## Migrations

Local development creates the schema automatically. For controlled environments use Alembic from `backend/`:

```bash
alembic upgrade head
```

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL to move off SQLite; model queries do not use SQLite-only database features.

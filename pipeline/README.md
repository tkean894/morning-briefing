# Pipeline

Daily batch jobs (ingestion, clustering, ranking, story generation, audio) run on a schedule via GitHub Actions and write results directly to Postgres. The FastAPI app in `../api` only reads pre-built rows at request time — it never calls an LLM/TTS API inline.

Populated starting in Phase 2.

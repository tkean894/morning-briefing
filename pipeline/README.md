# Pipeline

Daily batch jobs (ingestion, clustering, ranking, story generation, audio) run on a schedule via GitHub Actions and write results directly to Postgres. The FastAPI app in `../api` only reads pre-built rows at request time — it never calls an LLM/TTS API inline.

The actual code lives at [`../api/app/pipeline`](../api/app/pipeline) rather than in this folder — it reuses the FastAPI app's DB models, config, and dependencies directly instead of duplicating them in a separate package. Run it locally with `cd api && python -m app.pipeline.ingest`; in CI it runs via [`.github/workflows/ingest.yml`](../.github/workflows/ingest.yml) on a daily schedule.

- Phase 2 (done): RSS + Guardian/NYT ingestion into `raw_articles`
- Phase 3+ (later): dedup/clustering, ranking, LLM story generation, audio

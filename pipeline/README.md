# Pipeline

Daily batch jobs (ingestion, clustering, ranking, story generation, audio) run on a schedule via GitHub Actions and write results directly to Postgres. The FastAPI app in `../api` only reads pre-built rows at request time — it never calls an LLM/TTS API inline.

The actual code lives at [`../api/app/pipeline`](../api/app/pipeline) rather than in this folder — it reuses the FastAPI app's DB models, config, and dependencies directly instead of duplicating them in a separate package. Run it locally with `cd api && python -m app.pipeline.ingest`; in CI it runs via [`.github/workflows/ingest.yml`](../.github/workflows/ingest.yml) on a daily schedule.

- Phase 2 (done): RSS + Guardian/NYT ingestion into `raw_articles`
- Phase 3 (done): dedup/clustering (`app/pipeline/cluster.py`) into `story_clusters`, with a first-pass importance score (source count, credibility, recency). Uses TF-IDF + complete-linkage agglomerative clustering rather than an embeddings API -- cheap and effective at this article volume; revisit if quality needs it later.
- Phase 4 (done): LLM story generation (`app/pipeline/generate.py`) into `stories`/`story_sources`, plus the "Today in 30 seconds" digest (`daily_digests`). Uses Gemini's free tier (`gemini-flash-lite-latest`) rather than Anthropic, which has no free tier -- paced to the free tier's rate limits since it's a scheduled batch job with no one waiting on it.
- Phase 5+ (later): per-user briefing assembly, audio, frontend

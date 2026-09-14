# Morning Briefs

"Know what matters today in 10 minutes." A personalized morning news briefing app — one finite, ranked briefing per day instead of an infinite feed.

## Layout

- `web/` — Next.js (TypeScript, Tailwind, App Router) frontend, deployed to Vercel
- `api/` — FastAPI backend, deployed to Render. Serves pre-built briefings; never calls LLM/TTS at request time
- `pipeline/` — daily batch jobs (ingestion → clustering → ranking → story generation → audio), run on a schedule via GitHub Actions, writing results into Postgres

## Architecture

Expensive work (news ingestion, dedup/clustering, LLM summarization, TTS) runs once per day, shared across all users. Personalization happens in a cheap per-user "assembly" step (selecting/ordering shared stories) with no LLM/TTS calls — so cost scales with story volume, not user count.

Stack: Next.js/TS/Tailwind, FastAPI, Postgres (Neon, pgvector), Clerk (auth), Cloudflare R2 (audio storage), Claude (LLM), Google Cloud TTS.

## Local development

**Frontend**
```
cd web
npm install
npm run dev
```

**Backend**
```
cd api
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Copy `.env.example` → `.env` (api) and `.env.local.example` → `.env.local` (web) and fill in real values as each phase requires them. Never commit real secrets.

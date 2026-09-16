# Audio Briefing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared (non-personalized), four-length (5/10/15/20 min) daily audio briefing: a Gemini-generated conversational script, synthesized via Google Cloud TTS, stored in Cloudflare R2, and playable from the home page.

**Architecture:** A new daily pipeline step (`app/pipeline/audio.py`) selects the day's top shared stories per length (reusing `app.assembly`'s must-include/category-cap pattern, minus personalization), generates one script per length via Gemini, synthesizes it with Google Cloud TTS, uploads the MP3 to R2, and writes one `AudioBriefing` row per `(date, length)`. `GET /briefings/today` joins in the row matching the requesting user's preferred length. The frontend shows a "Listen to Brief" button that reveals a native `<audio>` element when a URL is present.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Gemini (`google-genai`, already in use), `google-cloud-texttospeech`, `boto3` (R2's S3-compatible API), pytest (new to this repo), Next.js/React (frontend).

**Spec:** `docs/superpowers/specs/2026-09-16-audio-briefing-design.md`

## Global Constraints

- Shared, not personalized: one `AudioBriefing` row per `(date, length_minutes)`, not per user.
- All four lengths (5, 10, 15, 20 minutes) generated daily.
- TTS: Google Cloud TTS, **Standard voices** (not WaveNet/Neural2) to stay inside the free 4M-char/month tier.
- Storage: Cloudflare R2, S3-compatible API via `boto3`.
- Audio generation failures must not break the rest of the daily pipeline (per-length try/except, log and skip).
- Sensitive stories (`is_sensitive=True`) must carry their fact/perspective separation into the audio script, not flatten it.
- **This project has exactly one Postgres database** (a single Neon instance) — there is no separate dev/staging DB; local dev and production share it. Never write an automated test that connects to it. Any step that runs `alembic upgrade/downgrade` or otherwise touches this database must be run by the human operator directly in their own terminal, not executed via an agent's Bash tool — Claude Code's own safety classifier blocks production-database mutations from agent-run Bash, and this is a real constraint of the project, not just a permissions quirk to work around.
- No custom test DB/SQLite substitution: the models use Postgres-specific `JSONB` columns that don't translate to SQLite, so don't attempt to stand up an in-memory test database for this feature. Keep automated tests to pure logic with no DB or network I/O, matching this codebase's existing convention (`cluster.py`, `generate.py`, `ingest.py` have no unit tests either — verified by manually running the pipeline).
- No frontend test framework exists in this repo (no Jest/Vitest configured) — don't introduce one for this feature. Frontend verification is `npm run lint`, `npm run build`, and a manual dev-server check, matching how the rest of `web/` has been verified in this project.

---

### Task 1: Audio story-selection logic + pytest infrastructure

**Files:**
- Create: `api/pytest.ini`
- Create: `api/tests/__init__.py`
- Create: `api/tests/pipeline/__init__.py`
- Create: `api/tests/pipeline/test_audio_selection.py`
- Create: `api/app/pipeline/audio_selection.py`
- Modify: `api/requirements.txt`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `app.models.Story` (existing — `category`, `summary`, `why_it_matters`, `what_to_watch`, `key_facts`, `importance_score` fields)
- Produces: `select_stories_for_audio(stories: list[Story], target_length_minutes: int) -> list[Story]`, `estimate_duration_seconds(stories: list[Story]) -> int`, constants `AUDIO_WORDS_PER_MINUTE`, `AUDIO_MUST_INCLUDE_COUNT`, `AUDIO_MAX_PER_CATEGORY` — all consumed by Task 4's `app/pipeline/audio.py`.

- [ ] **Step 1: Add pytest to requirements and create test scaffolding**

Add this line to `api/requirements.txt` (keep the file's existing alphabetical-ish ordering, insert near other top-level tooling — exact position doesn't matter, pip doesn't care):

```
pytest==8.4.1
```

Create `api/pytest.ini`:

```ini
[pytest]
testpaths = tests
```

Create `api/tests/__init__.py` (empty file) and `api/tests/pipeline/__init__.py` (empty file).

- [ ] **Step 2: Write the failing test**

Create `api/tests/pipeline/test_audio_selection.py`:

```python
from app.models import Story
from app.pipeline.audio_selection import (
    AUDIO_MAX_PER_CATEGORY,
    AUDIO_MUST_INCLUDE_COUNT,
    AUDIO_WORDS_PER_MINUTE,
    estimate_duration_seconds,
    select_stories_for_audio,
)


def _make_story(category: str, importance_score: float, word_count: int) -> Story:
    words = " ".join(["word"] * word_count)
    return Story(
        category=category,
        summary=words,
        why_it_matters="",
        what_to_watch="",
        key_facts=[],
        importance_score=importance_score,
    )


def test_select_stories_for_audio_respects_length_budget():
    stories = [
        _make_story("technology", importance_score=100 - i, word_count=AUDIO_WORDS_PER_MINUTE)
        for i in range(10)
    ]

    selected = select_stories_for_audio(stories, target_length_minutes=5)

    assert len(selected) == 5
    assert [s.importance_score for s in selected] == [100, 99, 98, 97, 96]


def test_select_stories_for_audio_always_includes_top_must_include_stories():
    stories = [
        _make_story("politics", importance_score=1000, word_count=AUDIO_WORDS_PER_MINUTE),
        _make_story("world-news", importance_score=900, word_count=AUDIO_WORDS_PER_MINUTE),
    ] + [
        _make_story("sports", importance_score=10 - i, word_count=AUDIO_WORDS_PER_MINUTE)
        for i in range(10)
    ]

    selected = select_stories_for_audio(stories, target_length_minutes=5)

    assert selected[0].importance_score == 1000
    assert selected[1].importance_score == 900


def test_select_stories_for_audio_caps_stories_per_category():
    stories = [
        _make_story("sports", importance_score=100 - i, word_count=AUDIO_WORDS_PER_MINUTE)
        for i in range(10)
    ]

    selected = select_stories_for_audio(stories, target_length_minutes=20)

    sports_count = sum(1 for s in selected if s.category == "sports")
    assert sports_count == AUDIO_MAX_PER_CATEGORY


def test_select_stories_for_audio_empty_input_returns_empty():
    assert select_stories_for_audio([], target_length_minutes=10) == []


def test_estimate_duration_seconds_matches_word_count_at_spoken_pace():
    stories = [_make_story("technology", importance_score=1, word_count=AUDIO_WORDS_PER_MINUTE)]

    assert estimate_duration_seconds(stories) == 60


def test_estimate_duration_seconds_empty_input_is_zero():
    assert estimate_duration_seconds([]) == 0
```

Also confirm `AUDIO_MUST_INCLUDE_COUNT == 2` is implicitly exercised by the must-include test above (two off-category stories both survive selection).

- [ ] **Step 3: Run tests to verify they fail**

Run (from `api/`, with the venv active):
```
pip install -r requirements.txt
pytest tests/pipeline/test_audio_selection.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'app.pipeline.audio_selection'`.

- [ ] **Step 4: Write the implementation**

Create `api/app/pipeline/audio_selection.py`:

```python
"""Pure story-selection and duration-estimation logic for the shared daily
audio briefing. Kept separate from app.pipeline.audio's Gemini/TTS/R2 I/O so
it can be unit tested without any network calls.

Unlike app.assembly (which personalizes per user), this selects the same
story set for everyone, mirroring how DailyDigest is shared rather than
personalized. See docs/superpowers/specs/2026-09-16-audio-briefing-design.md.
"""

from app.models import Story

# Spoken delivery is slower than the silent-reading pace app.assembly uses
# (200 wpm) for its read-time estimate.
AUDIO_WORDS_PER_MINUTE = 150

# How many of the day's single most important stories always make the audio
# briefing regardless of category/length budget, mirroring
# app.assembly.MUST_INCLUDE_COUNT.
AUDIO_MUST_INCLUDE_COUNT = 2

# Caps any one category (sports is the common flood case) from crowding out
# the rest of the briefing, mirroring app.assembly.MAX_PER_CATEGORY_IN_BRIEFING.
AUDIO_MAX_PER_CATEGORY = 4


def _story_word_count(story: Story) -> int:
    text = " ".join(
        [
            story.summary,
            story.why_it_matters,
            story.what_to_watch,
            " ".join(story.key_facts),
        ]
    )
    return len(text.split())


def select_stories_for_audio(
    stories: list[Story], target_length_minutes: int
) -> list[Story]:
    """Selects a shared (non-personalized) story set for the audio
    briefing, budgeted to target_length_minutes at spoken pace. `stories`
    must already be sorted by importance_score descending."""
    if not stories:
        return []

    must_include = stories[:AUDIO_MUST_INCLUDE_COUNT]
    candidates = stories[AUDIO_MUST_INCLUDE_COUNT:]

    selected = list(must_include)
    total_minutes = sum(
        _story_word_count(s) / AUDIO_WORDS_PER_MINUTE for s in must_include
    )
    category_counts: dict[str, int] = {}
    for s in must_include:
        category_counts[s.category] = category_counts.get(s.category, 0) + 1

    for story in candidates:
        if total_minutes >= target_length_minutes:
            break
        if category_counts.get(story.category, 0) >= AUDIO_MAX_PER_CATEGORY:
            continue
        selected.append(story)
        total_minutes += _story_word_count(story) / AUDIO_WORDS_PER_MINUTE
        category_counts[story.category] = category_counts.get(story.category, 0) + 1

    return selected


def estimate_duration_seconds(stories: list[Story]) -> int:
    """Estimates spoken duration from selected stories' word counts. Used
    because Google Cloud TTS doesn't return duration, and reading it from
    the generated MP3 is unnecessary precision for a "~10 min" label."""
    total_words = sum(_story_word_count(s) for s in stories)
    minutes = total_words / AUDIO_WORDS_PER_MINUTE
    return round(minutes * 60)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/pipeline/test_audio_selection.py -v`
Expected: all 6 tests PASS.

- [ ] **Step 6: Wire pytest into CI**

In `.github/workflows/ci.yml`, in the `api` job, add a step after `pip install -r requirements.txt` and before the existing `python -c "import app.main"` step:

```yaml
      - run: pytest
```

- [ ] **Step 7: Commit**

```bash
git add api/pytest.ini api/tests/ api/app/pipeline/audio_selection.py api/requirements.txt .github/workflows/ci.yml
git commit -m "Add pytest infra and shared audio story-selection logic"
```

---

### Task 2: `AudioBriefing` database model + migration

**Files:**
- Modify: `api/app/models.py`
- Create: `api/alembic/versions/<autogenerated>_add_audio_briefings.py`

**Interfaces:**
- Produces: `app.models.AudioBriefing` (fields: `id`, `briefing_date`, `length_minutes`, `script`, `audio_url`, `duration_seconds`, `created_at`) — consumed by Task 4 (writes rows) and Task 5 (reads rows).

- [ ] **Step 1: Add the model**

In `api/app/models.py`, add after the `DailyDigest` class (same shared-per-day pattern, so keep them adjacent):

```python
class AudioBriefing(Base):
    """Shared (non-personalized) daily audio briefing, one row per
    (date, length) pair, generated by app.pipeline.audio. See
    docs/superpowers/specs/2026-09-16-audio-briefing-design.md."""

    __tablename__ = "audio_briefings"
    __table_args__ = (UniqueConstraint("briefing_date", "length_minutes"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    briefing_date: Mapped[datetime.date] = mapped_column(Date, index=True)
    length_minutes: Mapped[int]
    script: Mapped[str]
    audio_url: Mapped[str]
    duration_seconds: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
```

- [ ] **Step 2: Verify the module still imports cleanly**

Run (from `api/`, venv active): `python -c "import app.models"`
Expected: no output, exit code 0.

- [ ] **Step 3: Generate the migration**

Run (from `api/`, venv active):
```
alembic revision --autogenerate -m "add audio briefings"
```
This creates a new file under `api/alembic/versions/` with an auto-generated revision ID and `down_revision` automatically set to the current head (`b6373a3d72c8`). Open the generated file and confirm it contains an `op.create_table("audio_briefings", ...)` call with all six columns and the unique constraint on `(briefing_date, length_minutes)`. If autogenerate produced anything unexpected (e.g. picked up unrelated diffs), edit the file so `upgrade()`/`downgrade()` only cover this table — autogenerate diffs the whole schema, so it can occasionally pick up noise unrelated to this change.

- [ ] **Step 4: Apply the migration — human-run step, not agent-run**

This connects to the project's single (production) database. **Do not run this via an agent's Bash tool.** Tell the human operator to run, in their own terminal, with the venv active and `DATABASE_URL` set to the value in `api/.env`:
```
cd api
alembic upgrade head
```
and confirm the new revision applies cleanly. Wait for their confirmation before proceeding to Task 4 (which writes to this table).

- [ ] **Step 5: Commit**

```bash
git add api/app/models.py api/alembic/versions/
git commit -m "Add AudioBriefing model and migration"
```

---

### Task 3: TTS/R2 configuration

**Files:**
- Modify: `api/app/config.py`
- Modify: `api/.env.example`
- Modify: `api/requirements.txt`
- Create: `api/tests/test_config.py`

**Interfaces:**
- Produces: `settings.google_tts_credentials_json`, `settings.r2_account_id`, `settings.r2_access_key_id`, `settings.r2_secret_access_key`, `settings.r2_bucket_name`, `settings.r2_public_url_base` — all consumed by Task 4.

- [ ] **Step 1: Write the failing test**

Create `api/tests/test_config.py`:

```python
from app.config import Settings


def test_settings_loads_with_defaults_for_new_audio_fields():
    settings = Settings(_env_file=None)

    assert settings.google_tts_credentials_json == ""
    assert settings.r2_account_id == ""
    assert settings.r2_access_key_id == ""
    assert settings.r2_secret_access_key == ""
    assert settings.r2_bucket_name == ""
    assert settings.r2_public_url_base == ""
```

`_env_file=None` skips loading `api/.env` for this test, so it checks the class's own defaults rather than whatever happens to be in the developer's local `.env`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with a pydantic validation error (unknown/missing fields).

- [ ] **Step 3: Add the settings**

In `api/app/config.py`, add these fields to the `Settings` class (after `gemini_api_key`):

```python
    google_tts_credentials_json: str = ""
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_public_url_base: str = ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Document the new env vars**

Add to `api/.env.example` (after `GEMINI_API_KEY`):

```
# Required for app.pipeline.audio (audio briefing generation)
# Full JSON contents of a Google Cloud service account key with the
# Cloud Text-to-Speech API enabled, as a single-line string.
GOOGLE_TTS_CREDENTIALS_JSON=
# Cloudflare R2 (S3-compatible) bucket for storing generated audio files
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=
# Public base URL the bucket is served from (R2 public bucket URL or a
# custom domain in front of it), no trailing slash
R2_PUBLIC_URL_BASE=
```

- [ ] **Step 6: Add the new Python dependencies**

Add to `api/requirements.txt`:

```
google-cloud-texttospeech==2.27.0
boto3==1.40.0
```

Run (from `api/`, venv active): `pip install -r requirements.txt`

- [ ] **Step 7: Commit**

```bash
git add api/app/config.py api/.env.example api/requirements.txt api/tests/test_config.py
git commit -m "Add TTS/R2 configuration for audio briefings"
```

---

### Task 4: Audio pipeline orchestration (`app/pipeline/audio.py`)

**Files:**
- Create: `api/app/pipeline/audio.py`
- Modify: `.github/workflows/ingest.yml`

**Interfaces:**
- Consumes: `app.pipeline.audio_selection.{select_stories_for_audio, estimate_duration_seconds}` (Task 1), `app.models.{Story, AudioBriefing}` (Task 2), `app.config.settings.{google_tts_credentials_json, r2_account_id, r2_access_key_id, r2_secret_access_key, r2_bucket_name, r2_public_url_base}` (Task 3), and reuses `app.pipeline.generate._client`/`_generate_with_rate_limit`-style patterns (new copies here, not imported, since `generate.py`'s helpers are private to that module — see Step 3).
- Produces: `run()`, invoked by `.github/workflows/ingest.yml` as `python -m app.pipeline.audio`, and by any human running it manually.

This task has no automated tests (per Global Constraints — it's DB- and network-I/O-heavy, and this codebase's convention for pipeline orchestration modules like `cluster.py`/`generate.py`/`ingest.py` is manual verification, not unit tests). Verification is a manual pipeline run in Step 5.

- [ ] **Step 1: Read the existing per-item rate-limited generation pattern**

Before writing this file, re-read `api/app/pipeline/generate.py` in full (particularly `_client`, `_generate_with_rate_limit`, and the per-cluster try/except loop in `run()`) — this task's Gemini script-generation call and per-length error isolation follow the same shape.

- [ ] **Step 2: Write the implementation**

Create `api/app/pipeline/audio.py`:

```python
"""Generates the shared daily audio briefing: one Gemini-written
conversational script and one Google Cloud TTS-synthesized MP3 per length
(5/10/15/20 min), uploaded to Cloudflare R2. See
docs/superpowers/specs/2026-09-16-audio-briefing-design.md.

Shared across all users (not personalized), same cost model as
app.pipeline.generate: this runs once per length per day regardless of
user count.
"""

import datetime
import json
import logging
import time

import boto3
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from google.cloud import texttospeech
from google.oauth2 import service_account
from sqlalchemy import delete, select

from app.config import settings
from app.db import SessionLocal
from app.models import AudioBriefing, Story
from app.pipeline.audio_selection import (
    estimate_duration_seconds,
    select_stories_for_audio,
)

logger = logging.getLogger("audio")

MODEL = "gemini-flash-lite-latest"
RATE_LIMIT_DELAY_SECONDS = 13
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 30

LENGTHS_MINUTES = [5, 10, 15, 20]

SCRIPT_SYSTEM_PROMPT = """You are a knowledgeable person giving a friend their morning news briefing out loud.

Rules:
1. Write a flowing, conversational spoken script, not a list of bullet points. Start with a natural greeting like "Good morning. Here's what you need to know today."
2. Use ONLY the facts given for each story. Never invent names, numbers, quotes, or events not stated.
3. Do not simply read the written summaries verbatim -- rephrase into natural spoken language with brief transitions between stories ("Meanwhile, in tech news...", "On the markets front...").
4. For any story marked as sensitive, keep its fact/perspective separation intact when spoken -- state what's established, then attribute differing views (e.g. "Democrats argue X, while the company maintains Y"), rather than collapsing it into one flat narrated take.
5. Keep the tone factual and neutral. Avoid sensationalism.
6. End with a brief, natural sign-off."""


def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_with_rate_limit(client: genai.Client, contents: str) -> str:
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SCRIPT_SYSTEM_PROMPT
                ),
            )
            time.sleep(RATE_LIMIT_DELAY_SECONDS)
            return response.text
        except genai_errors.ClientError as exc:
            if exc.code == 429 and attempt < RATE_LIMIT_RETRIES:
                logger.warning(
                    "Rate limited, backing off %ds (attempt %d/%d)",
                    RATE_LIMIT_BACKOFF_SECONDS,
                    attempt + 1,
                    RATE_LIMIT_RETRIES,
                )
                time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
                continue
            raise
    raise RuntimeError("unreachable")


def _build_script_prompt(stories: list[Story]) -> str:
    lines = ["Today's stories, in the order to present them:", ""]
    for s in stories:
        lines.append(f"[{s.category}] {s.headline}")
        lines.append(f"Summary: {s.summary}")
        lines.append(f"Why it matters: {s.why_it_matters}")
        lines.append(f"What to watch: {s.what_to_watch}")
        if s.is_sensitive and s.perspectives:
            lines.append("This is a sensitive/contested topic. Perspectives:")
            for p in s.perspectives:
                lines.append(f"  - {p}")
        lines.append("")
    return "\n".join(lines)


def _tts_client() -> texttospeech.TextToSpeechClient:
    info = json.loads(settings.google_tts_credentials_json)
    credentials = service_account.Credentials.from_service_account_info(info)
    return texttospeech.TextToSpeechClient(credentials=credentials)


def _synthesize_speech(tts_client: texttospeech.TextToSpeechClient, script: str) -> bytes:
    synthesis_input = texttospeech.SynthesisInput(text=script)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )


def _upload_to_r2(r2_client, audio_bytes: bytes, date: datetime.date, length_minutes: int) -> str:
    key = f"audio-briefings/{date.isoformat()}/{length_minutes}.mp3"
    r2_client.put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=audio_bytes,
        ContentType="audio/mpeg",
    )
    return f"{settings.r2_public_url_base}/{key}"


def _generate_length(
    genai_client: genai.Client,
    tts_client: texttospeech.TextToSpeechClient,
    r2_client,
    db,
    all_stories: list[Story],
    date: datetime.date,
    length_minutes: int,
) -> None:
    selected = select_stories_for_audio(all_stories, length_minutes)
    if not selected:
        logger.info("No stories available for %d-minute audio briefing", length_minutes)
        return

    prompt = _build_script_prompt(selected)
    script = _generate_with_rate_limit(genai_client, prompt)

    audio_bytes = _synthesize_speech(tts_client, script)
    audio_url = _upload_to_r2(r2_client, audio_bytes, date, length_minutes)
    duration_seconds = estimate_duration_seconds(selected)

    db.add(
        AudioBriefing(
            briefing_date=date,
            length_minutes=length_minutes,
            script=script,
            audio_url=audio_url,
            duration_seconds=duration_seconds,
        )
    )
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()

        # Wipe today's audio briefings so this run is idempotent.
        db.execute(delete(AudioBriefing).where(AudioBriefing.briefing_date == today))
        db.commit()

        all_stories = list(
            db.execute(
                select(Story)
                .where(Story.date == today)
                .order_by(Story.importance_score.desc())
            ).scalars()
        )
        if not all_stories:
            logger.info("No stories to generate audio for today")
            return

        genai_client = _client()
        tts_client = _tts_client()
        r2_client = _r2_client()

        succeeded = 0
        for length_minutes in LENGTHS_MINUTES:
            try:
                _generate_length(
                    genai_client, tts_client, r2_client, db, all_stories, today, length_minutes
                )
                succeeded += 1
            except Exception:
                db.rollback()
                logger.exception(
                    "Failed to generate %d-minute audio briefing", length_minutes
                )

        logger.info(
            "Generated %d/%d audio briefing lengths for %s",
            succeeded,
            len(LENGTHS_MINUTES),
            today,
        )
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
```

- [ ] **Step 3: Verify the module imports cleanly**

Run (from `api/`, venv active): `python -c "import app.pipeline.audio"`
Expected: no output, exit code 0. (This only checks imports resolve — it does not call any external API.)

- [ ] **Step 4: Wire into the daily GitHub Actions workflow**

In `.github/workflows/ingest.yml`, add a new step after the existing `python -m app.pipeline.generate` step:

```yaml
      - run: python -m app.pipeline.audio
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GOOGLE_TTS_CREDENTIALS_JSON: ${{ secrets.GOOGLE_TTS_CREDENTIALS_JSON }}
          R2_ACCOUNT_ID: ${{ secrets.R2_ACCOUNT_ID }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
          R2_BUCKET_NAME: ${{ secrets.R2_BUCKET_NAME }}
          R2_PUBLIC_URL_BASE: ${{ secrets.R2_PUBLIC_URL_BASE }}
```

Tell the human operator they need to: create a Google Cloud project with the Cloud Text-to-Speech API enabled and a service account key (paste the full JSON as `GOOGLE_TTS_CREDENTIALS_JSON`), create a Cloudflare R2 bucket with public access (or a custom domain) for `R2_PUBLIC_URL_BASE`, and add all six new secrets to the GitHub repo (Settings → Secrets and variables → Actions) before this step will succeed. This step will fail without those — that's expected until they're set up, not a bug in the code.

- [ ] **Step 5: Manual smoke test (human-run, requires real credentials)**

Once the human operator has real Google Cloud TTS and R2 credentials in `api/.env`, and Task 2's migration has been applied, they should run, from `api/` with the venv active:
```
python -m app.pipeline.audio
```
and confirm: it logs `Generated 4/4 audio briefing lengths for <date>`, and querying `SELECT * FROM audio_briefings WHERE briefing_date = CURRENT_DATE` shows 4 rows with working `audio_url` values (open one in a browser to confirm it plays). This step requires real API credentials and touches the shared database — do not attempt it without the human operator present, and do not attempt it via an agent's Bash tool.

- [ ] **Step 6: Commit**

```bash
git add api/app/pipeline/audio.py .github/workflows/ingest.yml
git commit -m "Add audio pipeline: script generation, TTS synthesis, R2 upload"
```

---

### Task 5: API — expose audio in `GET /briefings/today`

**Files:**
- Modify: `api/app/schemas.py`
- Modify: `api/app/routers/briefings.py`
- Create: `api/tests/test_schemas.py`

**Interfaces:**
- Consumes: `app.models.AudioBriefing` (Task 2)
- Produces: `BriefingOut.audio_url: str | None`, `BriefingOut.audio_duration_seconds: int | None` — consumed by the frontend (Task 6).

- [ ] **Step 1: Write the failing test**

Create `api/tests/test_schemas.py`:

```python
import datetime

from app.schemas import BriefingOut


def test_briefing_out_defaults_audio_fields_to_none():
    briefing = BriefingOut(
        date=datetime.date(2026, 9, 16),
        briefing_length_minutes=10,
        story_count=0,
    )

    assert briefing.audio_url is None
    assert briefing.audio_duration_seconds is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_schemas.py -v`
Expected: FAIL — `audio_url` is not a recognized field (pydantic raises on the attribute access, or the field simply doesn't exist).

- [ ] **Step 3: Add the fields**

In `api/app/schemas.py`, modify `BriefingOut`:

```python
class BriefingOut(BaseModel):
    date: datetime.date
    briefing_length_minutes: BriefingLength
    story_count: int
    estimated_read_minutes: float = 0.0
    digest: DigestOut | None = None
    stories: list[BriefingStoryOut] = []
    audio_url: str | None = None
    audio_duration_seconds: int | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_schemas.py -v`
Expected: PASS.

- [ ] **Step 5: Join the AudioBriefing row in the router**

In `api/app/routers/briefings.py`, add `AudioBriefing` to the import from `app.models`:

```python
from app.models import AudioBriefing, DailyDigest, User, UserPreference
```

Then, inside `get_todays_briefing`, after the existing `digest_out` block and before building `stories_out`, add:

```python
    audio_url = None
    audio_duration_seconds = None
    if result["story_count"] > 0:
        today = result["date"] if isinstance(result["date"], datetime.date) else None
        if today:
            audio_row = db.execute(
                select(AudioBriefing).where(
                    AudioBriefing.briefing_date == today,
                    AudioBriefing.length_minutes == prefs.briefing_length_minutes,
                )
            ).scalar_one_or_none()
            if audio_row:
                audio_url = audio_row.audio_url
                audio_duration_seconds = audio_row.duration_seconds
```

And add the two fields to the final `BriefingOut(...)` construction:

```python
    return BriefingOut(
        date=result["date"],
        briefing_length_minutes=prefs.briefing_length_minutes,
        story_count=result["story_count"],
        estimated_read_minutes=result.get("estimated_read_minutes", 0.0),
        digest=digest_out,
        stories=stories_out,
        audio_url=audio_url,
        audio_duration_seconds=audio_duration_seconds,
    )
```

- [ ] **Step 6: Verify the module imports cleanly**

Run: `python -c "import app.main"`
Expected: no output, exit code 0.

- [ ] **Step 7: Commit**

```bash
git add api/app/schemas.py api/app/routers/briefings.py api/tests/test_schemas.py
git commit -m "Expose audio briefing URL/duration in GET /briefings/today"
```

---

### Task 6: Frontend — "Listen to Brief" player

**Files:**
- Modify: `web/src/lib/api.ts`
- Create: `web/src/components/AudioPlayer.tsx`
- Modify: `web/src/app/page.tsx`

**Interfaces:**
- Consumes: `Briefing.audio_url: string | null`, `Briefing.audio_duration_seconds: number | null` (Task 5's API response shape)
- Produces: `<AudioPlayer audioUrl={string} />` component

No automated tests for this task (no frontend test framework in this repo — see Global Constraints). Verification is `npm run lint`, `npm run build`, and a manual dev-server check in Step 4.

- [ ] **Step 1: Add the new fields to the Briefing type**

In `web/src/lib/api.ts`, modify the `Briefing` type:

```typescript
export type Briefing = {
  date: string;
  briefing_length_minutes: BriefingLength;
  story_count: number;
  estimated_read_minutes: number;
  digest: Digest | null;
  stories: BriefingStory[];
  audio_url: string | null;
  audio_duration_seconds: number | null;
};
```

- [ ] **Step 2: Create the player component**

Create `web/src/components/AudioPlayer.tsx`:

```tsx
"use client";

import { useState } from "react";

export function AudioPlayer({ audioUrl }: { audioUrl: string }) {
  const [expanded, setExpanded] = useState(false);

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        className="rounded-md border border-ink/15 px-5 py-3 text-sm font-medium text-ink transition hover:border-ink/40"
      >
        Listen to brief
      </button>
    );
  }

  return (
    <audio controls autoPlay src={audioUrl} className="h-11 w-full max-w-xs">
      Your browser does not support the audio element.
    </audio>
  );
}
```

- [ ] **Step 3: Wire it into the home page**

In `web/src/app/page.tsx`, add the import:

```typescript
import { AudioPlayer } from "@/components/AudioPlayer";
```

Then, in the button row (currently just `Start reading` and `Edit preferences`), add the player before the existing buttons, only when `audio_url` is present:

```tsx
      {briefing.story_count > 0 && (
        <div className="mb-10 flex flex-wrap items-center gap-3">
          {briefing.audio_url && <AudioPlayer audioUrl={briefing.audio_url} />}
          <a
            href="#briefing"
            className="rounded-md bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:bg-ink/85"
          >
            Start reading
          </a>
          <Link
            href="/settings/preferences"
            className="rounded-md border border-ink/15 px-5 py-3 text-sm font-medium text-ink transition hover:border-ink/40"
          >
            Edit preferences
          </Link>
        </div>
      )}
```

- [ ] **Step 4: Verify — lint, build, and manual check**

Run (from `web/`):
```
npm run lint
npm run build
```
Both must pass with no errors.

Then, since real audio requires Task 4's pipeline to have actually run with real credentials (which won't exist yet in most dev setups), manually verify gracefully-missing-audio behavior: start the dev server (`npm run dev`), sign in, and confirm the home page renders correctly with the "Listen to brief" button simply absent (since `audio_url` will be `null` until Task 4 has produced real data) — this is the expected, correct behavior per Step 3's conditional render, not a bug.

- [ ] **Step 5: Commit**

```bash
git add web/src/lib/api.ts web/src/components/AudioPlayer.tsx web/src/app/page.tsx
git commit -m "Add Listen to Brief audio player to the home page"
```

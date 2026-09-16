# Audio Briefing — Design Spec

Status: approved, pending implementation plan
Date: 2026-09-16

## Problem

The original product spec lists "Basic audio briefing" as an MVP feature, matching the spec's
example home page (`[Listen to Brief] [Start Reading]`). It's currently unbuilt: `audio_enabled`
exists only as a stored, unused boolean preference. No TTS, no storage, no player.

## Scope decisions

These were the two product-shape questions that determine cost and architecture, both decided
explicitly rather than defaulted:

1. **Shared, not personalized.** The audio briefing is one shared script + file per day (per
   length), built from the day's top-ranked stories — the same relationship `DailyDigest` (the
   "Today in 30 seconds" bullets) already has to personalization. This keeps audio generation
   cost scaling with story volume, not user count, matching the cost model the rest of the
   pipeline is already built around (expensive work runs once per day, shared across users).
   A fully-personalized-per-user audio briefing was considered and rejected: it would require an
   LLM script call + a TTS call per user per day, breaking that cost model. A user-supplied
   API-key model (users paste their own TTS/LLM keys) was also considered and rejected — it
   only shifts cost, doesn't reduce it, requires two keys (LLM + TTS) from the user, and
   introduces exactly the account-setup friction the product's "extremely intuitive, not
   cluttered" design goal is trying to avoid for a college-student/young-professional audience.
2. **All four lengths (5/10/15/20 min) for MVP**, matching the text briefing's existing length
   options, rather than a single fixed length. Roughly 4x the LLM script + TTS cost of a
   single-length approach, decided deliberately.

## Cost estimate

4 length variants/day × ~30 days ≈ 1.27M characters/month sent to TTS (estimated from selected
story word counts at spoken pace). Google Cloud TTS Standard voices are free up to 4M
characters/month (a permanent free tier, not a trial) — this usage stays comfortably inside it.
WaveNet/Neural2 voices (more natural-sounding) only get 1M free chars/month, which this volume
would slightly exceed (~$1-2/month). **Start on Standard voices** to stay fully free; revisit
voice quality later if it feels too robotic.

LLM script generation reuses the existing Gemini setup (already free-tier, already in use for
story generation) — no new LLM cost consideration beyond the existing one.

## Storage: Cloudflare R2

S3-compatible, 10GB free storage, **zero egress fees** — the deciding factor, since every
listen streams the file and egress-fee storage would scale cost with listens. Expected usage
(4 files/day × ~30 days × ~5-10MB/file) stays well under 1GB/month added, far inside the free
tier for a long time. The daily pipeline uploads the generated MP3 to R2 and stores only the
resulting URL in Postgres — audio bytes never touch the database.

## Database schema

One new table, no changes to existing ones:

```python
class AudioBriefing(Base):
    __tablename__ = "audio_briefings"
    __table_args__ = (UniqueConstraint("briefing_date", "length_minutes"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    briefing_date: Mapped[datetime.date] = mapped_column(Date, index=True)
    length_minutes: Mapped[int]  # 5 | 10 | 15 | 20
    script: Mapped[str]
    audio_url: Mapped[str]
    duration_seconds: Mapped[int]
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
```

One row per `(date, length)`, shared across all users. `GET /briefings/today` joins in the row
matching the requesting user's `briefing_length_minutes` preference.

## Pipeline step: `app/pipeline/audio.py`

Runs after `generate.py` in the daily pipeline (ingest → cluster → generate → **audio**), and
mirrors `cluster.py`'s idempotency pattern: wipe/replace today's `AudioBriefing` rows so reruns
are safe.

For each of the 4 lengths:

1. **Select stories** — reuse `assembly.py`'s must-include-top-2 + importance-ranked fill
   pattern, but *without* the personalization weighting (`category_weights`/`specific_weights`),
   since this is shared. Budget against a spoken-pace words-per-minute constant (~150 wpm; slower
   than the ~200 wpm `WORDS_PER_MINUTE` used for the reading-time estimate), not the reading-pace
   budget `assembly.py` uses.
2. **Generate script** — one Gemini call per length. System prompt: write a flowing,
   conversational script ("Good morning. Here's what you need to know today...") grounded in the
   selected stories' facts (summary / why it matters / what to watch as input), explicitly
   instructed not to read the written summaries verbatim — natural spoken transitions between
   stories, not a bullet-by-bullet recitation. For stories with `is_sensitive=True`, the prompt
   must carry over the same fact/perspective separation the written story enforces (e.g. "here's
   what's established, and here's how people disagree about it") rather than silently flattening
   it into a single narrated take — this is the same news-quality bar the text pipeline's
   `generate.py` prompt already applies, and audio shouldn't be a lower-rigor path around it.
3. **Synthesize audio** — send the script to Google Cloud TTS (Standard voice), get back MP3
   bytes.
4. **Upload to R2**, compute an estimated duration from script word count ÷ speaking rate (Google
   TTS doesn't return duration directly; reading it out of the MP3 file itself is unnecessary
   precision for a "~10 min" label), and write the `AudioBriefing` row.

**Failure handling**: the audio step must not be able to break the rest of the daily pipeline.
Wrap each length's generation in its own try/except, log and skip on failure (TTS quota issue,
R2 upload failure, etc.) rather than raising — a missing `AudioBriefing` row for a given
date/length just means the frontend has no audio to offer that day, which degrades gracefully
(see Frontend below), rather than blocking `ingest.py`/`cluster.py`/`generate.py` from
completing.

**New config** (`app/config.py` + `.env.example`): Google Cloud TTS credentials, and Cloudflare
R2 credentials (account ID, access key ID, secret access key, bucket name, public URL base).

**New GitHub Actions step** in `ingest.yml`: `python -m app.pipeline.audio`, with the above as
new repo secrets.

## API changes

`BriefingOut` (and the `/briefings/today` response) gains optional audio fields sourced from the
matching `AudioBriefing` row for the user's `briefing_length_minutes`:

```python
audio_url: str | None
audio_duration_seconds: int | None
```

`None` when no `AudioBriefing` row exists for today at that length (failed generation, or a
length the pipeline hasn't covered) — the frontend must handle this case, not assume audio is
always present.

## Frontend

Bring back `[Listen to Brief]` next to `[Start Reading]` on the home page (dropped in the recent
redesign since audio didn't exist yet at that point). Only rendered when `audio_url` is present
on the briefing response. Clicking it reveals an inline native `<audio controls>` element pointed
at `audio_url` — no custom player UI for MVP; the browser's built-in controls are sufficient and
match the project's "don't overengineer the MVP" instruction.

## Testing requirements

The repo currently has zero automated tests anywhere, which this feature doesn't fix wholesale,
but the new pipeline logic is worth covering given it's server-side business logic, not just
plumbing:

- Story-selection-for-audio word-count budgeting (given a set of stories and a target length,
  does it select a story set within the expected word-count range, and does it exclude
  personalization weighting correctly)
- Duration estimation math
- `BriefingOut` gracefully omitting audio fields when no `AudioBriefing` row exists

TTS/R2 calls themselves are integration points best smoke-tested manually (real API calls have
real cost and aren't worth mocking elaborately for an MVP), not unit tested.

## Explicitly out of scope for this feature

- Per-user personalized audio (rejected above)
- User-supplied API keys (rejected above)
- Custom audio player UI (waveform, playback speed control, etc.) — native browser controls only
- Audio for individual "Dive Deeper" story pages — only the full daily briefing gets audio

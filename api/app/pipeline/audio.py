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

"""Turns today's top StoryClusters into finished, user-facing Stories via
Gemini, grounded strictly in the clustered source articles.

Uses Gemini (rather than Anthropic, which has no free tier) so this stays
free at MVP volume. Costs stay trivial regardless of user count either way
because this runs once per cluster per day, shared across every user --
personalization happens later by selecting which already-generated stories
go into a given user's briefing, not by regenerating text per user.
"""

import datetime
import logging
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.config import settings
from app.db import SessionLocal
from app.interest_taxonomy import SUBCATEGORIES_BY_CATEGORY
from app.models import DailyDigest, RawArticle, Story, StoryCluster, StorySource

logger = logging.getLogger("generate")

MODEL = "gemini-flash-lite-latest"

# The Gemini free tier caps this model at 5 requests/minute -- pace calls
# to stay under that rather than burning retries on 429s. Not a concern for
# a scheduled batch job with no one waiting on it.
RATE_LIMIT_DELAY_SECONDS = 13
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 30

# A cap per category keeps any one flood of overlapping political/business
# coverage from crowding out every other category in the candidate pool
# Phase 5 personalization selects from -- tune once real usage exists.
MAX_STORIES_PER_CATEGORY = 8
MAX_STORIES_PER_DAY = 50

SYSTEM_PROMPT = """You are a factual news editor writing one story for a concise morning briefing.

Rules:
1. Use ONLY facts present in the provided source excerpts. Never invent names, numbers, quotes, or events not stated in the sources.
2. Write in a neutral, factual tone. Avoid sensational or clickbait language.
3. If the topic is politically contested or the sources reflect differing interpretations, separate established facts from perspective: set is_sensitive=true and fill perspectives with brief, attributed viewpoint summaries (e.g. "Democrats argue X", "The company maintains Y"). Otherwise set is_sensitive=false and perspectives=[].
4. summary is 2-4 sentences. why_it_matters and what_to_watch are each 1-2 sentences.
5. key_facts is 3-5 short, specific, verifiable facts or numbers drawn directly from the sources.
6. If a list of subcategory options is provided, pick the single one that best fits this story so it can be matched to readers who want that specific topic rather than the whole broad category. Only pick from the given list, exactly as spelled. If none clearly fit, set subcategory to null."""

DIGEST_SYSTEM_PROMPT = "You compress today's top news stories into extremely concise bullets for a 'today in 30 seconds' briefing section."


class StoryOutput(BaseModel):
    headline: str
    summary: str
    why_it_matters: str
    what_to_watch: str
    key_facts: list[str]
    is_sensitive: bool
    perspectives: list[str]
    subcategory: str | None = None


class DigestOutput(BaseModel):
    bullets: list[str]


def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _generate_with_rate_limit(
    client: genai.Client, contents: str, config: types.GenerateContentConfig
):
    """Calls generate_content, pacing for the free tier's 5 req/min cap and
    retrying with backoff on 429s rather than treating a rate limit as a
    hard failure for that story."""
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            time.sleep(RATE_LIMIT_DELAY_SECONDS)
            return response
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


def _build_cluster_prompt(category: str, articles: list[RawArticle]) -> str:
    lines = [f"Category: {category}"]
    subcats = SUBCATEGORIES_BY_CATEGORY.get(category, [])
    if subcats:
        options = ", ".join(slug for slug, _name in subcats)
        lines.append(f"Subcategory options: {options}")
    lines += ["", "Source articles covering this story:"]
    for a in articles:
        lines.append(f"- [{a.source.name}] {a.title}")
        if a.summary:
            lines.append(f"  {a.summary}")
    return "\n".join(lines)


def _select_clusters(db, today: datetime.date) -> list[StoryCluster]:
    clusters = list(
        db.execute(
            select(StoryCluster)
            .where(StoryCluster.cluster_date == today)
            .order_by(StoryCluster.importance_score.desc())
        ).scalars()
    )
    selected: list[StoryCluster] = []
    per_category: dict[str, int] = {}
    for cluster in clusters:
        if len(selected) >= MAX_STORIES_PER_DAY:
            break
        count = per_category.get(cluster.category, 0)
        if count >= MAX_STORIES_PER_CATEGORY:
            continue
        selected.append(cluster)
        per_category[cluster.category] = count + 1
    return selected


def _generate_story(client: genai.Client, db, cluster: StoryCluster) -> Story | None:
    articles = list(
        db.execute(
            select(RawArticle).where(RawArticle.cluster_id == cluster.id)
        ).scalars()
    )
    if not articles:
        return None

    prompt = _build_cluster_prompt(cluster.category, articles)
    response = _generate_with_rate_limit(
        client,
        prompt,
        types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=StoryOutput,
        ),
    )
    result: StoryOutput = response.parsed

    valid_subcats = {slug for slug, _name in SUBCATEGORIES_BY_CATEGORY.get(cluster.category, [])}
    subcategory = result.subcategory if result.subcategory in valid_subcats else None

    story = Story(
        cluster_id=cluster.id,
        date=cluster.cluster_date,
        category=cluster.category,
        subcategory=subcategory,
        headline=result.headline,
        summary=result.summary,
        why_it_matters=result.why_it_matters,
        what_to_watch=result.what_to_watch,
        key_facts=result.key_facts,
        is_sensitive=result.is_sensitive,
        perspectives=result.perspectives,
        importance_score=cluster.importance_score,
    )
    seen_urls = set()
    for a in articles:
        if a.url in seen_urls:
            continue
        seen_urls.add(a.url)
        story.sources.append(StorySource(name=a.source.name, url=a.url))
    return story


def _generate_digest(
    client: genai.Client, db, today: datetime.date, stories: list[Story]
) -> None:
    top = sorted(stories, key=lambda s: s.importance_score, reverse=True)[:3]
    if not top:
        return
    prompt = "\n".join(f"- {s.headline}: {s.summary}" for s in top)
    response = _generate_with_rate_limit(
        client,
        prompt,
        types.GenerateContentConfig(
            system_instruction=DIGEST_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=DigestOutput,
        ),
    )
    result: DigestOutput = response.parsed
    db.merge(DailyDigest(digest_date=today, bullets=result.bullets))


def run() -> None:
    db = SessionLocal()
    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()

        # Wipe today's stories so this run is idempotent (cascades to story_sources).
        db.execute(delete(Story).where(Story.date == today))
        db.commit()

        clusters = _select_clusters(db, today)
        if not clusters:
            logger.info("No clusters to generate stories for today")
            return

        client = _client()
        generated: list[Story] = []
        for cluster in clusters:
            try:
                story = _generate_story(client, db, cluster)
                if story:
                    db.add(story)
                    db.commit()
                    generated.append(story)
            except Exception:
                db.rollback()
                logger.exception("Failed to generate story for cluster %s", cluster.id)

        try:
            _generate_digest(client, db, today, generated)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to generate today's digest")

        logger.info(
            "Generated %d/%d stories for %s", len(generated), len(clusters), today
        )
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.db import SessionLocal
from app.models import RawArticle, Source
from app.pipeline.guardian import fetch_guardian_articles
from app.pipeline.nyt import fetch_nyt_articles
from app.pipeline.rss import fetch_rss_source
from app.pipeline.types import NormalizedArticle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

# Some general-interest RSS feeds (CBS Sports in particular) mix gambling/
# betting-promo content in with real news. Not appropriate for a briefing
# product -- filter it out at ingestion rather than letting it compete for
# space in the story pool.
SPAM_KEYWORDS = [
    "promo code",
    "bonus bet",
    "betting site",
    "betting guide",
    "betting line",
    "sportsbook",
    "free bet",
    "how to bet",
    " odds:",
    " odds,",
]


def _is_spam(article: NormalizedArticle) -> bool:
    title = article.title.lower()
    return any(keyword in title for keyword in SPAM_KEYWORDS)


def _fetch(source: Source) -> list[NormalizedArticle]:
    if source.kind == "rss":
        return fetch_rss_source(source)
    if source.kind == "api_guardian":
        if not settings.guardian_api_key:
            logger.info("Skipping %s: GUARDIAN_API_KEY not set", source.slug)
            return []
        return fetch_guardian_articles(settings.guardian_api_key)
    if source.kind == "api_nyt":
        if not settings.nyt_api_key:
            logger.info("Skipping %s: NYT_API_KEY not set", source.slug)
            return []
        return fetch_nyt_articles(settings.nyt_api_key)
    raise ValueError(f"Unknown source kind: {source.kind}")


def _upsert_articles(db, source: Source, articles: list[NormalizedArticle]) -> int:
    if not articles:
        return 0
    rows = [
        {
            "source_id": source.id,
            "external_id": a.external_id,
            "url": a.url,
            "title": a.title,
            "summary": a.summary,
            "published_at": a.published_at,
            "raw_payload": a.raw_payload,
        }
        for a in articles
    ]
    stmt = pg_insert(RawArticle).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=[RawArticle.source_id, RawArticle.external_id]
    ).returning(RawArticle.id)
    result = db.execute(stmt)
    inserted = len(result.fetchall())
    db.commit()
    return inserted


def run() -> None:
    db = SessionLocal()
    try:
        sources = db.execute(
            select(Source).where(Source.active.is_(True))
        ).scalars().all()

        total_new = 0
        for source in sources:
            try:
                articles = [a for a in _fetch(source) if not _is_spam(a)]
                new_count = _upsert_articles(db, source, articles)
                total_new += new_count
                logger.info(
                    "%s: fetched %d, inserted %d new",
                    source.slug,
                    len(articles),
                    new_count,
                )
            except Exception:
                logger.exception("Failed to ingest source %s", source.slug)

        logger.info("Ingestion complete: %d new articles across %d sources", total_new, len(sources))
    finally:
        db.close()


if __name__ == "__main__":
    run()

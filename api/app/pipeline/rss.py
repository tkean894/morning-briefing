import calendar
import datetime

import feedparser
import httpx

from app.models import Source
from app.pipeline.text_utils import clean_summary
from app.pipeline.types import NormalizedArticle

USER_AGENT = "MorningBriefsBot/0.1 (+https://github.com/tkean894/morning-briefing)"


def _to_datetime(struct_time) -> datetime.datetime | None:
    if struct_time is None:
        return None
    return datetime.datetime.fromtimestamp(
        calendar.timegm(struct_time), tz=datetime.timezone.utc
    )


def fetch_rss_source(source: Source) -> list[NormalizedArticle]:
    response = httpx.get(
        source.feed_url,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
        follow_redirects=True,
    )
    response.raise_for_status()
    parsed = feedparser.parse(response.content)

    articles = []
    for entry in parsed.entries:
        url = entry.get("link")
        if not url:
            continue
        external_id = entry.get("id") or url
        articles.append(
            NormalizedArticle(
                external_id=external_id,
                url=url,
                title=entry.get("title", "").strip(),
                summary=clean_summary(entry.get("summary")),
                published_at=_to_datetime(entry.get("published_parsed")),
                raw_payload={
                    "title": entry.get("title"),
                    "link": url,
                    "summary": entry.get("summary"),
                    "published": entry.get("published"),
                },
            )
        )
    return articles

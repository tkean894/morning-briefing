import datetime

import httpx

from app.pipeline.text_utils import clean_summary
from app.pipeline.types import NormalizedArticle

API_URL = "https://api.nytimes.com/svc/topstories/v2/home.json"


def fetch_nyt_articles(api_key: str) -> list[NormalizedArticle]:
    response = httpx.get(API_URL, params={"api-key": api_key}, timeout=15)
    response.raise_for_status()
    results = response.json()["results"]

    articles = []
    for item in results:
        url = item.get("url")
        if not url:
            continue
        published_at = None
        if item.get("published_date"):
            published_at = datetime.datetime.fromisoformat(item["published_date"])
        articles.append(
            NormalizedArticle(
                external_id=item.get("uri", url),
                url=url,
                title=item.get("title", "").strip(),
                summary=clean_summary(item.get("abstract")),
                published_at=published_at,
                raw_payload=item,
            )
        )
    return articles

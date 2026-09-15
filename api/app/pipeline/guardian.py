import datetime

import httpx

from app.pipeline.text_utils import clean_summary
from app.pipeline.types import NormalizedArticle

API_URL = "https://content.guardianapis.com/search"


def fetch_guardian_articles(api_key: str) -> list[NormalizedArticle]:
    response = httpx.get(
        API_URL,
        params={
            "api-key": api_key,
            "order-by": "newest",
            "show-fields": "trailText",
            "page-size": 50,
        },
        timeout=15,
    )
    response.raise_for_status()
    results = response.json()["response"]["results"]

    articles = []
    for item in results:
        published_at = None
        if item.get("webPublicationDate"):
            published_at = datetime.datetime.fromisoformat(
                item["webPublicationDate"].replace("Z", "+00:00")
            )
        articles.append(
            NormalizedArticle(
                external_id=item["id"],
                url=item["webUrl"],
                title=item.get("webTitle", "").strip(),
                summary=clean_summary(item.get("fields", {}).get("trailText")),
                published_at=published_at,
                raw_payload=item,
            )
        )
    return articles

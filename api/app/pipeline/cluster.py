"""Groups same-event articles together and scores each group's importance.

Uses TF-IDF + cosine similarity over each article's title+summary rather
than an embeddings API -- at MVP scale (tens to low hundreds of articles/
day) this needs no external service and costs nothing, and is easy enough
to swap for real embeddings later if similarity quality turns out to need
it. Runs fresh each day: any existing clusters for today's date are wiped
and recomputed, so re-running the pipeline is safe and idempotent.
"""

import collections
import datetime
import logging

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import delete, select, update

from app.db import SessionLocal
from app.models import RawArticle, StoryCluster

logger = logging.getLogger("cluster")

# Average-linkage clustering: two articles land in the same story only if
# the *whole* group stays this similar on average, not just one pairwise
# link -- naive single-link/union-find chaining was merging dozens of
# unrelated politics stories together through shared vocabulary (Trump, AI,
# Supreme Court) that didn't actually mean they were the same event. A
# first-pass heuristic -- tune once more real clustering output has been
# eyeballed against actual daily news volume.
SIMILARITY_THRESHOLD = 0.3
WINDOW_HOURS = 36
CREDIBILITY_SCORE = {1: 3, 2: 2, 3: 1}


def _compute_importance(members: list[RawArticle]) -> float:
    distinct_sources = len({a.source_id for a in members})
    min_tier = min(a.source.credibility_tier for a in members)
    credibility_score = CREDIBILITY_SCORE.get(min_tier, 1)

    published_dates = [a.published_at for a in members if a.published_at]
    if published_dates:
        age_hours = (
            datetime.datetime.now(datetime.timezone.utc) - max(published_dates)
        ).total_seconds() / 3600
        recency_score = max(0.0, 1 - age_hours / 24)
    else:
        recency_score = 0.3

    return distinct_sources * 10 + credibility_score * 5 + recency_score * 10


def _majority_category(members: list[RawArticle]) -> str:
    counts = collections.Counter(a.source.category for a in members)
    return counts.most_common(1)[0][0]


def run(window_hours: int = WINDOW_HOURS) -> None:
    db = SessionLocal()
    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()

        # Wipe today's clusters so this run is idempotent.
        old_cluster_ids = [
            row[0]
            for row in db.execute(
                select(StoryCluster.id).where(StoryCluster.cluster_date == today)
            )
        ]
        if old_cluster_ids:
            db.execute(
                update(RawArticle)
                .where(RawArticle.cluster_id.in_(old_cluster_ids))
                .values(cluster_id=None, cluster_similarity=None)
            )
            db.execute(
                delete(StoryCluster).where(StoryCluster.id.in_(old_cluster_ids))
            )
            db.commit()

        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=window_hours
        )
        articles = list(
            db.execute(
                select(RawArticle).where(RawArticle.published_at >= cutoff)
            ).scalars()
        )
        if not articles:
            logger.info("No articles in the last %dh to cluster", window_hours)
            return

        texts = [f"{a.title} {a.summary or ''}" for a in articles]
        vectorizer = TfidfVectorizer(
            stop_words="english", max_features=5000, ngram_range=(1, 2)
        )
        matrix = vectorizer.fit_transform(texts)
        similarity = cosine_similarity(matrix)

        distance = np.clip(1 - similarity, 0, None)
        np.fill_diagonal(distance, 0)

        if len(articles) == 1:
            labels = [0]
        else:
            clustering = AgglomerativeClustering(
                metric="precomputed",
                linkage="complete",
                distance_threshold=1 - SIMILARITY_THRESHOLD,
                n_clusters=None,
            )
            labels = clustering.fit_predict(distance)

        groups: dict[int, list[int]] = collections.defaultdict(list)
        for i, label in enumerate(labels):
            groups[label].append(i)

        for indices in groups.values():
            members = [articles[i] for i in indices]
            cluster = StoryCluster(
                cluster_date=today,
                category=_majority_category(members),
                importance_score=_compute_importance(members),
            )
            db.add(cluster)
            db.flush()
            for i, article in zip(indices, members):
                article.cluster_id = cluster.id
                if len(indices) == 1:
                    article.cluster_similarity = 1.0
                else:
                    others = [k for k in indices if k != i]
                    article.cluster_similarity = max(
                        similarity[i, k] for k in others
                    )
        db.commit()

        multi_source = sum(1 for g in groups.values() if len(g) > 1)
        logger.info(
            "Clustered %d articles into %d stories (%d multi-source)",
            len(articles),
            len(groups),
            multi_source,
        )
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()

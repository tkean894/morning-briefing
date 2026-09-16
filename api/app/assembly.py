"""Turns today's shared pool of Stories into one user's personalized,
length-appropriate briefing. Pure Python, no LLM/network calls -- cheap
enough to run fresh on every request rather than persisting a snapshot,
so a preference change is reflected immediately rather than waiting for
a nightly regeneration.
"""

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.interest_taxonomy import TAXONOMY
from app.models import Story, User, UserInterest

CATEGORY_ORDER = [c["slug"] for c in TAXONOMY]

# How many of the day's single most important stories every user sees
# regardless of their interests -- the "still see the huge national story"
# guarantee from the product spec.
MUST_INCLUDE_COUNT = 2

# Multiplier applied to a story's importance score when its category isn't
# one of the user's selected interests. Not zero: a big enough story can
# still surface, it's just deprioritized rather than hidden outright.
UNSELECTED_CATEGORY_WEIGHT = 0.3

WORDS_PER_MINUTE = 200
MIN_STORIES = 3
MAX_STORIES = 20

# Without this, a user who selects a category with many routine stories in
# the pool (sports is the common case) can end up with a briefing that's
# mostly one category, crowding out their other interests entirely.
MAX_PER_CATEGORY_IN_BRIEFING = 4


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


def _user_category_weights(db: Session, user: User) -> dict[str, float]:
    """Maps a broad category slug -> the user's affinity weight for it, for
    every broad interest the user selected (directly or via a specific
    sub-interest under it)."""
    rows = db.execute(
        select(UserInterest).where(UserInterest.user_id == user.id)
    ).scalars()
    weights: dict[str, float] = {}
    for ui in rows:
        interest = ui.interest
        category_slug = interest.parent.slug if interest.parent else interest.slug
        weights[category_slug] = max(weights.get(category_slug, 0), ui.affinity_weight)
    return weights


def assemble_briefing(db: Session, user: User, target_length_minutes: int) -> dict:
    today = datetime.datetime.now(datetime.timezone.utc).date()
    all_stories = list(
        db.execute(
            select(Story)
            .where(Story.date == today)
            .order_by(Story.importance_score.desc())
        ).scalars()
    )

    if not all_stories:
        return {"date": today, "story_count": 0, "stories": []}

    category_weights = _user_category_weights(db, user)

    must_include = all_stories[:MUST_INCLUDE_COUNT]
    must_include_ids = {s.id for s in must_include}
    candidates = [s for s in all_stories if s.id not in must_include_ids]

    def combined_score(story: Story) -> float:
        weight = category_weights.get(story.category, UNSELECTED_CATEGORY_WEIGHT)
        return story.importance_score * weight

    candidates.sort(key=combined_score, reverse=True)

    selected: list[tuple[Story, str]] = [(s, "must_include") for s in must_include]
    total_minutes = sum(_story_word_count(s) / WORDS_PER_MINUTE for s in must_include)
    category_counts: dict[str, int] = {}
    for s in must_include:
        category_counts[s.category] = category_counts.get(s.category, 0) + 1

    for story in candidates:
        if len(selected) >= MAX_STORIES:
            break
        if len(selected) >= MIN_STORIES and total_minutes >= target_length_minutes:
            break
        if category_counts.get(story.category, 0) >= MAX_PER_CATEGORY_IN_BRIEFING:
            continue
        selected.append((story, "personalized"))
        total_minutes += _story_word_count(story) / WORDS_PER_MINUTE
        category_counts[story.category] = category_counts.get(story.category, 0) + 1

    selected.sort(
        key=lambda pair: (
            CATEGORY_ORDER.index(pair[0].category)
            if pair[0].category in CATEGORY_ORDER
            else len(CATEGORY_ORDER),
            -pair[0].importance_score,
        )
    )

    return {
        "date": today,
        "story_count": len(selected),
        "estimated_read_minutes": round(total_minutes, 1),
        "stories": selected,
    }

import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assembly import assemble_briefing
from app.auth import get_current_user
from app.db import get_db
from app.models import DailyDigest, User, UserPreference
from app.schemas import BriefingOut, BriefingStoryOut, DigestOut

router = APIRouter()


@router.get("/briefings/today", response_model=BriefingOut)
def get_todays_briefing(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BriefingOut:
    prefs = user.preferences or UserPreference(briefing_length_minutes=10)
    result = assemble_briefing(db, user, prefs.briefing_length_minutes)

    digest_out = None
    if result["story_count"] > 0:
        today = result["date"] if isinstance(result["date"], datetime.date) else None
        digest_row = db.get(DailyDigest, today) if today else None
        if digest_row:
            digest_out = DigestOut(bullets=digest_row.bullets)

    stories_out = [
        BriefingStoryOut(
            id=story.id,
            category=story.category,
            headline=story.headline,
            summary=story.summary,
            why_it_matters=story.why_it_matters,
            what_to_watch=story.what_to_watch,
            key_facts=story.key_facts,
            is_sensitive=story.is_sensitive,
            perspectives=story.perspectives,
            sources=story.sources,
            inclusion_reason=reason,
        )
        for story, reason in result["stories"]
    ]

    return BriefingOut(
        date=result["date"],
        briefing_length_minutes=prefs.briefing_length_minutes,
        story_count=result["story_count"],
        estimated_read_minutes=result.get("estimated_read_minutes", 0.0),
        digest=digest_out,
        stories=stories_out,
    )

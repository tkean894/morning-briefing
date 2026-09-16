from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Story, User
from app.schemas import RelatedStoryOut, StoryDetailOut

router = APIRouter()


@router.get("/stories/{story_id}", response_model=StoryDetailOut)
def get_story(
    story_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StoryDetailOut:
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")

    related = list(
        db.execute(
            select(Story)
            .where(
                Story.date == story.date,
                Story.category == story.category,
                Story.id != story.id,
            )
            .order_by(Story.importance_score.desc())
            .limit(3)
        ).scalars()
    )

    return StoryDetailOut(
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
        related=[RelatedStoryOut.model_validate(r) for r in related],
    )

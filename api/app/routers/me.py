import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User, UserInterest, UserPreference
from app.schemas import MeOut, PreferencesIn

router = APIRouter()


@router.get("/me", response_model=MeOut)
def get_me(user: User = Depends(get_current_user)) -> MeOut:
    prefs = user.preferences
    return MeOut(
        onboarding_completed=bool(prefs and prefs.onboarding_completed_at),
        briefing_length_minutes=prefs.briefing_length_minutes if prefs else 10,
        audio_enabled=prefs.audio_enabled if prefs else True,
        interest_ids=[ui.interest_id for ui in user.interests],
    )


@router.put("/preferences", response_model=MeOut)
def put_preferences(
    body: PreferencesIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeOut:
    db.query(UserInterest).filter(UserInterest.user_id == user.id).delete()
    for interest_id in set(body.interest_ids):
        db.add(UserInterest(user_id=user.id, interest_id=interest_id))

    prefs = db.get(UserPreference, user.id)
    if prefs is None:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
    prefs.briefing_length_minutes = body.briefing_length_minutes
    prefs.audio_enabled = body.audio_enabled
    if prefs.onboarding_completed_at is None:
        prefs.onboarding_completed_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()

    return MeOut(
        onboarding_completed=True,
        briefing_length_minutes=prefs.briefing_length_minutes,
        audio_enabled=prefs.audio_enabled,
        interest_ids=list(body.interest_ids),
    )

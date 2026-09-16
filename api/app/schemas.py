import datetime
from typing import Literal

from pydantic import BaseModel

BriefingLength = Literal[5, 10, 15, 20]


class InterestOut(BaseModel):
    id: int
    slug: str
    name: str
    children: list["InterestOut"] = []

    model_config = {"from_attributes": True}


class MeOut(BaseModel):
    onboarding_completed: bool
    briefing_length_minutes: BriefingLength
    audio_enabled: bool
    interest_ids: list[int]


class PreferencesIn(BaseModel):
    interest_ids: list[int]
    briefing_length_minutes: BriefingLength
    audio_enabled: bool = True


class StorySourceOut(BaseModel):
    name: str
    url: str

    model_config = {"from_attributes": True}


class BriefingStoryOut(BaseModel):
    id: int
    category: str
    headline: str
    summary: str
    why_it_matters: str
    what_to_watch: str
    key_facts: list[str]
    is_sensitive: bool
    perspectives: list[str]
    sources: list[StorySourceOut]
    inclusion_reason: Literal["must_include", "personalized"]

    model_config = {"from_attributes": True}


class DigestOut(BaseModel):
    bullets: list[str]


class BriefingOut(BaseModel):
    date: datetime.date
    briefing_length_minutes: BriefingLength
    story_count: int
    estimated_read_minutes: float = 0.0
    digest: DigestOut | None = None
    stories: list[BriefingStoryOut] = []

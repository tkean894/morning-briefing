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

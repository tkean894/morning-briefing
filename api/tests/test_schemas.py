import datetime

from app.schemas import BriefingOut


def test_briefing_out_defaults_audio_fields_to_none():
    briefing = BriefingOut(
        date=datetime.date(2026, 9, 16),
        briefing_length_minutes=10,
        story_count=0,
    )

    assert briefing.audio_url is None
    assert briefing.audio_duration_seconds is None

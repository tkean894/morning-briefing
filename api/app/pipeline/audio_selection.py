"""Pure story-selection and duration-estimation logic for the shared daily
audio briefing. Kept separate from app.pipeline.audio's Gemini/TTS/R2 I/O so
it can be unit tested without any network calls.

Unlike app.assembly (which personalizes per user), this selects the same
story set for everyone, mirroring how DailyDigest is shared rather than
personalized. See docs/superpowers/specs/2026-09-16-audio-briefing-design.md.
"""

from app.models import Story

# Spoken delivery is slower than the silent-reading pace app.assembly uses
# (200 wpm) for its read-time estimate.
AUDIO_WORDS_PER_MINUTE = 150

# How many of the day's single most important stories always make the audio
# briefing regardless of category/length budget, mirroring
# app.assembly.MUST_INCLUDE_COUNT.
AUDIO_MUST_INCLUDE_COUNT = 2

# Caps any one category (sports is the common flood case) from crowding out
# the rest of the briefing, mirroring app.assembly.MAX_PER_CATEGORY_IN_BRIEFING.
AUDIO_MAX_PER_CATEGORY = 4


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


def select_stories_for_audio(
    stories: list[Story], target_length_minutes: int
) -> list[Story]:
    """Selects a shared (non-personalized) story set for the audio
    briefing, budgeted to target_length_minutes at spoken pace. `stories`
    must already be sorted by importance_score descending."""
    if not stories:
        return []

    must_include = stories[:AUDIO_MUST_INCLUDE_COUNT]
    candidates = stories[AUDIO_MUST_INCLUDE_COUNT:]

    selected = list(must_include)
    total_minutes = sum(
        _story_word_count(s) / AUDIO_WORDS_PER_MINUTE for s in must_include
    )
    category_counts: dict[str, int] = {}
    for s in must_include:
        category_counts[s.category] = category_counts.get(s.category, 0) + 1

    for story in candidates:
        if total_minutes >= target_length_minutes:
            break
        if category_counts.get(story.category, 0) >= AUDIO_MAX_PER_CATEGORY:
            continue
        selected.append(story)
        total_minutes += _story_word_count(story) / AUDIO_WORDS_PER_MINUTE
        category_counts[story.category] = category_counts.get(story.category, 0) + 1

    return selected


def estimate_duration_seconds(stories: list[Story]) -> int:
    """Estimates spoken duration from selected stories' word counts. Used
    because Google Cloud TTS doesn't return duration, and reading it from
    the generated MP3 is unnecessary precision for a "~10 min" label."""
    total_words = sum(_story_word_count(s) for s in stories)
    minutes = total_words / AUDIO_WORDS_PER_MINUTE
    return round(minutes * 60)

from app.models import Story
from app.pipeline.audio_selection import (
    AUDIO_MAX_PER_CATEGORY,
    AUDIO_MUST_INCLUDE_COUNT,
    AUDIO_WORDS_PER_MINUTE,
    estimate_duration_seconds,
    select_stories_for_audio,
)


def _make_story(category: str, importance_score: float, word_count: int) -> Story:
    words = " ".join(["word"] * word_count)
    return Story(
        category=category,
        summary=words,
        why_it_matters="",
        what_to_watch="",
        key_facts=[],
        importance_score=importance_score,
    )


def test_select_stories_for_audio_respects_length_budget():
    categories = ["technology", "business", "markets", "sports"]
    stories = [
        _make_story(categories[i % len(categories)], importance_score=100 - i, word_count=AUDIO_WORDS_PER_MINUTE)
        for i in range(10)
    ]

    selected = select_stories_for_audio(stories, target_length_minutes=5)

    assert len(selected) == 5
    assert [s.importance_score for s in selected] == [100, 99, 98, 97, 96]


def test_select_stories_for_audio_always_includes_top_must_include_stories():
    stories = [
        _make_story("politics", importance_score=1000, word_count=AUDIO_WORDS_PER_MINUTE),
        _make_story("world-news", importance_score=900, word_count=AUDIO_WORDS_PER_MINUTE),
    ] + [
        _make_story("sports", importance_score=10 - i, word_count=AUDIO_WORDS_PER_MINUTE)
        for i in range(10)
    ]

    selected = select_stories_for_audio(stories, target_length_minutes=5)

    assert selected[0].importance_score == 1000
    assert selected[1].importance_score == 900


def test_select_stories_for_audio_caps_stories_per_category():
    stories = [
        _make_story("sports", importance_score=100 - i, word_count=AUDIO_WORDS_PER_MINUTE)
        for i in range(10)
    ]

    selected = select_stories_for_audio(stories, target_length_minutes=20)

    sports_count = sum(1 for s in selected if s.category == "sports")
    assert sports_count == AUDIO_MAX_PER_CATEGORY


def test_select_stories_for_audio_empty_input_returns_empty():
    assert select_stories_for_audio([], target_length_minutes=10) == []


def test_estimate_duration_seconds_matches_word_count_at_spoken_pace():
    stories = [_make_story("technology", importance_score=1, word_count=AUDIO_WORDS_PER_MINUTE)]

    assert estimate_duration_seconds(stories) == 60


def test_estimate_duration_seconds_empty_input_is_zero():
    assert estimate_duration_seconds([]) == 0

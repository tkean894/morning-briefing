import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

MAX_SUMMARY_LENGTH = 400


def clean_summary(raw: str | None, max_length: int = MAX_SUMMARY_LENGTH) -> str | None:
    """Strip HTML and truncate to a short snippet.

    Some feeds (Axios in particular) put the entire article's full HTML in
    the RSS summary field rather than a short description. Beyond the
    licensing risk of storing/using full article text, that shared
    boilerplate (repeated section headers, link markup) was polluting
    clustering similarity scores across otherwise-unrelated stories.
    """
    if not raw:
        return None
    text = _TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if not text:
        return None
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated + "..."

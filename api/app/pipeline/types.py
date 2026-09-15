import datetime
from dataclasses import dataclass, field


@dataclass
class NormalizedArticle:
    external_id: str
    url: str
    title: str
    summary: str | None
    published_at: datetime.datetime | None
    raw_payload: dict = field(default_factory=dict)

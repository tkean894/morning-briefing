import datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    interests: Mapped[list["UserInterest"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Interest(Base):
    """Taxonomy of broad interests (parent_id is null) and specific interests
    (parent_id points at a broad interest), e.g. Markets -> Stocks."""

    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("interests.id"))
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    sort_order: Mapped[int] = mapped_column(default=0)

    children: Mapped[list["Interest"]] = relationship(
        back_populates="parent", order_by="Interest.sort_order"
    )
    parent: Mapped["Interest | None"] = relationship(
        back_populates="children", remote_side=[id]
    )


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "interest_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    interest_id: Mapped[int] = mapped_column(ForeignKey("interests.id"))
    affinity_weight: Mapped[float] = mapped_column(default=1.0)

    user: Mapped["User"] = relationship(back_populates="interests")
    interest: Mapped["Interest"] = relationship()


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    kind: Mapped[str]  # "rss" | "api_guardian" | "api_nyt"
    category: Mapped[str]  # loosely matches an interests.slug broad category
    feed_url: Mapped[str | None]
    credibility_tier: Mapped[int] = mapped_column(default=2)
    active: Mapped[bool] = mapped_column(default=True)


class StoryCluster(Base):
    """A group of raw_articles from different sources judged to cover the
    same real-world event, produced by app.pipeline.cluster."""

    __tablename__ = "story_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_date: Mapped[datetime.date] = mapped_column(Date, index=True)
    category: Mapped[str]
    importance_score: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    articles: Mapped[list["RawArticle"]] = relationship(back_populates="cluster")


class RawArticle(Base):
    __tablename__ = "raw_articles"
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    external_id: Mapped[str]
    url: Mapped[str]
    title: Mapped[str]
    summary: Mapped[str | None]
    published_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("story_clusters.id"))
    cluster_similarity: Mapped[float | None]

    source: Mapped["Source"] = relationship()
    cluster: Mapped["StoryCluster | None"] = relationship(back_populates="articles")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    briefing_length_minutes: Mapped[int] = mapped_column(default=10)
    audio_enabled: Mapped[bool] = mapped_column(default=True)
    onboarding_completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    user: Mapped["User"] = relationship(back_populates="preferences")

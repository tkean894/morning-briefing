import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    clerk_user_id: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
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


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    briefing_length_minutes: Mapped[int] = mapped_column(default=10)
    audio_enabled: Mapped[bool] = mapped_column(default=True)
    onboarding_completed_at: Mapped[datetime.datetime | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="preferences")

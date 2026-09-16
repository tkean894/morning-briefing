"""add cbs sports source

Revision ID: b6373a3d72c8
Revises: 9cae518c5914
Create Date: 2026-09-15 22:56:18.057170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.pipeline.sources_seed import SOURCES

# revision identifiers, used by Alembic.
revision: str = 'b6373a3d72c8'
down_revision: Union[str, Sequence[str], None] = '9cae518c5914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

sources_table = sa.table(
    "sources",
    sa.column("slug", sa.String),
    sa.column("name", sa.String),
    sa.column("kind", sa.String),
    sa.column("category", sa.String),
    sa.column("feed_url", sa.String),
    sa.column("credibility_tier", sa.Integer),
    sa.column("active", sa.Boolean),
)

NEW_SLUG = "cbs-sports"


def upgrade() -> None:
    source = next(s for s in SOURCES if s["slug"] == NEW_SLUG)
    op.get_bind().execute(
        sources_table.insert().values(
            slug=source["slug"],
            name=source["name"],
            kind=source["kind"],
            category=source["category"],
            feed_url=source["feed_url"],
            credibility_tier=source["credibility_tier"],
            active=True,
        )
    )


def downgrade() -> None:
    op.execute(sources_table.delete().where(sources_table.c.slug == NEW_SLUG))

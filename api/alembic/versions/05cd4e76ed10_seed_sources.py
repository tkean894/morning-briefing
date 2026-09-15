"""seed sources

Revision ID: 05cd4e76ed10
Revises: 5d8a5ae9ac91
Create Date: 2026-09-15 13:44:06.996433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.pipeline.sources_seed import SOURCES

# revision identifiers, used by Alembic.
revision: str = '05cd4e76ed10'
down_revision: Union[str, Sequence[str], None] = '5d8a5ae9ac91'
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


def upgrade() -> None:
    conn = op.get_bind()
    for source in SOURCES:
        conn.execute(
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
    op.execute(sources_table.delete())

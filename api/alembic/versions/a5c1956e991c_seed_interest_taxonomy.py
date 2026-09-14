"""seed interest taxonomy

Revision ID: a5c1956e991c
Revises: 92db17de84cb
Create Date: 2026-09-14 13:53:29.346552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.interest_taxonomy import TAXONOMY

# revision identifiers, used by Alembic.
revision: str = 'a5c1956e991c'
down_revision: Union[str, Sequence[str], None] = '92db17de84cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

interests_table = sa.table(
    "interests",
    sa.column("id", sa.Integer),
    sa.column("parent_id", sa.Integer),
    sa.column("slug", sa.String),
    sa.column("name", sa.String),
    sa.column("sort_order", sa.Integer),
)


def upgrade() -> None:
    conn = op.get_bind()
    for parent_order, parent in enumerate(TAXONOMY):
        result = conn.execute(
            interests_table.insert().values(
                parent_id=None,
                slug=parent["slug"],
                name=parent["name"],
                sort_order=parent_order,
            ).returning(interests_table.c.id)
        )
        parent_id = result.scalar_one()
        for child_order, child in enumerate(parent.get("children", [])):
            conn.execute(
                interests_table.insert().values(
                    parent_id=parent_id,
                    slug=child["slug"],
                    name=child["name"],
                    sort_order=child_order,
                )
            )


def downgrade() -> None:
    op.execute(interests_table.delete())

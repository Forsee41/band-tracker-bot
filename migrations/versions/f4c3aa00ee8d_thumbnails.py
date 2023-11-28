"""thumbnails

Revision ID: f4c3aa00ee8d
Revises: 34167ecf3940
Create Date: 2023-11-28 14:23:06.445338

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4c3aa00ee8d"
down_revision = "34167ecf3940"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artist", sa.Column("thumbnail", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("artist", "thumbnail")

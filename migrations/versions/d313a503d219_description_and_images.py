"""description and images

Revision ID: d313a503d219
Revises: f4c3aa00ee8d
Create Date: 2023-12-09 22:47:57.423774

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d313a503d219"
down_revision = "f4c3aa00ee8d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("artist", sa.Column("description", sa.String(), nullable=True))

    op.add_column("event", sa.Column("thumbnail", sa.String(), nullable=True))

    op.add_column("artist_socials", sa.Column("wiki", sa.String(), nullable=True))


def downgrade():
    op.drop_column("artist", "description")

    op.drop_column("event", "thumbnail")

    op.drop_column("artist_socials", "wiki")

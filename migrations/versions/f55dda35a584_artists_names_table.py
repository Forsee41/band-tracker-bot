"""artists names table

Revision ID: f55dda35a584
Revises: d313a503d219
Create Date: 2023-12-15 13:39:52.808024

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f55dda35a584"
down_revision = "d313a503d219"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artist_names",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("artist_names")

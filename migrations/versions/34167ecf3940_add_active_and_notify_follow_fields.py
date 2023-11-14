"""add active and notify follow fields

Revision ID: 34167ecf3940
Revises: 46b3ad61f509
Create Date: 2023-11-14 22:18:17.481974

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "34167ecf3940"
down_revision = "46b3ad61f509"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("subscription")
    op.add_column("follow", sa.Column("notify", sa.Boolean(), nullable=False))
    op.add_column("follow", sa.Column("active", sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("follow", "active")
    op.drop_column("follow", "notify")
    op.create_table(
        "subscription",
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("artist_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["artist_id"],
            ["artist.id"],
            name="subscription_artist_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="subscription_user_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "artist_id", name="subscription_pkey"),
    )
    # ### end Alembic commands ###
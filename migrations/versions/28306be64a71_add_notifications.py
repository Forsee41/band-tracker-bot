"""add notifications

Revision ID: 28306be64a71
Revises: 82c72be5643a
Create Date: 2024-02-03 12:59:41.970617

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "28306be64a71"
down_revision = "82c72be5643a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "event_user",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["event.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="unique_event_user"),
    )
    op.create_index(
        op.f("ix_event_user_event_id"), "event_user", ["event_id"], unique=False
    )
    op.create_index(
        op.f("ix_event_user_user_id"), "event_user", ["user_id"], unique=False
    )
    op.create_table(
        "notification",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("event_user_id", sa.UUID(), nullable=False),
        sa.Column("artist_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["artist_id"], ["artist.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["event_user_id"], ["event_user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artist_id", "event_user_id", name="unique_notification"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("notification")
    op.drop_index(op.f("ix_event_user_user_id"), table_name="event_user")
    op.drop_index(op.f("ix_event_user_event_id"), table_name="event_user")
    op.drop_table("event_user")
    # ### end Alembic commands ###
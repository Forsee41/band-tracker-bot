"""add messages

Revision ID: cb4fb4355c24
Revises: f4c3aa00ee8d
Create Date: 2023-12-10 16:00:53.377241

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cb4fb4355c24"
down_revision = "f4c3aa00ee8d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "message",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tg_message_id", sa.Integer(), nullable=False),
        sa.Column(
            "message_type",
            sa.Enum(
                "TEST",
                "NOTIFICATION",
                "HELP",
                "START",
                "MENU",
                "SETTINGS",
                "AMP",
                "FOLLOW_CONFIG",
                "EMP",
                "EVENT_ARTISTS",
                "FOLLOWS",
                "ARTIST_EVENT",
                "ARTIST_EVENT_START",
                "ARTIST_EVENT_END",
                "GLOBAL_EVENT",
                "GLOBAL_EVENT_START",
                "GLOBAL_EVENT_END",
                name="messagetype",
            ),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tg_message_id"),
    )
    op.create_index(op.f("ix_message_active"), "message", ["active"], unique=False)
    op.create_index(
        op.f("ix_message_message_type"), "message", ["message_type"], unique=False
    )
    op.create_index(op.f("ix_message_user_id"), "message", ["user_id"], unique=True)
    op.drop_constraint("user_tg_id_unique", "user", type_="unique")
    op.create_index(op.f("ix_user_tg_id"), "user", ["tg_id"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_user_tg_id"), table_name="user")
    op.create_unique_constraint("user_tg_id_unique", "user", ["tg_id"])
    op.drop_index(op.f("ix_message_user_id"), table_name="message")
    op.drop_index(op.f("ix_message_message_type"), table_name="message")
    op.drop_index(op.f("ix_message_active"), table_name="message")
    op.drop_table("message")
    # ### end Alembic commands ###

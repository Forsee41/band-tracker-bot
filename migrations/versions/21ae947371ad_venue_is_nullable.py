"""venue_is_nullable

Revision ID: 21ae947371ad
Revises: b7cc6df64cde
Create Date: 2023-08-20 19:00:36.513900

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "21ae947371ad"
down_revision = "b7cc6df64cde"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("event", "venue", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("event", "venue_city", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("event", "venue_country", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "event", "venue_country", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column("event", "venue_city", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("event", "venue", existing_type=sa.VARCHAR(), nullable=False)
    # ### end Alembic commands ###

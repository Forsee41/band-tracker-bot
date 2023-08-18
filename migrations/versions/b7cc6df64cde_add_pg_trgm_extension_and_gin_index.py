"""add pg_trgm extension and GIN index

Revision ID: b7cc6df64cde
Revises: 82cd26ecbdef
Create Date: 2023-08-16 20:20:17.886533

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7cc6df64cde"
down_revision = "82cd26ecbdef"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX artist_alias_gin_trgm_idx ON "
        "artist_alias USING gin (alias gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX artist_alias_gin_trgm_idx")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")

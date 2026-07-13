"""Compatibility marker for the reverted opportunities migration.

Revision ID: 0003

Some local databases applied the former 0003 migration before that product work was reverted.
Recognising the revision lets those databases move forward. The next migration removes the legacy
table if it is still present.
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "opportunities" in tables:
        op.drop_table("opportunities")

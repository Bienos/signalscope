"""Initial schema.

Revision ID: 0001
"""

from alembic import op

from app import models  # noqa: F401
from app.db import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # checkfirst keeps this migration compatible with databases created by
    # the local seed command in early MVP installations.
    Base.metadata.create_all(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(op.get_bind(), checkfirst=True)


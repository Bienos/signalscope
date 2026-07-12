"""Add auditable score evidence.

Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa

revision="0002"
down_revision="0001"
branch_labels=None
depends_on=None

def upgrade()->None:
    existing={column["name"] for column in sa.inspect(op.get_bind()).get_columns("viral_scores")}
    if "confidence_score" not in existing:op.add_column("viral_scores",sa.Column("confidence_score",sa.Float(),nullable=False,server_default="0"))
    if "components" not in existing:op.add_column("viral_scores",sa.Column("components",sa.JSON(),nullable=False,server_default=sa.text("'{}'")))
    if "cohort" not in existing:op.add_column("viral_scores",sa.Column("cohort",sa.JSON(),nullable=False,server_default=sa.text("'{}'")))
    if "score_version" not in existing:op.add_column("viral_scores",sa.Column("score_version",sa.String(length=20),nullable=False,server_default="2.0"))

def downgrade()->None:
    existing={column["name"] for column in sa.inspect(op.get_bind()).get_columns("viral_scores")}
    for name in ("score_version","cohort","components","confidence_score"):
        if name in existing:op.drop_column("viral_scores",name)

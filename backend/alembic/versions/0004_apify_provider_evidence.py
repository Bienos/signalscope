"""Preserve provider provenance and nullable engagement metrics.

Revision ID: 0004_apify_provider_evidence
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_apify_provider_evidence"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "opportunities" in tables:
        op.drop_table("opportunities")
    video_columns = {column["name"] for column in inspector.get_columns("videos")}
    if "raw_reference" not in video_columns:
        op.add_column(
            "videos",
            sa.Column("raw_reference", sa.String(length=300), nullable=False, server_default=""),
        )
    with op.batch_alter_table("creators") as batch:
        batch.alter_column("followers", existing_type=sa.Integer(), nullable=True)
    with op.batch_alter_table("video_snapshots") as batch:
        for column in ("views", "likes", "comments", "shares"):
            batch.alter_column(column, existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE creators SET followers = 0 WHERE followers IS NULL")
    with op.batch_alter_table("creators") as batch:
        batch.alter_column("followers", existing_type=sa.Integer(), nullable=False)
    for column in ("views", "likes", "comments", "shares"):
        op.execute(f"UPDATE video_snapshots SET {column} = 0 WHERE {column} IS NULL")
    with op.batch_alter_table("video_snapshots") as batch:
        for column in ("views", "likes", "comments", "shares"):
            batch.alter_column(column, existing_type=sa.Integer(), nullable=False)
    video_columns = {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("videos")
    }
    if "raw_reference" in video_columns:
        op.drop_column("videos", "raw_reference")

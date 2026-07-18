"""Add toy trend intelligence persistence foundations.

Revision ID: 0005_toy_trend_foundations
"""

from collections.abc import Iterable

from alembic import op
import sqlalchemy as sa

revision = "0005_toy_trend_foundations"
down_revision = "0004_apify_provider_evidence"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _add_columns(table: str, columns: Iterable[sa.Column]) -> None:
    existing = _columns(table)
    for column in columns:
        if column.name not in existing:
            op.add_column(table, column)


def upgrade() -> None:
    _add_columns(
        "provider_runs",
        (
            sa.Column("actor_id", sa.String(length=160), nullable=True),
            sa.Column("actor_version", sa.String(length=80), nullable=True),
            sa.Column("external_run_id", sa.String(length=160), nullable=True),
            sa.Column("dataset_id", sa.String(length=160), nullable=True),
            sa.Column("collection_type", sa.String(length=40), nullable=True),
            sa.Column("market", sa.String(length=8), nullable=True),
            sa.Column(
                "query_provenance",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            ),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("returned_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("accepted_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("duplicate_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("invalid_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("missing_field_rate", sa.Float(), nullable=True),
            sa.Column("cost", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=True),
            sa.Column("schema_fingerprint", sa.String(length=128), nullable=True),
            sa.Column("error_category", sa.String(length=80), nullable=True),
            sa.Column("error_summary", sa.Text(), nullable=True),
        ),
    )
    _add_columns(
        "creators",
        (
            sa.Column("profile_url", sa.String(length=300), nullable=True),
            sa.Column("account_region", sa.String(length=8), nullable=True),
            sa.Column("verified", sa.Boolean(), nullable=True),
            sa.Column(
                "creator_type", sa.String(length=80), nullable=False, server_default="Unknown"
            ),
            sa.Column("provider", sa.String(length=80), nullable=False, server_default="unknown"),
            sa.Column("raw_reference", sa.String(length=300), nullable=False, server_default=""),
            sa.Column(
                "missing_fields", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column("last_observed_at", sa.DateTime(), nullable=True),
        ),
    )
    _add_columns(
        "sounds",
        (
            sa.Column("provider", sa.String(length=80), nullable=False, server_default="unknown"),
            sa.Column("raw_reference", sa.String(length=300), nullable=False, server_default=""),
            sa.Column(
                "missing_fields", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column("last_observed_at", sa.DateTime(), nullable=True),
        ),
    )
    _add_columns(
        "videos",
        (
            sa.Column("provider_run_id", sa.Integer(), nullable=True),
            sa.Column("provider_language", sa.String(length=12), nullable=True),
            sa.Column("detected_language", sa.String(length=12), nullable=True),
            sa.Column("collection_market", sa.String(length=8), nullable=True),
            sa.Column("toy_category", sa.String(length=100), nullable=True),
            sa.Column("content_mechanism", sa.String(length=100), nullable=True),
            sa.Column(
                "safety_flags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "availability_status",
                sa.String(length=30),
                nullable=False,
                server_default="available",
            ),
            sa.Column(
                "discovery_query", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            ),
            sa.Column("schema_fingerprint", sa.String(length=128), nullable=True),
            sa.Column("first_observed_at", sa.DateTime(), nullable=True),
            sa.Column("last_observed_at", sa.DateTime(), nullable=True),
        ),
    )
    video_columns = _columns("videos")
    video_foreign_keys = {
        tuple(foreign_key.get("constrained_columns") or [])
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys("videos")
    }
    if "provider_run_id" in video_columns and ("provider_run_id",) not in video_foreign_keys:
        with op.batch_alter_table("videos") as batch:
            batch.create_foreign_key(
                "fk_videos_provider_run_id_provider_runs",
                "provider_runs",
                ["provider_run_id"],
                ["id"],
            )

    _add_columns(
        "video_snapshots",
        (
            sa.Column("provider_run_id", sa.Integer(), nullable=True),
            sa.Column("creator_follower_count", sa.Integer(), nullable=True),
            sa.Column(
                "availability_state",
                sa.String(length=30),
                nullable=False,
                server_default="available",
            ),
        ),
    )
    snapshot_columns = _columns("video_snapshots")
    snapshot_foreign_keys = {
        tuple(foreign_key.get("constrained_columns") or [])
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys("video_snapshots")
    }
    if (
        "provider_run_id" in snapshot_columns
        and ("provider_run_id",) not in snapshot_foreign_keys
    ):
        with op.batch_alter_table("video_snapshots") as batch:
            batch.create_foreign_key(
                "fk_video_snapshots_provider_run_id_provider_runs",
                "provider_runs",
                ["provider_run_id"],
                ["id"],
            )

    acceleration = next(
        column for column in sa.inspect(op.get_bind()).get_columns("viral_scores")
        if column["name"] == "acceleration"
    )
    if not acceleration["nullable"]:
        with op.batch_alter_table("viral_scores") as batch:
            batch.alter_column(
                "acceleration", existing_type=sa.Float(), nullable=True
            )

    tables = _tables()
    if "toy_signals" not in tables:
        op.create_table(
            "toy_signals",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("stable_key", sa.String(length=128), nullable=False, unique=True),
            sa.Column("title", sa.String(length=220), nullable=False),
            sa.Column("toy_category", sa.String(length=100), nullable=False),
            sa.Column(
                "content_mechanism",
                sa.String(length=100),
                nullable=False,
                server_default="Unknown",
            ),
            sa.Column(
                "lifecycle",
                sa.String(length=40),
                nullable=False,
                server_default="Insufficient evidence",
            ),
            sa.Column(
                "recommended_decision",
                sa.String(length=20),
                nullable=False,
                server_default="Monitor",
            ),
            sa.Column("confidence", sa.String(length=12), nullable=False, server_default="Low"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("first_detected_at", sa.DateTime(), nullable=False),
            sa.Column("last_calculated_at", sa.DateTime(), nullable=False),
            sa.Column("data_freshness_at", sa.DateTime(), nullable=True),
            sa.Column("unique_creators", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("post_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cohort_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("markets", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("languages", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column(
                "related_hashtags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "related_sounds", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column("saturation", sa.String(length=20), nullable=False, server_default="Low"),
            sa.Column("saturation_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("opportunity_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("main_supporting_evidence", sa.Text(), nullable=False, server_default=""),
            sa.Column(
                "main_contradictory_evidence", sa.Text(), nullable=False, server_default=""
            ),
            sa.Column("safety_state", sa.String(length=30), nullable=False, server_default="Unknown"),
            sa.Column("explanation", sa.Text(), nullable=False, server_default=""),
            sa.Column("components", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column(
                "missing_components", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "score_version", sa.String(length=20), nullable=False, server_default="toy-1.0"
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_toy_signals_stable_key", "toy_signals", ["stable_key"])
        op.create_index("ix_toy_signals_toy_category", "toy_signals", ["toy_category"])
        op.create_index("ix_toy_signals_lifecycle", "toy_signals", ["lifecycle"])

    tables = _tables()
    if "signal_video_evidence" not in tables:
        op.create_table(
            "signal_video_evidence",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("signal_id", sa.Integer(), sa.ForeignKey("toy_signals.id"), nullable=False),
            sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id"), nullable=False),
            sa.Column(
                "evidence_type",
                sa.String(length=40),
                nullable=False,
                server_default="supporting",
            ),
            sa.Column("supporting", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
            sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
            sa.Column("metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("observed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("signal_id", "video_id", name="uq_signal_video_evidence"),
        )
        op.create_index(
            "ix_signal_video_evidence_signal_id", "signal_video_evidence", ["signal_id"]
        )
        op.create_index(
            "ix_signal_video_evidence_video_id", "signal_video_evidence", ["video_id"]
        )

    tables = _tables()
    if "signal_decisions" not in tables:
        op.create_table(
            "signal_decisions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("signal_id", sa.Integer(), sa.ForeignKey("toy_signals.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column(
                "user_key", sa.String(length=80), nullable=False, server_default="single-user"
            ),
            sa.Column("decision", sa.String(length=20), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("analyst_note", sa.Text(), nullable=False, server_default=""),
            sa.Column("review_date", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("signal_id", "user_key", name="uq_signal_decision_user"),
        )
        op.create_index("ix_signal_decisions_signal_id", "signal_decisions", ["signal_id"])

    tables = _tables()
    if "opportunities" not in tables:
        op.create_table(
            "opportunities",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "source_signal_id", sa.Integer(), sa.ForeignKey("toy_signals.id"), nullable=False
            ),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column(
                "user_key", sa.String(length=80), nullable=False, server_default="single-user"
            ),
            sa.Column("state", sa.String(length=30), nullable=False, server_default="saved"),
            sa.Column("decision", sa.String(length=20), nullable=False, server_default="Monitor"),
            sa.Column("title", sa.String(length=220), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
            sa.Column("analyst_note", sa.Text(), nullable=False, server_default=""),
            sa.Column("client_context", sa.Text(), nullable=False, server_default=""),
            sa.Column("decision_window", sa.String(length=120), nullable=False, server_default=""),
            sa.Column("mechanism", sa.String(length=100), nullable=False, server_default=""),
            sa.Column("adaptation_notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("audience_need", sa.Text(), nullable=False, server_default=""),
            sa.Column("original_hook", sa.Text(), nullable=False, server_default=""),
            sa.Column("content_structure", sa.Text(), nullable=False, server_default=""),
            sa.Column(
                "recommended_creator_type",
                sa.String(length=100),
                nullable=False,
                server_default="Unknown",
            ),
            sa.Column(
                "production_complexity",
                sa.String(length=40),
                nullable=False,
                server_default="Unknown",
            ),
            sa.Column(
                "elements_not_to_copy", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "safety_considerations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "rights_considerations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "evidence_limitations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column(
                "originality_checks", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
            ),
            sa.Column("safety_checks", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("rights_note", sa.Text(), nullable=False, server_default=""),
            sa.Column("brief_status", sa.String(length=30), nullable=False, server_default="draft"),
            sa.Column(
                "review_status", sa.String(length=30), nullable=False, server_default="pending"
            ),
            sa.Column("include_in_report", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index(
            "ix_opportunities_source_signal_id", "opportunities", ["source_signal_id"]
        )

    tables = _tables()
    if "watchlists" not in tables:
        op.create_table(
            "watchlists",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column(
                "user_key", sa.String(length=80), nullable=False, server_default="single-user"
            ),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("objective", sa.Text(), nullable=False, server_default=""),
            sa.Column("categories", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("markets", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("languages", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("data_status", sa.String(length=30), nullable=False, server_default="demo"),
            sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("user_key", "name", name="uq_watchlist_user_name"),
        )

    tables = _tables()
    if "provider_quarantine" not in tables:
        op.create_table(
            "provider_quarantine",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "provider_run_id", sa.Integer(), sa.ForeignKey("provider_runs.id"), nullable=True
            ),
            sa.Column("provider", sa.String(length=80), nullable=False),
            sa.Column("external_record_id", sa.String(length=160), nullable=True),
            sa.Column("reason_code", sa.String(length=80), nullable=False),
            sa.Column("redacted_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("raw_reference", sa.String(length=300), nullable=False, server_default=""),
            sa.Column("schema_fingerprint", sa.String(length=128), nullable=True),
            sa.Column(
                "missing_fields", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
            ),
            sa.Column("quarantined_at", sa.DateTime(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
            sa.Column("resolution", sa.Text(), nullable=True),
        )
        op.create_index(
            "ix_provider_quarantine_provider_run_id", "provider_quarantine", ["provider_run_id"]
        )
        op.create_index("ix_provider_quarantine_provider", "provider_quarantine", ["provider"])


def downgrade() -> None:
    tables = _tables()
    for table in (
        "provider_quarantine",
        "watchlists",
        "opportunities",
        "signal_decisions",
        "signal_video_evidence",
        "toy_signals",
    ):
        if table in tables:
            op.drop_table(table)

    acceleration = next(
        column for column in sa.inspect(op.get_bind()).get_columns("viral_scores")
        if column["name"] == "acceleration"
    )
    if acceleration["nullable"]:
        op.execute("UPDATE viral_scores SET acceleration = 0 WHERE acceleration IS NULL")
        with op.batch_alter_table("viral_scores") as batch:
            batch.alter_column("acceleration", existing_type=sa.Float(), nullable=False)

    removal = {
        "video_snapshots": (
            "availability_state",
            "creator_follower_count",
            "provider_run_id",
        ),
        "videos": (
            "last_observed_at",
            "first_observed_at",
            "schema_fingerprint",
            "discovery_query",
            "availability_status",
            "safety_flags",
            "content_mechanism",
            "toy_category",
            "collection_market",
            "detected_language",
            "provider_language",
            "provider_run_id",
        ),
        "sounds": ("last_observed_at", "missing_fields", "raw_reference", "provider"),
        "creators": (
            "last_observed_at",
            "missing_fields",
            "raw_reference",
            "provider",
            "creator_type",
            "verified",
            "account_region",
            "profile_url",
        ),
        "provider_runs": (
            "error_summary",
            "error_category",
            "schema_fingerprint",
            "currency",
            "cost",
            "missing_field_rate",
            "invalid_records",
            "duplicate_records",
            "accepted_records",
            "returned_records",
            "finished_at",
            "query_provenance",
            "market",
            "collection_type",
            "dataset_id",
            "external_run_id",
            "actor_version",
            "actor_id",
        ),
    }
    for table, columns in removal.items():
        existing = _columns(table)
        removable = [column for column in columns if column in existing]
        if removable:
            inspector = sa.inspect(op.get_bind())
            for index in inspector.get_indexes(table):
                indexed_columns = set(index.get("column_names") or [])
                if indexed_columns.intersection(removable) and index.get("name"):
                    op.drop_index(index["name"], table_name=table)
            # Batch mode removes any foreign keys attached to the removed
            # provider_run_id columns on SQLite and remains valid on Postgres.
            with op.batch_alter_table(table) as batch:
                for column in removable:
                    batch.drop_column(column)

"""Scope daily reports to the authenticated user.

Revision ID: 0006_user_scoped_reports
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_user_scoped_reports"
down_revision = "0005_toy_trend_foundations"
branch_labels = None
depends_on = None


_NAMING = {"uq": "uq_%(table_name)s_%(column_0_name)s"}


def _unique_constraints() -> list[dict[str, object]]:
    return list(sa.inspect(op.get_bind()).get_unique_constraints("daily_reports"))


def _columns() -> set[str]:
    return {
        str(column["name"])
        for column in sa.inspect(op.get_bind()).get_columns("daily_reports")
    }


def _indexes() -> set[str]:
    return {
        str(index["name"])
        for index in sa.inspect(op.get_bind()).get_indexes("daily_reports")
        if index.get("name")
    }


def upgrade() -> None:
    if "user_key" not in _columns():
        op.add_column(
            "daily_reports",
            sa.Column(
                "user_key",
                sa.String(length=80),
                nullable=False,
                server_default=sa.text("'single-user'"),
            ),
        )

    constraints = _unique_constraints()
    legacy = next(
        (
            constraint
            for constraint in constraints
            if list(constraint.get("column_names") or []) == ["report_date"]
        ),
        None,
    )
    scoped_exists = any(
        set(constraint.get("column_names") or []) == {"report_date", "user_key"}
        for constraint in constraints
    )

    if legacy is not None:
        legacy_name = str(legacy.get("name") or "uq_daily_reports_report_date")
        with op.batch_alter_table(
            "daily_reports",
            recreate="always" if op.get_bind().dialect.name == "sqlite" else "auto",
            naming_convention=_NAMING,
        ) as batch:
            batch.drop_constraint(legacy_name, type_="unique")
            if not scoped_exists:
                batch.create_unique_constraint(
                    "uq_daily_report_date_user", ["report_date", "user_key"]
                )
    elif not scoped_exists:
        op.create_unique_constraint(
            "uq_daily_report_date_user",
            "daily_reports",
            ["report_date", "user_key"],
        )

    if "ix_daily_reports_user_key" not in _indexes():
        op.create_index("ix_daily_reports_user_key", "daily_reports", ["user_key"])
    if "ix_daily_reports_report_date" not in _indexes():
        op.create_index("ix_daily_reports_report_date", "daily_reports", ["report_date"])


def downgrade() -> None:
    # A downgrade cannot represent more than one report per date. Keep the
    # oldest row for each date so the legacy unique constraint can be restored.
    op.execute(
        sa.text(
            "DELETE FROM daily_reports WHERE id NOT IN "
            "(SELECT MIN(id) FROM daily_reports GROUP BY report_date)"
        )
    )
    constraints = _unique_constraints()
    scoped = next(
        (
            constraint
            for constraint in constraints
            if set(constraint.get("column_names") or []) == {"report_date", "user_key"}
        ),
        None,
    )
    if "ix_daily_reports_user_key" in _indexes():
        op.drop_index("ix_daily_reports_user_key", table_name="daily_reports")
    if "ix_daily_reports_report_date" in _indexes():
        op.drop_index("ix_daily_reports_report_date", table_name="daily_reports")
    with op.batch_alter_table(
        "daily_reports",
        recreate="always" if op.get_bind().dialect.name == "sqlite" else "auto",
        naming_convention=_NAMING,
    ) as batch:
        if scoped is not None:
            batch.drop_constraint(
                str(scoped.get("name") or "uq_daily_report_date_user"), type_="unique"
            )
        batch.drop_column("user_key")
        batch.create_unique_constraint("uq_daily_reports_report_date", ["report_date"])


"""initial schema

Revision ID: 20260406_000001
Revises:
Create Date: 2026-04-06 00:00:01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260406_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


event_type = postgresql.ENUM("RAIN", "FROST", "HAIL", "STRONG_WIND", name="event_type", create_type=False)
validity_window_kind = postgresql.ENUM("RELATIVE", "ABSOLUTE", name="validity_window_kind", create_type=False)
relative_window_unit = postgresql.ENUM("HOUR", "DAY", "WEEK", "MONTH", "YEAR", name="relative_window_unit", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    event_type.create(bind, checkfirst=True)
    validity_window_kind.create(bind, checkfirst=True)
    relative_window_unit.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("ix_users_phone", "users", ["phone"], unique=False)

    op.create_table(
        "fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_fields_user_id", "fields", ["user_id"], unique=False)

    op.create_table(
        "weather_forecasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("forecast_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("probability_percent", sa.Float(), nullable=False),
        sa.Column("intensity_value", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("field_id", "forecast_datetime", "event_type", name="uq_weather_forecast_field_datetime_event"),
    )
    op.create_index(
        "ix_weather_forecasts_field_event_datetime",
        "weather_forecasts",
        ["field_id", "event_type", "forecast_datetime"],
        unique=False,
    )

    op.create_table(
        "weather_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("probability_threshold_percent", sa.Float(), nullable=False),
        sa.Column("intensity_threshold_value", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_weather_alerts_field_id", "weather_alerts", ["field_id"], unique=False)
    op.create_index("ix_weather_alerts_user_id", "weather_alerts", ["user_id"], unique=False)
    op.create_index(
        "ix_weather_alerts_field_event_active",
        "weather_alerts",
        ["field_id", "event_type", "is_active"],
        unique=False,
    )

    op.create_table(
        "alert_validity_windows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("kind", validity_window_kind, nullable=False),
        sa.Column("relative_value", sa.Integer(), nullable=True),
        sa.Column("relative_unit", relative_window_unit, nullable=True),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["weather_alerts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_validity_windows_alert_id", "alert_validity_windows", ["alert_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("forecast_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger_probability_percent", sa.Float(), nullable=False),
        sa.Column("trigger_intensity_value", sa.Float(), nullable=True),
        sa.Column("message", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["weather_alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["forecast_id"], ["weather_forecasts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("alert_id", "forecast_id", name="uq_notifications_alert_forecast"),
    )
    op.create_index("ix_notifications_alert_id", "notifications", ["alert_id"], unique=False)
    op.create_index("ix_notifications_field_id", "notifications", ["field_id"], unique=False)
    op.create_index("ix_notifications_forecast_id", "notifications", ["forecast_id"], unique=False)
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_user_created_at", "notifications", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_user_created_at", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_forecast_id", table_name="notifications")
    op.drop_index("ix_notifications_field_id", table_name="notifications")
    op.drop_index("ix_notifications_alert_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_alert_validity_windows_alert_id", table_name="alert_validity_windows")
    op.drop_table("alert_validity_windows")

    op.drop_index("ix_weather_alerts_field_event_active", table_name="weather_alerts")
    op.drop_index("ix_weather_alerts_user_id", table_name="weather_alerts")
    op.drop_index("ix_weather_alerts_field_id", table_name="weather_alerts")
    op.drop_table("weather_alerts")

    op.drop_index("ix_weather_forecasts_field_event_datetime", table_name="weather_forecasts")
    op.drop_table("weather_forecasts")

    op.drop_index("ix_fields_user_id", table_name="fields")
    op.drop_table("fields")

    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    relative_window_unit.drop(bind, checkfirst=True)
    validity_window_kind.drop(bind, checkfirst=True)
    event_type.drop(bind, checkfirst=True)

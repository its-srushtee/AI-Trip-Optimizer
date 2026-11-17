"""trippulse and budget guardian schema extensions

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Trip Expenses table
    op.create_table(
        "trip_expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("original_amount", sa.Float(), nullable=True),
        sa.Column("original_currency", sa.String(length=10), nullable=True),
        sa.Column("exchange_rate", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trip_expenses_trip_id", "trip_expenses", ["trip_id"])
    op.create_index("ix_trip_expenses_user_id", "trip_expenses", ["user_id"])
    op.create_index("ix_trip_expenses_idempotency_key", "trip_expenses", ["idempotency_key"], unique=True)

    # 2. Trip Alerts table
    op.create_table(
        "trip_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="yellow"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("relevant_date", sa.Date(), nullable=True),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("simulation_type", sa.String(length=50), nullable=True),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trip_alerts_trip_id", "trip_alerts", ["trip_id"])

    # 3. Trip Monitoring Logs table
    op.create_table(
        "trip_monitoring_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_health", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("health_status", sa.String(length=20), nullable=False, server_default="green"),
        sa.Column("weather_status", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("budget_status", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("disruptions_detected", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("recommendations_summary", sa.Text(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trip_monitoring_logs_trip_id", "trip_monitoring_logs", ["trip_id"])

    # 4. Trip Reoptimizations table
    op.create_table(
        "trip_reoptimizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trigger_reason", sa.String(length=100), nullable=False),
        sa.Column("original_itinerary", sa.JSON(), nullable=False),
        sa.Column("proposed_itinerary", sa.JSON(), nullable=False),
        sa.Column("diff_summary", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("applied_changes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_trip_reoptimizations_trip_id", "trip_reoptimizations", ["trip_id"])

    # 5. Trip Chat Messages table
    op.create_table(
        "trip_chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("action_proposal", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trip_chat_messages_trip_id", "trip_chat_messages", ["trip_id"])
    op.create_index("ix_trip_chat_messages_user_id", "trip_chat_messages", ["user_id"])


def downgrade() -> None:
    op.drop_table("trip_chat_messages")
    op.drop_table("trip_reoptimizations")
    op.drop_table("trip_monitoring_logs")
    op.drop_table("trip_alerts")
    op.drop_table("trip_expenses")

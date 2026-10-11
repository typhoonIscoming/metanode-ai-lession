"""initial schema

建立 6 张核心表与默认 setting 行。所有时间字段 timestamptz；
setting 单行约束（id = 1）保证全局只一份配置；
market.condition_id UNIQUE 保证手动 + 自动发现去重；
signal_event 双索引覆盖「按市场翻页」与「未推送扫描」两个高频读路径。

Revision ID: 20260518_0001
Revises:
Create Date: 2026-05-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260518_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ---- 1. setting：全局配置单行 ----
    op.create_table(
        "setting",
        sa.Column("id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "entry_threshold",
            sa.Numeric(4, 3),
            nullable=False,
            server_default="0.150",
        ),
        sa.Column("debounce_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("price_poll_minutes", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("predict_ttl_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column(
            "discovery_keywords",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default="{bitcoin,btc}",
        ),
        sa.Column(
            "discovery_max_days_to_resolve",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column("feishu_webhook_url", sa.Text(), nullable=True),
        sa.Column("openai_api_key", sa.Text(), nullable=True),
        sa.Column(
            "openai_model",
            sa.String(64),
            nullable=False,
            server_default="gpt-5",
        ),
        sa.Column(
            "web_search_provider",
            sa.String(32),
            nullable=False,
            server_default="tavily",
        ),
        sa.Column("web_search_api_key", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("id = 1", name="ck_setting_singleton"),
        sa.CheckConstraint("debounce_minutes >= 1", name="ck_setting_debounce_min"),
        sa.CheckConstraint("price_poll_minutes >= 1", name="ck_setting_poll_min"),
        sa.CheckConstraint("predict_ttl_hours >= 1", name="ck_setting_ttl_min"),
        sa.CheckConstraint(
            "web_search_provider IN ('tavily','exa','brave','openai')",
            name="ck_setting_web_search_provider",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_setting"),
    )
    # seed 单行默认 setting；下游 patch /api/v1/settings 都改这条
    op.execute("INSERT INTO setting (id) VALUES (1)")

    # ---- 2. market ----
    op.create_table(
        "market",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("condition_id", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("strike_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("direction", sa.String(8), nullable=True),
        sa.Column("resolve_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome_yes_token_id", sa.Text(), nullable=False),
        sa.Column("outcome_no_token_id", sa.Text(), nullable=False),
        sa.Column(
            "state",
            sa.String(16),
            nullable=False,
            server_default="WATCHING",
        ),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_state_change_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("direction IN ('above','below')", name="ck_market_direction"),
        sa.CheckConstraint(
            "state IN ('WATCHING','ENTERED_LONG','ENTERED_SHORT','EXPIRED')",
            name="ck_market_state",
        ),
        sa.CheckConstraint("source IN ('discovery','manual')", name="ck_market_source"),
        sa.UniqueConstraint("condition_id", name="uq_market_condition_id"),
        sa.PrimaryKeyConstraint("id", name="pk_market"),
    )
    op.create_index(
        "market_state_active_idx",
        "market",
        ["state"],
        postgresql_where=sa.text("state <> 'EXPIRED'"),
    )
    op.create_index("market_resolve_at_idx", "market", ["resolve_at"])

    # ---- 3. prediction ----
    op.create_table(
        "prediction",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("market_id", sa.BigInteger(), nullable=False),
        sa.Column("p_ai", sa.Numeric(5, 4), nullable=False),
        sa.Column("p_quant", sa.Numeric(5, 4), nullable=False),
        sa.Column("llm_adjustment", sa.Numeric(6, 4), nullable=False),
        sa.Column("llm_confidence", sa.String(8), nullable=True),
        sa.Column("llm_rationale", sa.Text(), nullable=True),
        sa.Column(
            "news_sources",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("spot_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("realized_vol", sa.Numeric(8, 6), nullable=True),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("p_ai BETWEEN 0 AND 1", name="ck_prediction_p_ai_range"),
        sa.CheckConstraint("p_quant BETWEEN 0 AND 1", name="ck_prediction_p_quant_range"),
        sa.CheckConstraint(
            "llm_confidence IN ('low','medium','high') OR llm_confidence IS NULL",
            name="ck_prediction_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["market_id"],
            ["market.id"],
            ondelete="CASCADE",
            name="fk_prediction_market",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_prediction"),
    )
    op.create_index(
        "prediction_market_created_idx",
        "prediction",
        ["market_id", sa.text("created_at DESC")],
    )

    # ---- 4. price_tick ----
    op.create_table(
        "price_tick",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("market_id", sa.BigInteger(), nullable=False),
        sa.Column("p_yes", sa.Numeric(5, 4), nullable=False),
        sa.Column("p_no", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "midpoint_source",
            sa.String(32),
            nullable=False,
            server_default="clob_midpoint",
        ),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("p_yes BETWEEN 0 AND 1", name="ck_price_tick_p_yes_range"),
        sa.ForeignKeyConstraint(
            ["market_id"],
            ["market.id"],
            ondelete="CASCADE",
            name="fk_price_tick_market",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_price_tick"),
    )
    op.create_index(
        "price_tick_market_fetched_idx",
        "price_tick",
        ["market_id", sa.text("fetched_at DESC")],
    )

    # ---- 5. signal_event ----
    op.create_table(
        "signal_event",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("market_id", sa.BigInteger(), nullable=False),
        sa.Column("prediction_id", sa.BigInteger(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("from_state", sa.String(16), nullable=False),
        sa.Column("to_state", sa.String(16), nullable=False),
        sa.Column("p_ai_at_event", sa.Numeric(5, 4), nullable=False),
        sa.Column("p_mkt_at_event", sa.Numeric(5, 4), nullable=False),
        sa.Column("gap", sa.Numeric(6, 4), nullable=False),
        sa.Column(
            "feishu_pushed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("feishu_push_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feishu_error", sa.Text(), nullable=True),
        sa.Column(
            "feishu_retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "kind IN ('ENTRY_LONG','ENTRY_SHORT','EXIT_LONG','EXIT_SHORT','EXPIRED')",
            name="ck_signal_event_kind",
        ),
        sa.ForeignKeyConstraint(
            ["market_id"],
            ["market.id"],
            ondelete="CASCADE",
            name="fk_signal_event_market",
        ),
        sa.ForeignKeyConstraint(
            ["prediction_id"],
            ["prediction.id"],
            name="fk_signal_event_prediction",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_signal_event"),
    )
    op.create_index(
        "signal_event_market_occurred_idx",
        "signal_event",
        ["market_id", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "signal_event_unpushed_idx",
        "signal_event",
        ["occurred_at"],
        postgresql_where=sa.text("feishu_pushed = false"),
    )

    # ---- 6. job_run ----
    op.create_table(
        "job_run",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "stats",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('running','success','failed')",
            name="ck_job_run_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_job_run"),
    )
    op.create_index(
        "job_run_name_started_idx",
        "job_run",
        ["job_name", sa.text("started_at DESC")],
    )


def downgrade() -> None:
    # 反向依赖顺序：先删带 FK 的子表，再删父表
    op.drop_index("job_run_name_started_idx", table_name="job_run")
    op.drop_table("job_run")

    op.drop_index("signal_event_unpushed_idx", table_name="signal_event")
    op.drop_index("signal_event_market_occurred_idx", table_name="signal_event")
    op.drop_table("signal_event")

    op.drop_index("price_tick_market_fetched_idx", table_name="price_tick")
    op.drop_table("price_tick")

    op.drop_index("prediction_market_created_idx", table_name="prediction")
    op.drop_table("prediction")

    op.drop_index("market_resolve_at_idx", table_name="market")
    op.drop_index("market_state_active_idx", table_name="market")
    op.drop_table("market")

    op.drop_table("setting")

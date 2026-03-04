"""phase1: add 7 tables (spc, capa, oee, notifications)

Revision ID: e20bee5ef217
Revises: 59d7a9d4a614
Create Date: 2026-03-04 09:14:41.017293
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e20bee5ef217'
down_revision: Union[str, Sequence[str], None] = '59d7a9d4a614'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PHASE1_TABLES = [
    "spc_rules", "spc_violations", "capa", "capa_actions",
    "oee_daily", "notifications", "notification_settings",
]


def upgrade() -> None:
    op.create_table(
        "spc_rules",
        sa.Column("rule_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column("rule_type", sa.String(20), nullable=False, server_default="XBAR_R"),
        sa.Column("ucl", sa.Numeric(12, 4)),
        sa.Column("lcl", sa.Numeric(12, 4)),
        sa.Column("target", sa.Numeric(12, 4)),
        sa.Column("sample_size", sa.Integer, nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("rule_type IN ('XBAR_R','XBAR_S','P','NP','C','U')", name="ck_spc_rule_type"),
        sa.UniqueConstraint("item_code", "check_name", name="uq_spc_rule_item_check"),
    )
    op.create_table(
        "spc_violations",
        sa.Column("violation_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.Integer, sa.ForeignKey("spc_rules.rule_id")),
        sa.Column("inspection_id", sa.Integer, sa.ForeignKey("inspections.inspection_id")),
        sa.Column("violation_type", sa.String(50), nullable=False),
        sa.Column("measured_value", sa.Numeric(12, 4)),
        sa.Column("subgroup_no", sa.Integer),
        sa.Column("severity", sa.String(10), server_default="WARNING"),
        sa.Column("resolved", sa.Boolean, server_default=sa.text("FALSE")),
        sa.Column("resolved_at", sa.TIMESTAMP),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("severity IN ('WARNING','CRITICAL')", name="ck_spc_viol_severity"),
    )
    op.create_table(
        "capa",
        sa.Column("capa_id", sa.String(30), primary_key=True),
        sa.Column("capa_type", sa.String(20), nullable=False),
        sa.Column("source_type", sa.String(30)),
        sa.Column("source_id", sa.String(50)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("priority", sa.String(10), server_default="MID"),
        sa.Column("assigned_to", sa.String(50), sa.ForeignKey("users.user_id")),
        sa.Column("due_date", sa.Date),
        sa.Column("closed_at", sa.TIMESTAMP),
        sa.Column("created_by", sa.String(50), sa.ForeignKey("users.user_id")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("capa_type IN ('CORRECTIVE','PREVENTIVE')", name="ck_capa_type"),
        sa.CheckConstraint("status IN ('OPEN','INVESTIGATION','ACTION','VERIFICATION','CLOSED','REJECTED')", name="ck_capa_status"),
        sa.CheckConstraint("priority IN ('HIGH','MID','LOW')", name="ck_capa_priority"),
    )
    op.create_table(
        "capa_actions",
        sa.Column("action_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("capa_id", sa.String(30), sa.ForeignKey("capa.capa_id")),
        sa.Column("action_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("result", sa.Text),
        sa.Column("performed_by", sa.String(50), sa.ForeignKey("users.user_id")),
        sa.Column("performed_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("action_type IN ('ROOT_CAUSE','CORRECTIVE','PREVENTIVE','VERIFICATION')", name="ck_capa_action_type"),
    )
    op.create_table(
        "oee_daily",
        sa.Column("oee_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("equip_code", sa.String(20), sa.ForeignKey("equipments.equip_code")),
        sa.Column("calc_date", sa.Date, nullable=False),
        sa.Column("planned_time", sa.Numeric(8, 2), server_default="480"),
        sa.Column("downtime", sa.Numeric(8, 2), server_default="0"),
        sa.Column("ideal_ct", sa.Numeric(8, 4)),
        sa.Column("total_count", sa.Integer, server_default="0"),
        sa.Column("good_count", sa.Integer, server_default="0"),
        sa.Column("availability", sa.Numeric(5, 4)),
        sa.Column("performance", sa.Numeric(5, 4)),
        sa.Column("quality_rate", sa.Numeric(5, 4)),
        sa.Column("oee", sa.Numeric(5, 4)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("equip_code", "calc_date", name="uq_oee_equip_date"),
    )
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.user_id")),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("severity", sa.String(10), server_default="INFO"),
        sa.Column("ref_type", sa.String(30)),
        sa.Column("ref_id", sa.String(50)),
        sa.Column("is_read", sa.Boolean, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("type IN ('EQUIP_DOWN','SPC_VIOLATION','INVENTORY_LOW','AI_WARNING','CAPA_DUE','SYSTEM')", name="ck_notif_type"),
        sa.CheckConstraint("severity IN ('INFO','WARNING','CRITICAL')", name="ck_notif_severity"),
    )
    op.create_table(
        "notification_settings",
        sa.Column("setting_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.user_id")),
        sa.Column("notification_type", sa.String(30), nullable=False),
        sa.Column("channel", sa.String(20), server_default="WEB"),
        sa.Column("is_enabled", sa.Boolean, server_default=sa.text("TRUE")),
        sa.CheckConstraint("channel IN ('WEB','EMAIL','BOTH')", name="ck_ns_channel"),
        sa.UniqueConstraint("user_id", "notification_type", "channel", name="uq_ns_user_type_ch"),
    )

    # Indexes
    for idx_name, tbl, cols in [
        ("idx_spc_rules_item", "spc_rules", ["item_code"]),
        ("idx_spc_violations_rule", "spc_violations", ["rule_id"]),
        ("idx_spc_violations_created", "spc_violations", ["created_at"]),
        ("idx_capa_status", "capa", ["status"]),
        ("idx_capa_assigned", "capa", ["assigned_to"]),
        ("idx_capa_due", "capa", ["due_date"]),
        ("idx_capa_actions_capa", "capa_actions", ["capa_id"]),
        ("idx_oee_equip", "oee_daily", ["equip_code"]),
        ("idx_oee_date", "oee_daily", ["calc_date"]),
        ("idx_oee_equip_date", "oee_daily", ["equip_code", "calc_date"]),
        ("idx_notif_user", "notifications", ["user_id"]),
        ("idx_notif_unread", "notifications", ["user_id", "is_read"]),
        ("idx_notif_created", "notifications", ["created_at"]),
        ("idx_notif_settings_user", "notification_settings", ["user_id"]),
    ]:
        op.create_index(idx_name, tbl, cols)


def downgrade() -> None:
    for t in reversed(PHASE1_TABLES):
        op.drop_table(t)

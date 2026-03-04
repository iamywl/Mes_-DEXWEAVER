"""baseline: v4.0 21 tables

Revision ID: 59d7a9d4a614
Revises:
Create Date: 2026-03-04 09:01:05.540697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59d7a9d4a614'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "users", "user_permissions", "items", "bom", "processes", "equipments",
    "routings", "equip_status_log", "production_plans", "work_orders",
    "work_results", "quality_standards", "inspections", "inspection_details",
    "defect_codes", "inventory", "inventory_transactions", "shipments",
    "defect_history", "equip_sensors", "ai_forecasts",
]


def upgrade() -> None:
    """기존 init.sql의 21개 테이블을 Alembic 관리하에 생성."""
    # 1. users
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(50), primary_key=True),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("role", sa.String(20), nullable=False, server_default="worker"),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("role IN ('admin','manager','worker','viewer')", name="ck_users_role"),
    )

    # 2. user_permissions
    op.create_table(
        "user_permissions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(50), sa.ForeignKey("users.user_id", ondelete="CASCADE")),
        sa.Column("menu", sa.String(100), nullable=False),
        sa.Column("can_read", sa.Boolean, server_default=sa.text("TRUE")),
        sa.Column("can_write", sa.Boolean, server_default=sa.text("FALSE")),
        sa.UniqueConstraint("user_id", "menu", name="uq_user_permissions_user_menu"),
    )

    # 3. items
    op.create_table(
        "items",
        sa.Column("item_code", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(20), nullable=False, server_default="RAW"),
        sa.Column("unit", sa.String(10), nullable=False, server_default="EA"),
        sa.Column("spec", sa.String(500)),
        sa.Column("safety_stock", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("category IN ('RAW','SEMI','PRODUCT')", name="ck_items_category"),
    )

    # 4. bom
    op.create_table(
        "bom",
        sa.Column("bom_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("parent_item", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("child_item", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("qty_per_unit", sa.Numeric(10, 4), nullable=False, server_default="1"),
        sa.Column("loss_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("parent_item", "child_item", name="uq_bom_parent_child"),
    )

    # 5. processes (equip_code FK added later due to circular ref)
    op.create_table(
        "processes",
        sa.Column("process_code", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("std_time_min", sa.Integer, nullable=False, server_default="0"),
        sa.Column("description", sa.Text),
        sa.Column("equip_code", sa.String(20)),
    )

    # 6. equipments
    op.create_table(
        "equipments",
        sa.Column("equip_code", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("process_code", sa.String(20)),
        sa.Column("capacity_per_hour", sa.Integer, nullable=False, server_default="100"),
        sa.Column("status", sa.String(20), nullable=False, server_default="STOP"),
        sa.Column("install_date", sa.Date),
        sa.CheckConstraint("status IN ('RUNNING','STOP','DOWN')", name="ck_equip_status"),
    )

    # 순환 참조 FK
    op.create_foreign_key("fk_proc_equip", "processes", "equipments", ["equip_code"], ["equip_code"])
    op.create_foreign_key("fk_equip_proc", "equipments", "processes", ["process_code"], ["process_code"])

    # 7. routings
    op.create_table(
        "routings",
        sa.Column("routing_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("process_code", sa.String(20), sa.ForeignKey("processes.process_code")),
        sa.Column("cycle_time", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("item_code", "seq", name="uq_routing_item_seq"),
    )

    # 8. equip_status_log
    op.create_table(
        "equip_status_log",
        sa.Column("log_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("equip_code", sa.String(20), sa.ForeignKey("equipments.equip_code")),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("worker_id", sa.String(50)),
        sa.Column("changed_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('RUNNING','STOP','DOWN')", name="ck_esl_status"),
    )

    # 9. production_plans
    op.create_table(
        "production_plans",
        sa.Column("plan_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("plan_qty", sa.Integer, nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("priority", sa.String(10), server_default="MID"),
        sa.Column("status", sa.String(20), server_default="WAIT"),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("priority IN ('HIGH','MID','LOW')", name="ck_plan_priority"),
        sa.CheckConstraint("status IN ('WAIT','PROGRESS','DONE')", name="ck_plan_status"),
    )

    # 10. work_orders
    op.create_table(
        "work_orders",
        sa.Column("wo_id", sa.String(30), primary_key=True),
        sa.Column("plan_id", sa.Integer, sa.ForeignKey("production_plans.plan_id")),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("work_date", sa.Date, nullable=False),
        sa.Column("equip_code", sa.String(20), sa.ForeignKey("equipments.equip_code")),
        sa.Column("plan_qty", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), server_default="WAIT"),
        sa.CheckConstraint("status IN ('WAIT','WORKING','DONE')", name="ck_wo_status"),
    )

    # 11. work_results
    op.create_table(
        "work_results",
        sa.Column("result_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("wo_id", sa.String(30), sa.ForeignKey("work_orders.wo_id")),
        sa.Column("good_qty", sa.Integer, nullable=False, server_default="0"),
        sa.Column("defect_qty", sa.Integer, nullable=False, server_default="0"),
        sa.Column("defect_code", sa.String(50)),
        sa.Column("worker_id", sa.String(50)),
        sa.Column("start_time", sa.TIMESTAMP),
        sa.Column("end_time", sa.TIMESTAMP),
    )

    # 12. quality_standards
    op.create_table(
        "quality_standards",
        sa.Column("standard_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column("check_type", sa.String(20), server_default="NUMERIC"),
        sa.Column("std_value", sa.Numeric(10, 4)),
        sa.Column("min_value", sa.Numeric(10, 4)),
        sa.Column("max_value", sa.Numeric(10, 4)),
        sa.Column("unit", sa.String(20)),
        sa.CheckConstraint("check_type IN ('NUMERIC','VISUAL','FUNCTIONAL')", name="ck_qs_type"),
    )

    # 13. inspections
    op.create_table(
        "inspections",
        sa.Column("inspection_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("inspect_type", sa.String(20), nullable=False),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("lot_no", sa.String(50)),
        sa.Column("judgment", sa.String(10), server_default="PASS"),
        sa.Column("inspected_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("inspector_id", sa.String(50)),
        sa.CheckConstraint("inspect_type IN ('INCOMING','PROCESS','OUTGOING')", name="ck_insp_type"),
        sa.CheckConstraint("judgment IN ('PASS','FAIL')", name="ck_insp_judgment"),
    )

    # 14. inspection_details
    op.create_table(
        "inspection_details",
        sa.Column("detail_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("inspection_id", sa.Integer, sa.ForeignKey("inspections.inspection_id", ondelete="CASCADE")),
        sa.Column("check_name", sa.String(100), nullable=False),
        sa.Column("measured_value", sa.Numeric(10, 4)),
        sa.Column("judgment", sa.String(10), server_default="PASS"),
        sa.CheckConstraint("judgment IN ('PASS','FAIL')", name="ck_insd_judgment"),
    )

    # 15. defect_codes
    op.create_table(
        "defect_codes",
        sa.Column("defect_code", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
    )

    # 16. inventory
    op.create_table(
        "inventory",
        sa.Column("inv_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("lot_no", sa.String(50), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False, server_default="0"),
        sa.Column("warehouse", sa.String(10), nullable=False),
        sa.Column("location", sa.String(20)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("item_code", "lot_no", "warehouse", name="uq_inv_item_lot_wh"),
    )

    # 17. inventory_transactions
    op.create_table(
        "inventory_transactions",
        sa.Column("tx_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slip_no", sa.String(30), nullable=False),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("lot_no", sa.String(50)),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("tx_type", sa.String(10), nullable=False),
        sa.Column("warehouse", sa.String(10)),
        sa.Column("location", sa.String(20)),
        sa.Column("ref_id", sa.String(50)),
        sa.Column("supplier", sa.String(100)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.CheckConstraint("tx_type IN ('IN','OUT','MOVE')", name="ck_tx_type"),
    )

    # 18. shipments
    op.create_table(
        "shipments",
        sa.Column("shipment_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("ship_date", sa.Date, nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("customer", sa.String(255)),
    )

    # 19. defect_history
    op.create_table(
        "defect_history",
        sa.Column("defect_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("item_code", sa.String(20), sa.ForeignKey("items.item_code")),
        sa.Column("equip_code", sa.String(20), sa.ForeignKey("equipments.equip_code")),
        sa.Column("recorded_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("temperature", sa.Numeric(6, 2)),
        sa.Column("pressure", sa.Numeric(6, 2)),
        sa.Column("speed", sa.Numeric(6, 2)),
        sa.Column("humidity", sa.Numeric(6, 2)),
        sa.Column("defect_count", sa.Integer, server_default="0"),
        sa.Column("total_count", sa.Integer, server_default="0"),
    )

    # 20. equip_sensors
    op.create_table(
        "equip_sensors",
        sa.Column("sensor_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("equip_code", sa.String(20), sa.ForeignKey("equipments.equip_code")),
        sa.Column("vibration", sa.Numeric(8, 4)),
        sa.Column("temperature", sa.Numeric(8, 4)),
        sa.Column("current_amp", sa.Numeric(8, 4)),
        sa.Column("recorded_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )

    # 21. ai_forecasts
    op.create_table(
        "ai_forecasts",
        sa.Column("forecast_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("item_code", sa.String(20)),
        sa.Column("equip_code", sa.String(20)),
        sa.Column("result_json", sa.JSON),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    """역순으로 테이블 삭제."""
    # 순환 참조 FK 먼저 삭제
    op.drop_constraint("fk_proc_equip", "processes", type_="foreignkey")
    op.drop_constraint("fk_equip_proc", "equipments", type_="foreignkey")

    for t in reversed(TABLES):
        op.drop_table(t)

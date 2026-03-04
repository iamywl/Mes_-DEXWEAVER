"""REQ-069: 커스텀 대시보드 빌더 — 위젯 레이아웃 CRUD."""

import json
import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def save_layout(data: dict, user_id: str) -> dict:
    """대시보드 레이아웃 저장."""
    layout_name = data.get("layout_name", "").strip()
    if not layout_name:
        return {"error": "layout_name은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        layout_id = data.get("layout_id")
        widgets = data.get("widgets", [])

        if layout_id:
            # 기존 레이아웃 업데이트
            cursor.execute(
                """UPDATE dashboard_layouts SET layout_name = %s,
                          layout_config = %s, is_shared = %s, updated_at = NOW()
                   WHERE layout_id = %s AND user_id = %s""",
                (layout_name, json.dumps(data.get("config", {})),
                 data.get("is_shared", False), layout_id, user_id),
            )
            # 기존 위젯 삭제 후 재생성
            cursor.execute("DELETE FROM dashboard_widgets WHERE layout_id = %s",
                           (layout_id,))
        else:
            cursor.execute(
                """INSERT INTO dashboard_layouts
                   (user_id, layout_name, is_preset, is_shared, layout_config)
                   VALUES (%s,%s,%s,%s,%s) RETURNING layout_id""",
                (user_id, layout_name, data.get("is_preset", False),
                 data.get("is_shared", False),
                 json.dumps(data.get("config", {}))),
            )
            layout_id = cursor.fetchone()[0]

        # 위젯 저장
        for w in widgets:
            cursor.execute(
                """INSERT INTO dashboard_widgets
                   (layout_id, widget_type, title, data_source, config,
                    position_x, position_y, width, height)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (layout_id, w.get("widget_type", "TABLE"),
                 w.get("title"), w.get("data_source", ""),
                 json.dumps(w.get("config", {})),
                 w.get("x", 0), w.get("y", 0),
                 w.get("w", 4), w.get("h", 3)),
            )

        conn.commit()
        cursor.close()
        return {"success": True, "layout_id": layout_id,
                "widgets_count": len(widgets)}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("대시보드 저장 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_layouts(user_id: str) -> dict:
    """사용자 대시보드 목록 (본인 + 공유)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            """SELECT layout_id, user_id, layout_name, is_preset, is_shared,
                      layout_config, created_at, updated_at
               FROM dashboard_layouts
               WHERE user_id = %s OR is_shared = TRUE OR is_preset = TRUE
               ORDER BY updated_at DESC""",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {"layout_id": r[0], "user_id": r[1], "layout_name": r[2],
                 "is_preset": r[3], "is_shared": r[4], "config": r[5],
                 "created_at": r[6].isoformat() if r[6] else None,
                 "updated_at": r[7].isoformat() if r[7] else None}
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def get_layout_detail(layout_id: int) -> dict:
    """대시보드 상세 (위젯 포함)."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """SELECT layout_id, user_id, layout_name, is_preset, is_shared,
                      layout_config FROM dashboard_layouts
               WHERE layout_id = %s""", (layout_id,))
        l = cursor.fetchone()
        if not l:
            cursor.close()
            return {"error": "레이아웃을 찾을 수 없습니다."}

        cursor.execute(
            """SELECT widget_id, widget_type, title, data_source, config,
                      position_x, position_y, width, height
               FROM dashboard_widgets WHERE layout_id = %s
               ORDER BY position_y, position_x""",
            (layout_id,),
        )
        widgets = cursor.fetchall()
        cursor.close()

        return {
            "layout_id": l[0], "user_id": l[1], "layout_name": l[2],
            "is_preset": l[3], "is_shared": l[4], "config": l[5],
            "widgets": [
                {"widget_id": w[0], "widget_type": w[1], "title": w[2],
                 "data_source": w[3], "config": w[4],
                 "x": w[5], "y": w[6], "w": w[7], "h": w[8]}
                for w in widgets
            ],
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def delete_layout(layout_id: int, user_id: str) -> dict:
    """대시보드 삭제."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM dashboard_layouts WHERE layout_id = %s AND user_id = %s",
            (layout_id, user_id),
        )
        if cursor.rowcount == 0:
            cursor.close()
            return {"error": "삭제할 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)

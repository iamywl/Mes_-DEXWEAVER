"""REQ-044: 노동 관리 — 작업자 스킬 매트릭스 (FN-058)."""

import logging
from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def get_worker_skills(process_code: str = None,
                            skill_level: str = None,
                            worker_id: str = None) -> dict:
    """FN-058: 작업자 스킬 매트릭스 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT ws.user_id, u.name, ws.process_code, ws.skill_level,
                        ws.certified, ws.cert_expiry, ws.updated_at
                 FROM worker_skills ws
                 LEFT JOIN users u ON ws.user_id = u.user_id
                 WHERE 1=1"""
        params = []
        if process_code:
            sql += " AND ws.process_code = %s"
            params.append(process_code)
        if skill_level:
            sql += " AND ws.skill_level = %s"
            params.append(skill_level)
        if worker_id:
            sql += " AND ws.user_id = %s"
            params.append(worker_id)
        sql += " ORDER BY ws.user_id, ws.process_code LIMIT 500"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()

        # 작업자별 그룹핑
        workers_map = {}
        for r in rows:
            uid = r[0]
            if uid not in workers_map:
                workers_map[uid] = {"worker_id": uid, "name": r[1] or uid, "skills": []}
            workers_map[uid]["skills"].append({
                "process_code": r[2], "skill_level": r[3],
                "certified": r[4],
                "cert_expiry": r[5].isoformat() if r[5] else None,
                "updated_at": r[6].isoformat() if r[6] else None,
            })

        # 공정별 요약
        summary = {}
        for r in rows:
            pc = r[2]
            lvl = r[3]
            if pc not in summary:
                summary[pc] = {"process_code": pc, "EXPERT": 0, "ADVANCED": 0,
                               "INTERMEDIATE": 0, "BEGINNER": 0}
            if lvl in summary[pc]:
                summary[pc][lvl] += 1

        cursor.close()
        return {
            "workers": list(workers_map.values()),
            "total": len(workers_map),
            "summary": {"by_process": list(summary.values())},
        }
    except Exception as e:
        log.error("스킬 매트릭스 조회 오류: %s", e)
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def upsert_worker_skill(data: dict) -> dict:
    """작업자 스킬 등록/수정."""
    user_id = data.get("user_id", "").strip()
    process_code = data.get("process_code", "").strip()
    skill_level = data.get("skill_level", "BEGINNER")

    if not user_id or not process_code:
        return {"error": "user_id, process_code는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO worker_skills (user_id, process_code, skill_level, certified, cert_expiry)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (user_id, process_code)
               DO UPDATE SET skill_level = EXCLUDED.skill_level,
                             certified = EXCLUDED.certified,
                             cert_expiry = EXCLUDED.cert_expiry,
                             updated_at = NOW()""",
            (user_id, process_code, skill_level,
             data.get("certified", False), data.get("cert_expiry")),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "user_id": user_id, "process_code": process_code,
                "skill_level": skill_level}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("스킬 등록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)

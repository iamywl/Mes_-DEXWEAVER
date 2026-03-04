"""REQ-043: 문서 관리 DMS — 문서 등록/조회/다운로드 (FN-056~057)."""

import logging
import os
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/mes_uploads")


async def create_document(data: dict, user_id: str = None) -> dict:
    """FN-056: 문서 등록 (메타데이터만 — 파일 업로드는 별도 엔드포인트)."""
    title = data.get("title", "").strip()
    if not title:
        return {"error": "title은 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT COUNT(*) FROM documents WHERE doc_code LIKE %s",
            (f"DOC-{today}-%",),
        )
        seq = (cursor.fetchone()[0] or 0) + 1
        doc_code = f"DOC-{today}-{seq:03d}"

        cursor.execute(
            """INSERT INTO documents
               (doc_code, doc_type, title, file_path, file_size, version,
                item_code, process_code, status, uploaded_by, description)
               VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 'DRAFT', %s, %s)
               RETURNING doc_id""",
            (doc_code, data.get("doc_type", "SOP"), title,
             data.get("file_path", ""), data.get("file_size", 0),
             data.get("item_code"), data.get("process_code"),
             user_id, data.get("description", "")),
        )
        doc_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return {"success": True, "doc_id": doc_id, "doc_code": doc_code}
    except Exception as e:
        if conn:
            conn.rollback()
        log.error("문서 등록 오류: %s", e)
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def upload_document_file(doc_id: int, file_content: bytes,
                                filename: str) -> dict:
    """파일 업로드 처리."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(filename)[1] if filename else ""
    stored_name = f"doc_{doc_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        return {"error": f"파일 저장 실패: {e}"}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET file_path = %s, file_size = %s WHERE doc_id = %s",
            (file_path, len(file_content), doc_id),
        )
        conn.commit()
        cursor.close()
        return {"success": True, "file_path": file_path, "file_size": len(file_content)}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)


async def get_documents(doc_type: str = None, item_code: str = None,
                        process_code: str = None, keyword: str = None,
                        status: str = None) -> dict:
    """FN-057: 문서 목록 조회."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        sql = """SELECT doc_id, doc_code, doc_type, title, file_path, file_size,
                        version, item_code, process_code, status, uploaded_by,
                        description, is_active, created_at
                 FROM documents WHERE is_active = TRUE"""
        params = []
        if doc_type:
            sql += " AND doc_type = %s"
            params.append(doc_type)
        if item_code:
            sql += " AND item_code = %s"
            params.append(item_code)
        if process_code:
            sql += " AND process_code = %s"
            params.append(process_code)
        if status:
            sql += " AND status = %s"
            params.append(status)
        if keyword:
            sql += " AND (title ILIKE %s OR description ILIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        sql += " ORDER BY created_at DESC LIMIT 200"

        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        return {
            "items": [
                {
                    "doc_id": r[0], "doc_code": r[1], "doc_type": r[2],
                    "title": r[3], "file_path": r[4],
                    "file_size_kb": round(r[5] / 1024, 1) if r[5] else 0,
                    "version": r[6], "item_code": r[7], "process_code": r[8],
                    "status": r[9], "uploaded_by": r[10], "description": r[11],
                    "created_at": r[13].isoformat() if r[13] else None,
                }
                for r in rows
            ]
        }
    except Exception:
        return {"error": "조회 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)


async def approve_document(doc_id: int) -> dict:
    """문서 승인."""
    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE documents SET status = 'APPROVED' WHERE doc_id = %s AND status = 'DRAFT'",
            (doc_id,),
        )
        if cursor.rowcount == 0:
            cursor.close()
            return {"error": "승인할 수 없습니다."}
        conn.commit()
        cursor.close()
        return {"success": True, "doc_id": doc_id, "status": "APPROVED"}
    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}
    finally:
        if conn:
            release_conn(conn)

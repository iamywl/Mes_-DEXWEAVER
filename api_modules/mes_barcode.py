"""REQ-052: 바코드/QR코드 생성 및 스캔 처리."""

import base64
import io
import logging
from datetime import datetime

from api_modules.database import get_conn, release_conn

log = logging.getLogger(__name__)


async def generate_barcode(data: dict) -> dict:
    """바코드/QR코드 이미지 생성 (Base64 반환).

    body: { "content": "LOT-20260301-001", "format": "qr"|"code128", "label": "optional" }
    """
    content = data.get("content", "").strip()
    fmt = data.get("format", "qr").lower()
    label = data.get("label", "")

    if not content:
        return {"error": "content는 필수입니다."}

    try:
        if fmt == "qr":
            return _generate_qr(content, label)
        else:
            return _generate_barcode(content, fmt, label)
    except Exception as e:
        log.error("바코드 생성 오류: %s", e)
        return {"error": f"바코드 생성 실패: {str(e)}"}


def _generate_qr(content: str, label: str) -> dict:
    """QR코드 생성."""
    try:
        import qrcode
    except ImportError:
        return {"error": "qrcode 라이브러리가 설치되지 않았습니다."}

    qr = qrcode.QRCode(version=1, box_size=10, border=4,
                        error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {
        "success": True,
        "format": "qr",
        "content": content,
        "label": label,
        "image_base64": b64,
        "mime_type": "image/png",
    }


def _generate_barcode(content: str, fmt: str, label: str) -> dict:
    """1D 바코드 생성 (Code128 등)."""
    try:
        import barcode as barcode_lib
        from barcode.writer import ImageWriter
    except ImportError:
        return {"error": "python-barcode 라이브러리가 설치되지 않았습니다."}

    fmt_map = {"code128": "code128", "ean13": "ean13", "code39": "code39"}
    bc_type = fmt_map.get(fmt, "code128")

    try:
        bc_class = barcode_lib.get_barcode_class(bc_type)
    except barcode_lib.errors.BarcodeNotFoundError:
        return {"error": f"지원하지 않는 바코드 형식: {fmt}"}

    bc = bc_class(content, writer=ImageWriter())
    buf = io.BytesIO()
    bc.write(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {
        "success": True,
        "format": bc_type,
        "content": content,
        "label": label,
        "image_base64": b64,
        "mime_type": "image/png",
    }


async def scan_barcode(data: dict) -> dict:
    """바코드/QR 스캔 결과 처리 — 스캔된 코드를 해석하여 관련 정보 반환.

    body: { "code": "LOT-20260301-001", "context": "inventory"|"work"|"quality" }
    """
    code = data.get("code", "").strip()
    context = data.get("context", "inventory")

    if not code:
        return {"error": "code는 필수입니다."}

    conn = None
    try:
        conn = get_conn()
        if not conn:
            return {"error": "데이터베이스 연결에 실패했습니다."}
        cursor = conn.cursor()

        result = {"code": code, "context": context, "found": False}

        # LOT 번호로 해석 시도
        if code.startswith("LOT-") or context == "inventory":
            cursor.execute(
                "SELECT lot_no, item_code, warehouse, qty, status "
                "FROM inventory WHERE lot_no = %s", (code,)
            )
            row = cursor.fetchone()
            if row:
                result.update({
                    "found": True, "type": "LOT",
                    "lot_no": row[0], "item_code": row[1],
                    "warehouse": row[2], "qty": float(row[3]) if row[3] else 0,
                    "status": row[4],
                })

        # 작업지시 번호
        if not result["found"] and (code.startswith("WO-") or context == "work"):
            cursor.execute(
                "SELECT wo_no, item_code, plan_qty, status "
                "FROM work_orders WHERE wo_no = %s", (code,)
            )
            row = cursor.fetchone()
            if row:
                result.update({
                    "found": True, "type": "WORK_ORDER",
                    "wo_no": row[0], "item_code": row[1],
                    "plan_qty": float(row[2]) if row[2] else 0,
                    "status": row[3],
                })

        # 품목 코드
        if not result["found"]:
            cursor.execute(
                "SELECT item_code, item_name, item_type, unit "
                "FROM items WHERE item_code = %s", (code,)
            )
            row = cursor.fetchone()
            if row:
                result.update({
                    "found": True, "type": "ITEM",
                    "item_code": row[0], "item_name": row[1],
                    "item_type": row[2], "unit": row[3],
                })

        cursor.close()
        return result
    except Exception as e:
        log.error("바코드 스캔 처리 오류: %s", e)
        return {"error": "스캔 처리 중 오류가 발생했습니다."}
    finally:
        if conn:
            release_conn(conn)

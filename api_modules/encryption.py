"""NFR-012: AES-256 데이터 암호화 — PII/감사로그/전자서명 at-rest 암호화.

사용법:
    from api_modules.encryption import encrypt, decrypt
    encrypted = encrypt("민감 데이터")
    original = decrypt(encrypted)
"""

import base64
import hashlib
import os
import logging

log = logging.getLogger(__name__)

# AES-256 key from environment (32 bytes = 256 bits)
_KEY_ENV = os.getenv("MES_ENCRYPT_KEY", "dexweaver-mes-default-key-2026!")
_KEY = hashlib.sha256(_KEY_ENV.encode()).digest()

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False
    log.warning("cryptography 라이브러리 미설치 — 암호화 비활성화 (평문 저장)")


def encrypt(plaintext: str) -> str:
    """AES-256-GCM 암호화 → Base64 인코딩 문자열.

    라이브러리 미설치 시 평문 반환 (graceful fallback).
    """
    if not plaintext:
        return plaintext
    if not _HAS_CRYPTO:
        return plaintext

    nonce = os.urandom(12)  # 96-bit nonce for GCM
    aesgcm = AESGCM(_KEY)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Format: base64(nonce + ciphertext)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(encrypted: str) -> str:
    """AES-256-GCM 복호화.

    라이브러리 미설치 시 또는 복호화 실패 시 원본 반환.
    """
    if not encrypted:
        return encrypted
    if not _HAS_CRYPTO:
        return encrypted

    try:
        raw = base64.b64decode(encrypted)
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(_KEY)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception:
        # Not encrypted or different key — return as-is
        return encrypted


def is_encrypted(value: str) -> bool:
    """Check if value appears to be AES-GCM encrypted (base64, min length)."""
    if not value or len(value) < 40:
        return False
    try:
        raw = base64.b64decode(value)
        return len(raw) > 12  # nonce(12) + at least some ciphertext
    except Exception:
        return False

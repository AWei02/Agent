"""Encryption for Feishu App Secrets stored in the platform database."""

from __future__ import annotations

import os
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


class FeishuSecretError(ValueError):
    pass


def _fernet() -> Fernet:
    key = os.getenv("FEISHU_APP_SECRET_ENCRYPTION_KEY", "").strip()
    if not key:
        # Existing deployments already require this internal Worker secret.
        # Deriving a purpose-scoped Fernet key keeps application onboarding
        # usable without adding another mandatory environment variable.
        internal_secret = os.getenv("FEISHU_INTERNAL_AUTH_SECRET", "").strip()
        if internal_secret:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(f"feishu-app-secret:{internal_secret}".encode()).digest()
            ).decode()
    if not key:
        raise FeishuSecretError("FEISHU_INTERNAL_AUTH_SECRET or FEISHU_APP_SECRET_ENCRYPTION_KEY must be configured")
    try:
        return Fernet(key.encode())
    except (TypeError, ValueError) as exc:
        raise FeishuSecretError("FEISHU_APP_SECRET_ENCRYPTION_KEY is invalid") from exc


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise FeishuSecretError("Unable to decrypt Feishu App Secret") from exc

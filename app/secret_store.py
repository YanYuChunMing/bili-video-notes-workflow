import base64
import ctypes
import os
import sqlite3
import sys
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SECRET_DEEPSEEK_API_KEY = "deepseek_api_key"
SCHEMA_VERSION = 1


class SecretStoreError(RuntimeError):
    pass


@dataclass
class SecretStatus:
    available: bool
    scheme: str
    db_path: str
    message: str = ""


def _running_in_docker() -> bool:
    return Path("/.dockerenv").exists() or os.getenv("BILI_IN_DOCKER") == "1"


def default_db_path() -> Path:
    configured = os.getenv("BILI_SECRET_DB")
    if configured:
        return Path(configured)
    if _running_in_docker():
        return Path("/app/secrets/local_secrets.sqlite3")
    return Path("temp/local_secrets.sqlite3")


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS secrets (
            name TEXT PRIMARY KEY,
            encrypted_value BLOB NOT NULL,
            scheme TEXT NOT NULL,
            salt BLOB,
            nonce BLOB,
            updated_at TEXT NOT NULL,
            schema_version INTEGER NOT NULL
        )
        """
    )
    return conn


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _bytes_to_blob(data: bytes) -> _DataBlob:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    blob._buffer = buffer
    return blob


def _blob_to_bytes(blob: _DataBlob) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob.pbData)


def _dpapi_protect(value: str) -> bytes:
    if sys.platform != "win32":
        raise SecretStoreError("DPAPI 仅在 Windows 可用。")
    in_blob = _bytes_to_blob(value.encode("utf-8"))
    out_blob = _DataBlob()
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise SecretStoreError("Windows DPAPI 加密失败。")
    return _blob_to_bytes(out_blob)


def _dpapi_unprotect(value: bytes) -> str:
    if sys.platform != "win32":
        raise SecretStoreError("DPAPI 仅在 Windows 可用。")
    in_blob = _bytes_to_blob(value)
    out_blob = _DataBlob()
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise SecretStoreError("Windows DPAPI 解密失败。")
    return _blob_to_bytes(out_blob).decode("utf-8")


def _get_passphrase(passphrase: str | None = None) -> str:
    value = passphrase or os.getenv("BILI_SECRET_PASSPHRASE", "")
    if not value:
        raise SecretStoreError(
            "当前环境不能使用 DPAPI；请设置 BILI_SECRET_PASSPHRASE 后再保存密钥。"
        )
    return value


def _fernet_from_passphrase(passphrase: str, salt: bytes):
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError as exc:
        raise SecretStoreError(
            "缺少 cryptography，无法在 Docker/Linux 中加密保存密钥。"
        ) from exc

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))
    return Fernet(key)


def _passphrase_encrypt(value: str, passphrase: str | None = None) -> tuple[bytes, bytes]:
    salt = os.urandom(16)
    fernet = _fernet_from_passphrase(_get_passphrase(passphrase), salt)
    return fernet.encrypt(value.encode("utf-8")), salt


def _passphrase_decrypt(value: bytes, salt: bytes, passphrase: str | None = None) -> str:
    fernet = _fernet_from_passphrase(_get_passphrase(passphrase), salt)
    return fernet.decrypt(value).decode("utf-8")


def _scheme_for_current_platform() -> str:
    return "dpapi" if sys.platform == "win32" and not _running_in_docker() else "passphrase"


def get_status(name: str = SECRET_DEEPSEEK_API_KEY, db_path: Path | None = None) -> SecretStatus:
    path = db_path or default_db_path()
    if not path.exists():
        return SecretStatus(False, "", str(path), "本地密钥数据库不存在。")
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT scheme FROM secrets WHERE name = ?",
            (name,),
        ).fetchone()
    if not row:
        return SecretStatus(False, "", str(path), "本地数据库中没有该密钥。")
    return SecretStatus(True, row[0], str(path), "本地数据库已保存。")


def has_secret(name: str = SECRET_DEEPSEEK_API_KEY, db_path: Path | None = None) -> bool:
    return get_status(name, db_path).available


def save_secret(
    name: str,
    value: str,
    *,
    passphrase: str | None = None,
    db_path: Path | None = None,
) -> None:
    if not value:
        raise SecretStoreError("密钥为空，未保存。")

    scheme = _scheme_for_current_platform()
    salt = None
    if scheme == "dpapi":
        encrypted = _dpapi_protect(value)
    else:
        encrypted, salt = _passphrase_encrypt(value, passphrase)

    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO secrets (name, encrypted_value, scheme, salt, nonce, updated_at, schema_version)
            VALUES (?, ?, ?, ?, NULL, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                encrypted_value = excluded.encrypted_value,
                scheme = excluded.scheme,
                salt = excluded.salt,
                nonce = excluded.nonce,
                updated_at = excluded.updated_at,
                schema_version = excluded.schema_version
            """,
            (
                name,
                encrypted,
                scheme,
                salt,
                datetime.now().isoformat(timespec="seconds"),
                SCHEMA_VERSION,
            ),
        )


def load_secret(
    name: str = SECRET_DEEPSEEK_API_KEY,
    *,
    passphrase: str | None = None,
    db_path: Path | None = None,
) -> str:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT encrypted_value, scheme, salt FROM secrets WHERE name = ?",
            (name,),
        ).fetchone()

    if not row:
        return ""

    encrypted, scheme, salt = row
    if scheme == "dpapi":
        return _dpapi_unprotect(encrypted)
    if scheme == "passphrase":
        return _passphrase_decrypt(encrypted, salt, passphrase)
    raise SecretStoreError(f"未知密钥加密方案：{scheme}")


def delete_secret(name: str = SECRET_DEEPSEEK_API_KEY, db_path: Path | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM secrets WHERE name = ?", (name,))

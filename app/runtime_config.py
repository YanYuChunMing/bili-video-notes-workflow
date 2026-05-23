from copy import deepcopy

try:
    import streamlit as st
except Exception:  # pragma: no cover - CLI path
    st = None

from app.secret_store import SECRET_DEEPSEEK_API_KEY, SecretStoreError, load_secret
from src import config_loader


def _session_api_key() -> str:
    if st is None:
        return ""
    try:
        return st.session_state.get("deepseek_api_key", "")
    except Exception:
        return ""


def _session_passphrase() -> str:
    if st is None:
        return ""
    try:
        return st.session_state.get("secret_passphrase", "")
    except Exception:
        return ""


def inject_runtime_secrets(config: dict, *, passphrase: str | None = None) -> dict:
    runtime = deepcopy(config)
    runtime.setdefault("deepseek", {})

    api_key = _session_api_key()
    if not api_key:
        try:
            api_key = load_secret(
                SECRET_DEEPSEEK_API_KEY,
                passphrase=passphrase or _session_passphrase() or None,
            )
        except SecretStoreError:
            api_key = ""

    runtime["deepseek"]["api_key"] = api_key
    return runtime


def load_runtime_config(config_path: str = "config.toml", *, passphrase: str | None = None) -> dict:
    return inject_runtime_secrets(config_loader.load_config(config_path), passphrase=passphrase)

import os
import json
from cryptography.fernet import Fernet
from flask import current_app, request
from app.extensions import db
from app.models import SiteSetting, ActivityLog


def _get_fernet():
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        # Derive a stable key from SECRET_KEY so behaviour is deterministic per-deployment
        # if ENCRYPTION_KEY isn't explicitly provided (still recommended to set it).
        import base64
        import hashlib
        secret = current_app.config["SECRET_KEY"].encode("utf-8")
        derived = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
        key = derived
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)


def get_setting(key, default=None):
    row = SiteSetting.query.filter_by(key=key).first()
    if not row:
        return default
    if row.is_encrypted and row.value:
        try:
            return _get_fernet().decrypt(row.value.encode("utf-8")).decode("utf-8")
        except Exception:  # noqa: BLE001
            return default
    return row.value


def set_setting(key, value, encrypted=False):
    row = SiteSetting.query.filter_by(key=key).first()
    stored_value = value
    if encrypted and value:
        stored_value = _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")
    if row:
        row.value = stored_value
        row.is_encrypted = encrypted
    else:
        row = SiteSetting(key=key, value=stored_value, is_encrypted=encrypted)
        db.session.add(row)
    db.session.commit()
    return row


def get_smtp_settings():
    return {
        "server": get_setting("smtp_server", ""),
        "port": get_setting("smtp_port", "587"),
        "email": get_setting("smtp_email", ""),
        "password": get_setting("smtp_password", ""),
        "encryption": get_setting("smtp_encryption", "TLS"),
    }


def save_smtp_settings(server, port, email, password, encryption):
    set_setting("smtp_server", server)
    set_setting("smtp_port", str(port))
    set_setting("smtp_email", email)
    set_setting("smtp_password", password, encrypted=True)
    set_setting("smtp_encryption", encryption)


def get_theme_settings():
    raw = get_setting("theme_json")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return {
        "primary": "#0b3d91",
        "secondary": "#ffffff",
        "accent": "#4a90d9",
        "dark_mode_enabled": False,
        "rounded_cards": True,
    }


def save_theme_settings(theme_dict):
    set_setting("theme_json", json.dumps(theme_dict))


def log_activity(action, user_id=None, target_type=None, target_id=None, details=None):
    try:
        ip = request.remote_addr if request else None
    except RuntimeError:
        ip = None
    entry = ActivityLog(
        user_id=user_id, action=action, target_type=target_type,
        target_id=target_id, details=details, ip_address=ip,
    )
    db.session.add(entry)
    db.session.commit()

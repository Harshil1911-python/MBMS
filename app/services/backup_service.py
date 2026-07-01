import os
import shutil
import zipfile
from datetime import datetime
from flask import current_app


def create_backup_zip():
    """Creates a ZIP containing the SQLite DB file (if used) and all uploads/qr/pdf assets."""
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    backup_dir = os.path.join(basedir, "instance", "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
        if db_uri.startswith("sqlite:///"):
            db_file = db_uri.replace("sqlite:///", "", 1)
            if os.path.exists(db_file):
                zf.write(db_file, arcname="database/mbms.db")

        static_folder = current_app.static_folder
        for sub in ("uploads", "qr", "generated_pdf"):
            folder = os.path.join(static_folder, sub)
            if not os.path.exists(folder):
                continue
            for root, _dirs, files in os.walk(folder):
                for f in files:
                    full = os.path.join(root, f)
                    arcname = os.path.join("assets", os.path.relpath(full, static_folder))
                    zf.write(full, arcname=arcname)

    return zip_path


def list_backups():
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    backup_dir = os.path.join(basedir, "instance", "backups")
    if not os.path.exists(backup_dir):
        return []
    files = sorted(os.listdir(backup_dir), reverse=True)
    return [f for f in files if f.endswith(".zip")]

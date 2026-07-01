import os
import uuid
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
from flask import current_app


def _allowed(filename, allowed_ext):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_ext


def _unique_name(original_filename):
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "bin"
    return f"{uuid.uuid4().hex}.{ext}"


def save_photo(file_storage, subfolder="photos"):
    """Save + compress a profile photo, returns (relative_path, thumb_relative_path) or (None, None)."""
    if not file_storage or not file_storage.filename:
        return None, None
    filename = secure_filename(file_storage.filename)
    if not _allowed(filename, current_app.config["ALLOWED_IMAGE_EXT"]):
        return None, None

    folder = current_app.config["PHOTO_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    new_name = _unique_name(filename)
    full_path = os.path.join(folder, new_name)

    img = Image.open(file_storage.stream)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    # Resize main image (cap at 1600px on the long edge) & compress
    img.thumbnail((1600, 1600))
    img.save(full_path, "JPEG", quality=85, optimize=True)

    # Thumbnail
    thumb_name = f"thumb_{new_name}"
    thumb_path = os.path.join(folder, thumb_name)
    thumb_img = img.copy()
    thumb_img.thumbnail((320, 320))
    thumb_img.save(thumb_path, "JPEG", quality=80, optimize=True)

    rel = f"uploads/photos/{new_name}"
    rel_thumb = f"uploads/photos/{thumb_name}"
    return rel, rel_thumb


def save_document(file_storage, subfolder="documents"):
    if not file_storage or not file_storage.filename:
        return None, None
    filename = secure_filename(file_storage.filename)
    if not _allowed(filename, current_app.config["ALLOWED_DOC_EXT"]):
        return None, None

    folder = current_app.config["DOCUMENT_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    new_name = _unique_name(filename)
    full_path = os.path.join(folder, new_name)
    file_storage.save(full_path)
    return f"uploads/documents/{new_name}", filename


def save_kundli(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    filename = secure_filename(file_storage.filename)
    if not _allowed(filename, current_app.config["ALLOWED_DOC_EXT"]):
        return None
    folder = current_app.config["KUNDLI_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    new_name = _unique_name(filename)
    full_path = os.path.join(folder, new_name)
    file_storage.save(full_path)
    return f"uploads/kundli/{new_name}"


def delete_file_safe(relative_path):
    if not relative_path:
        return
    try:
        full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "..", relative_path)
        full_path = os.path.normpath(os.path.join(current_app.static_folder, relative_path))
        if os.path.exists(full_path):
            os.remove(full_path)
    except OSError:
        pass

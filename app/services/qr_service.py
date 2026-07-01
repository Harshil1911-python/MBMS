import os
import qrcode
from flask import current_app, url_for


def generate_profile_qr(profile):
    """Generates a QR code pointing to the public read-only profile page."""
    folder = current_app.config["QR_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    public_url = url_for("public.profile_view", public_id=profile.public_id, _external=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0b3d91", back_color="white")

    filename = f"{profile.public_id}.png"
    full_path = os.path.join(folder, filename)
    img.save(full_path)

    return f"qr/{filename}"

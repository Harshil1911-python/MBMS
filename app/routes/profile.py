from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Profile, Photo, Document
from app.forms.profile_forms import ProfileForm
from app.utils.decorators import candidate_required
from app.utils.helpers import generate_profile_code, find_possible_duplicates
from app.services.upload_service import save_photo, save_document, save_kundli, delete_file_safe
from app.services.settings_service import log_activity

profile_bp = Blueprint("profile", __name__, template_folder="../templates/profile")

DOC_FIELD_MAP = {
    "aadhar_doc": "aadhar",
    "passport_doc": "passport",
    "pan_doc": "pan",
    "driving_license_doc": "driving_license",
    "other_doc": "other",
}


@profile_bp.route("/register", methods=["GET", "POST"])
@login_required
@candidate_required
def create_or_edit():
    profile = current_user.profile
    editable = profile is None or profile.is_editable

    if profile and not editable:
        flash("Your profile has been approved and is now read-only. Contact admin for changes.", "info")

    form = ProfileForm(obj=profile)
    if request.method == "GET" and profile is None:
        form.candidate_type.data = current_user.role
        form.email.data = current_user.email
        form.phone.data = current_user.phone

    if form.validate_on_submit():
        if not editable:
            abort(403)

        is_new = profile is None
        if is_new:
            profile = Profile(user_id=current_user.id)

        form.populate_obj(profile)
        # populate_obj also tries to set file fields; clean those (they're not model columns)
        profile.kundli_available = form.kundli_available.data

        if is_new:
            db.session.add(profile)
            db.session.flush()
            profile.profile_code = generate_profile_code(profile)

        # Photos
        existing_count = len(profile.photos)
        uploaded_files = [f for f in (form.photo_files.data or []) if f and getattr(f, "filename", "")]
        for f in uploaded_files:
            rel, thumb = save_photo(f)
            if rel:
                photo = Photo(profile_id=profile.id, file_path=rel, thumbnail_path=thumb,
                               sort_order=existing_count)
                db.session.add(photo)
                existing_count += 1

        db.session.flush()
        if not profile.featured_photo_path and profile.photos:
            profile.featured_photo_path = profile.photos[0].file_path
        elif not profile.featured_photo_path and uploaded_files:
            first_photo = Photo.query.filter_by(profile_id=profile.id).order_by(Photo.id).first()
            if first_photo:
                profile.featured_photo_path = first_photo.file_path
                first_photo.is_featured = True

        # Documents
        for field_name, doc_type in DOC_FIELD_MAP.items():
            file_storage = getattr(form, field_name).data
            if file_storage and getattr(file_storage, "filename", ""):
                rel, original = save_document(file_storage)
                if rel:
                    db.session.add(Document(profile_id=profile.id, doc_type=doc_type,
                                             file_path=rel, original_filename=original))

        if form.kundli_file.data and getattr(form.kundli_file.data, "filename", ""):
            kundli_rel = save_kundli(form.kundli_file.data)
            if kundli_rel:
                db.session.add(Document(profile_id=profile.id, doc_type="kundli", file_path=kundli_rel))
                profile.kundli_available = True

        total_photos = len(profile.photos) + len(uploaded_files) if is_new else len(profile.photos)
        if total_photos < current_app.config["MIN_PHOTOS"] and is_new:
            flash(f"Please upload at least {current_app.config['MIN_PHOTOS']} photos. "
                  f"You can add more later before approval.", "warning")

        profile.approval_status = "pending" if profile.approval_status != "approved" else profile.approval_status
        db.session.commit()

        log_activity("profile_saved", user_id=current_user.id, target_type="profile", target_id=profile.id)

        dupes = find_possible_duplicates(profile)
        if dupes:
            flash(f"Note: {len(dupes)} possible duplicate profile(s) detected — admin will review.", "warning")

        flash("Biodata saved successfully! It will be reviewed by our admin team.", "success")
        return redirect(url_for("profile.create_or_edit"))

    return render_template("profile/register_form.html", form=form, profile=profile, editable=editable)


@profile_bp.route("/my-profile")
@login_required
@candidate_required
def my_profile():
    if not current_user.profile:
        return redirect(url_for("profile.create_or_edit"))
    return render_template("profile/my_profile.html", profile=current_user.profile)


@profile_bp.route("/photo/<int:photo_id>/delete", methods=["POST"])
@login_required
@candidate_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if photo.profile.user_id != current_user.id:
        abort(403)
    if not photo.profile.is_editable:
        abort(403)
    delete_file_safe(photo.file_path)
    delete_file_safe(photo.thumbnail_path)
    was_featured = photo.profile.featured_photo_path == photo.file_path
    db.session.delete(photo)
    db.session.flush()
    if was_featured:
        remaining = Photo.query.filter_by(profile_id=photo.profile_id).order_by(Photo.sort_order).first()
        photo.profile.featured_photo_path = remaining.file_path if remaining else None
    db.session.commit()
    flash("Photo removed.", "info")
    return redirect(url_for("profile.create_or_edit"))


@profile_bp.route("/photo/<int:photo_id>/feature", methods=["POST"])
@login_required
@candidate_required
def feature_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    if photo.profile.user_id != current_user.id:
        abort(403)
    for p in photo.profile.photos:
        p.is_featured = False
    photo.is_featured = True
    photo.profile.featured_photo_path = photo.file_path
    db.session.commit()
    flash("Featured photo updated.", "success")
    return redirect(url_for("profile.create_or_edit"))

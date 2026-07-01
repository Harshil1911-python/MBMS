import os
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for, flash, request,
                    send_file, current_app, jsonify, abort)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import (User, Profile, Photo, Document, ActivityLog, LoginLog,
                         SiteSetting, Announcement, Testimonial, ContactMessage)
from app.forms.auth_forms import AdminCreateUserForm, ResetPasswordForm
from app.forms.profile_forms import AdminReviewForm, SearchFilterForm
from app.forms.settings_forms import SMTPSettingsForm, ThemeSettingsForm, AnnouncementForm, SiteSettingsForm
from app.utils.decorators import admin_required
from app.utils.helpers import apply_search_filters, find_possible_duplicates
from app.services.settings_service import (get_smtp_settings, save_smtp_settings,
                                            get_theme_settings, save_theme_settings, log_activity,
                                            get_setting, set_setting)
from app.services.csv_service import export_profiles_csv, export_profiles_excel, import_profiles_csv
from app.services.backup_service import create_backup_zip, list_backups
from app.services.qr_service import generate_profile_qr

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


# ---------------------------------------------------------------- Dashboard
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_brides": Profile.query.filter_by(candidate_type="bride", is_deleted=False).count(),
        "total_grooms": Profile.query.filter_by(candidate_type="groom", is_deleted=False).count(),
        "pending": Profile.query.filter_by(approval_status="pending", is_deleted=False).count(),
        "approved": Profile.query.filter_by(approval_status="approved", is_deleted=False).count(),
        "rejected": Profile.query.filter_by(approval_status="rejected", is_deleted=False).count(),
        "suspended": Profile.query.filter_by(approval_status="suspended", is_deleted=False).count(),
        "members": User.query.filter_by(role="member").count(),
        "admins": User.query.filter_by(role="admin").count(),
        "total_users": User.query.count(),
    }

    recent_profiles = (Profile.query.filter_by(is_deleted=False)
                        .order_by(Profile.created_at.desc()).limit(10).all())

    since = datetime.utcnow() - timedelta(days=180)
    recent_for_chart = (Profile.query.filter(Profile.created_at >= since, Profile.is_deleted.is_(False))
                         .with_entities(Profile.created_at).all())
    month_counts = {}
    for (created_at,) in recent_for_chart:
        key = created_at.strftime("%Y-%m")
        month_counts[key] = month_counts.get(key, 0) + 1
    sorted_months = sorted(month_counts.keys())
    monthly_chart = {"labels": sorted_months, "values": [month_counts[m] for m in sorted_months]}

    education_raw = (db.session.query(Profile.qualification, func.count(Profile.id))
                      .filter(Profile.qualification.isnot(None), Profile.is_deleted.is_(False))
                      .group_by(Profile.qualification).order_by(func.count(Profile.id).desc()).limit(6).all())
    education_chart = {"labels": [e or "Unspecified" for e, _c in education_raw],
                        "values": [c for _e, c in education_raw]}

    occupation_raw = (db.session.query(Profile.occupation, func.count(Profile.id))
                       .filter(Profile.occupation.isnot(None), Profile.is_deleted.is_(False))
                       .group_by(Profile.occupation).order_by(func.count(Profile.id).desc()).limit(6).all())
    occupation_chart = {"labels": [o or "Unspecified" for o, _c in occupation_raw],
                         "values": [c for _o, c in occupation_raw]}

    all_profiles = Profile.query.filter_by(is_deleted=False).all()
    age_buckets = {"18-24": 0, "25-30": 0, "31-36": 0, "37-45": 0, "46+": 0}
    for p in all_profiles:
        age = p.age
        if age is None:
            continue
        if age <= 24:
            age_buckets["18-24"] += 1
        elif age <= 30:
            age_buckets["25-30"] += 1
        elif age <= 36:
            age_buckets["31-36"] += 1
        elif age <= 45:
            age_buckets["37-45"] += 1
        else:
            age_buckets["46+"] += 1
    age_chart = {"labels": list(age_buckets.keys()), "values": list(age_buckets.values())}

    income_buckets = {"<3L": 0, "3-6L": 0, "6-10L": 0, "10-20L": 0, "20L+": 0}
    for p in all_profiles:
        inc = p.income_yearly or 0
        if inc == 0:
            continue
        if inc < 300000:
            income_buckets["<3L"] += 1
        elif inc < 600000:
            income_buckets["3-6L"] += 1
        elif inc < 1000000:
            income_buckets["6-10L"] += 1
        elif inc < 2000000:
            income_buckets["10-20L"] += 1
        else:
            income_buckets["20L+"] += 1
    income_chart = {"labels": list(income_buckets.keys()), "values": list(income_buckets.values())}

    return render_template("admin/dashboard.html", stats=stats, recent_profiles=recent_profiles,
                            monthly_chart=monthly_chart, education_chart=education_chart,
                            occupation_chart=occupation_chart, age_chart=age_chart, income_chart=income_chart)


# ---------------------------------------------------------------- User Management
@admin_bp.route("/users")
@login_required
@admin_required
def users_list():
    role = request.args.get("role", "")
    q = request.args.get("q", "")
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if q:
        query = query.filter(db.or_(User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template("admin/users_list.html", pagination=pagination, users=pagination.items,
                            role=role, q=q)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists.", "danger")
        else:
            user = User(full_name=form.full_name.data.strip(), email=email,
                        phone=form.phone.data.strip() if form.phone.data else None,
                        role=form.role.data, status="active",
                        created_by_id=current_user.id, must_change_password=True)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            log_activity("create_user", user_id=current_user.id, target_type="user", target_id=user.id,
                         details=f"role={user.role}")
            flash(f"User {user.full_name} created successfully.", "success")
            return redirect(url_for("admin.users_list"))
    return render_template("admin/user_form.html", form=form, title="Create User")


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@login_required
@admin_required
def suspend_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot suspend your own account.", "danger")
        return redirect(url_for("admin.users_list"))
    user.status = "suspended"
    db.session.commit()
    log_activity("suspend_user", user_id=current_user.id, target_type="user", target_id=user.id)
    flash(f"{user.full_name} has been suspended.", "warning")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@login_required
@admin_required
def activate_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "active"
    db.session.commit()
    log_activity("activate_user", user_id=current_user.id, target_type="user", target_id=user.id)
    flash(f"{user.full_name} has been activated.", "success")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users_list"))
    if user.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
        flash("Cannot delete the last remaining admin.", "danger")
        return redirect(url_for("admin.users_list"))
    user.status = "deleted"
    db.session.commit()
    log_activity("delete_user", user_id=current_user.id, target_type="user", target_id=user.id)
    flash(f"{user.full_name} has been deleted.", "info")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        user.must_change_password = True
        db.session.commit()
        log_activity("reset_password", user_id=current_user.id, target_type="user", target_id=user.id)
        flash(f"Password reset for {user.full_name}.", "success")
        return redirect(url_for("admin.users_list"))
    return render_template("admin/reset_password.html", form=form, user=user)


# ---------------------------------------------------------------- Profile Management
@admin_bp.route("/profiles")
@login_required
@admin_required
def profiles_list():
    status = request.args.get("status", "")
    form = SearchFilterForm(request.args)
    query = Profile.query.filter_by(is_deleted=False)
    if status:
        query = query.filter_by(approval_status=status)
    query = apply_search_filters(query, request.args)
    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=current_app.config["PROFILES_PER_PAGE"], error_out=False)
    return render_template("admin/profiles_list.html", pagination=pagination, profiles=pagination.items,
                            status=status, form=form)


@admin_bp.route("/profiles/<public_id>")
@login_required
@admin_required
def profile_detail(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    form = AdminReviewForm(admin_notes=profile.admin_notes)
    duplicates = find_possible_duplicates(profile)
    return render_template("admin/profile_detail.html", profile=profile, form=form, duplicates=duplicates)


@admin_bp.route("/profiles/<public_id>/review", methods=["POST"])
@login_required
@admin_required
def review_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    form = AdminReviewForm()
    if form.validate_on_submit():
        action = form.action.data
        profile.admin_notes = form.admin_notes.data
        if action == "approve":
            profile.approval_status = "approved"
            profile.is_verified = True
            profile.approved_by_id = current_user.id
            profile.approved_at = datetime.utcnow()
            if not profile.qr_path:
                profile.qr_path = generate_profile_qr(profile)
            flash(f"{profile.full_name}'s profile approved.", "success")
        elif action == "reject":
            profile.approval_status = "rejected"
            flash(f"{profile.full_name}'s profile rejected.", "warning")
        elif action == "suspend":
            profile.approval_status = "suspended"
            flash(f"{profile.full_name}'s profile suspended.", "warning")
        elif action == "restore":
            profile.approval_status = "pending"
            profile.is_deleted = False
            profile.is_archived = False
            flash(f"{profile.full_name}'s profile restored.", "info")
        db.session.commit()
        log_activity(f"profile_{action}", user_id=current_user.id, target_type="profile", target_id=profile.id)
    return redirect(url_for("admin.profile_detail", public_id=profile.public_id))


@admin_bp.route("/profiles/<public_id>/archive", methods=["POST"])
@login_required
@admin_required
def archive_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    profile.is_archived = True
    db.session.commit()
    log_activity("archive_profile", user_id=current_user.id, target_type="profile", target_id=profile.id)
    flash("Profile archived.", "info")
    return redirect(url_for("admin.profiles_list"))


@admin_bp.route("/profiles/<public_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    profile.is_deleted = True
    profile.deleted_at = datetime.utcnow()
    db.session.commit()
    log_activity("delete_profile", user_id=current_user.id, target_type="profile", target_id=profile.id)
    flash("Profile moved to recycle bin.", "info")
    return redirect(url_for("admin.profiles_list"))


@admin_bp.route("/profiles/<public_id>/restore", methods=["POST"])
@login_required
@admin_required
def restore_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    profile.is_deleted = False
    profile.deleted_at = None
    db.session.commit()
    log_activity("restore_profile", user_id=current_user.id, target_type="profile", target_id=profile.id)
    flash("Profile restored from recycle bin.", "success")
    return redirect(url_for("admin.recycle_bin"))


@admin_bp.route("/profiles/<public_id>/permanent-delete", methods=["POST"])
@login_required
@admin_required
def permanent_delete_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    user = profile.user
    db.session.delete(profile)
    if user:
        db.session.delete(user)
    db.session.commit()
    log_activity("permanent_delete_profile", user_id=current_user.id, target_type="profile")
    flash("Profile permanently deleted.", "danger")
    return redirect(url_for("admin.recycle_bin"))


@admin_bp.route("/recycle-bin")
@login_required
@admin_required
def recycle_bin():
    page = request.args.get("page", 1, type=int)
    pagination = (Profile.query.filter_by(is_deleted=True)
                  .order_by(Profile.deleted_at.desc()).paginate(page=page, per_page=25, error_out=False))
    return render_template("admin/recycle_bin.html", pagination=pagination, profiles=pagination.items)


@admin_bp.route("/profiles/<public_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_profile(public_id):
    from app.forms.profile_forms import ProfileForm
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    form = ProfileForm(obj=profile)
    if form.validate_on_submit():
        form.populate_obj(profile)
        db.session.commit()
        log_activity("admin_edit_profile", user_id=current_user.id, target_type="profile", target_id=profile.id)
        flash("Profile updated by admin.", "success")
        return redirect(url_for("admin.profile_detail", public_id=profile.public_id))
    return render_template("admin/profile_edit.html", form=form, profile=profile)


@admin_bp.route("/profiles/merge", methods=["POST"])
@login_required
@admin_required
def merge_profiles():
    keep_id = request.form.get("keep_id", type=int)
    remove_id = request.form.get("remove_id", type=int)
    keep = Profile.query.get_or_404(keep_id)
    remove = Profile.query.get_or_404(remove_id)

    for photo in list(remove.photos):
        photo.profile_id = keep.id
    for doc in list(remove.documents):
        doc.profile_id = keep.id
    remove.is_deleted = True
    remove.deleted_at = datetime.utcnow()
    remove.admin_notes = (remove.admin_notes or "") + f"\nMerged into profile {keep.profile_code}"
    db.session.commit()
    log_activity("merge_profiles", user_id=current_user.id, target_type="profile", target_id=keep.id,
                 details=f"merged {remove.profile_code} into {keep.profile_code}")
    flash(f"Merged {remove.profile_code} into {keep.profile_code}.", "success")
    return redirect(url_for("admin.profile_detail", public_id=keep.public_id))


# ---------------------------------------------------------------- Import / Export
@admin_bp.route("/import-export")
@login_required
@admin_required
def import_export():
    return render_template("admin/import_export.html")


@admin_bp.route("/export/csv")
@login_required
@admin_required
def export_csv():
    profiles = Profile.query.filter_by(is_deleted=False).all()
    csv_data = export_profiles_csv(profiles)
    log_activity("export_csv", user_id=current_user.id)
    from flask import Response
    return Response(csv_data, mimetype="text/csv",
                     headers={"Content-Disposition": "attachment;filename=profiles_export.csv"})


@admin_bp.route("/export/excel")
@login_required
@admin_required
def export_excel():
    profiles = Profile.query.filter_by(is_deleted=False).all()
    buf = export_profiles_excel(profiles)
    log_activity("export_excel", user_id=current_user.id)
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                      as_attachment=True, download_name="profiles_export.xlsx")


@admin_bp.route("/import/csv", methods=["POST"])
@login_required
@admin_required
def import_csv():
    file = request.files.get("csv_file")
    if not file or not file.filename.endswith(".csv"):
        flash("Please upload a valid CSV file.", "danger")
        return redirect(url_for("admin.import_export"))
    success, errors = import_profiles_csv(file.stream, current_user.id)
    log_activity("import_csv", user_id=current_user.id, details=f"success={success}, errors={len(errors)}")
    flash(f"Imported {success} profiles successfully.", "success" if success else "warning")
    for err in errors[:20]:
        flash(err, "warning")
    return redirect(url_for("admin.import_export"))


# ---------------------------------------------------------------- Backup / Restore
@admin_bp.route("/backup")
@login_required
@admin_required
def backup_page():
    backups = list_backups()
    return render_template("admin/backup.html", backups=backups)


@admin_bp.route("/backup/create", methods=["POST"])
@login_required
@admin_required
def backup_create():
    path = create_backup_zip()
    log_activity("create_backup", user_id=current_user.id, details=os.path.basename(path))
    flash("Backup created successfully.", "success")
    return redirect(url_for("admin.backup_page"))


@admin_bp.route("/backup/download/<filename>")
@login_required
@admin_required
def backup_download(filename):
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    backup_dir = os.path.join(basedir, "instance", "backups")
    safe_name = os.path.basename(filename)
    return send_file(os.path.join(backup_dir, safe_name), as_attachment=True)


# ---------------------------------------------------------------- Settings
@admin_bp.route("/settings/site", methods=["GET", "POST"])
@login_required
@admin_required
def settings_site():
    form = SiteSettingsForm(
        org_name=get_setting("org_name", current_app.config["ORG_NAME"]),
        registration_open=get_setting("registration_open", "true") == "true",
        auto_approve=get_setting("auto_approve", "false") == "true",
        min_photos=int(get_setting("min_photos", 5) or 5),
        max_photos=int(get_setting("max_photos", 20) or 20),
        contact_email=get_setting("contact_email", ""),
        contact_phone=get_setting("contact_phone", ""),
    )
    if form.validate_on_submit():
        set_setting("org_name", form.org_name.data)
        set_setting("registration_open", "true" if form.registration_open.data else "false")
        set_setting("auto_approve", "true" if form.auto_approve.data else "false")
        set_setting("min_photos", str(form.min_photos.data))
        set_setting("max_photos", str(form.max_photos.data))
        set_setting("contact_email", form.contact_email.data or "")
        set_setting("contact_phone", form.contact_phone.data or "")
        log_activity("update_site_settings", user_id=current_user.id)
        flash("Site settings updated.", "success")
        return redirect(url_for("admin.settings_site"))
    return render_template("admin/settings_site.html", form=form)


@admin_bp.route("/settings/smtp", methods=["GET", "POST"])
@login_required
@admin_required
def settings_smtp():
    current = get_smtp_settings()
    form = SMTPSettingsForm(server=current["server"], port=current["port"] or 587,
                             email=current["email"], password=current["password"],
                             encryption=current["encryption"])
    if form.validate_on_submit():
        save_smtp_settings(form.server.data, form.port.data, form.email.data,
                            form.password.data, form.encryption.data)
        log_activity("update_smtp_settings", user_id=current_user.id)
        flash("SMTP settings saved and encrypted.", "success")
        return redirect(url_for("admin.settings_smtp"))
    return render_template("admin/settings_smtp.html", form=form)


@admin_bp.route("/settings/theme", methods=["GET", "POST"])
@login_required
@admin_required
def settings_theme():
    current = get_theme_settings()
    form = ThemeSettingsForm(primary=current["primary"], secondary=current["secondary"],
                              accent=current["accent"], dark_mode_enabled=current["dark_mode_enabled"],
                              rounded_cards=current["rounded_cards"])
    if form.validate_on_submit():
        save_theme_settings({
            "primary": form.primary.data, "secondary": form.secondary.data,
            "accent": form.accent.data, "dark_mode_enabled": form.dark_mode_enabled.data,
            "rounded_cards": form.rounded_cards.data,
        })
        log_activity("update_theme", user_id=current_user.id)
        flash("Theme updated.", "success")
        return redirect(url_for("admin.settings_theme"))
    return render_template("admin/settings_theme.html", form=form)


# ---------------------------------------------------------------- Announcements
@admin_bp.route("/announcements")
@login_required
@admin_required
def announcements_list():
    items = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template("admin/announcements_list.html", items=items)


@admin_bp.route("/announcements/create", methods=["GET", "POST"])
@login_required
@admin_required
def announcement_create():
    form = AnnouncementForm()
    if form.validate_on_submit():
        ann = Announcement(title=form.title.data, body=form.body.data, is_active=form.is_active.data,
                            is_banner=form.is_banner.data, created_by_id=current_user.id)
        db.session.add(ann)
        db.session.commit()
        flash("Announcement created.", "success")
        return redirect(url_for("admin.announcements_list"))
    return render_template("admin/announcement_form.html", form=form, title="New Announcement")


@admin_bp.route("/announcements/<int:ann_id>/delete", methods=["POST"])
@login_required
@admin_required
def announcement_delete(ann_id):
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    flash("Announcement deleted.", "info")
    return redirect(url_for("admin.announcements_list"))


# ---------------------------------------------------------------- Logs
@admin_bp.route("/logs/activity")
@login_required
@admin_required
def activity_logs():
    page = request.args.get("page", 1, type=int)
    pagination = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template("admin/activity_logs.html", pagination=pagination, logs=pagination.items)


@admin_bp.route("/logs/login")
@login_required
@admin_required
def login_logs():
    page = request.args.get("page", 1, type=int)
    pagination = LoginLog.query.order_by(LoginLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template("admin/login_logs.html", pagination=pagination, logs=pagination.items)


@admin_bp.route("/messages")
@login_required
@admin_required
def contact_messages():
    page = request.args.get("page", 1, type=int)
    pagination = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False)
    return render_template("admin/contact_messages.html", pagination=pagination, messages=pagination.items)


@admin_bp.route("/messages/<int:msg_id>/read", methods=["POST"])
@login_required
@admin_required
def mark_message_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for("admin.contact_messages"))

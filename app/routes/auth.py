from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.models import User, LoginLog
from app.forms.auth_forms import LoginForm, RegisterCandidateForm, ChangePasswordForm
from app.services.settings_service import log_activity

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(_role_home(current_user))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        success = bool(user and user.check_password(form.password.data) and user.status == "active")

        db.session.add(LoginLog(
            user_id=user.id if user else None, email_attempted=email, success=success,
            ip_address=request.remote_addr, user_agent=request.headers.get("User-Agent", "")[:255],
        ))
        db.session.commit()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
        elif user.status == "suspended":
            flash("Your account has been suspended. Contact the administrator.", "danger")
        elif user.status == "deleted":
            flash("This account no longer exists.", "danger")
        else:
            from datetime import datetime
            login_user(user, remember=form.remember.data)
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            log_activity("login", user_id=user.id)
            flash(f"Welcome back, {user.full_name}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or _role_home(user))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_activity("logout", user_id=current_user.id)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    form = RegisterCandidateForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(phone=form.phone.data.strip()).first():
            flash("An account with this phone number already exists.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            phone=form.phone.data.strip(),
            role=form.candidate_type.data,
            status="active",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_activity("self_register", user_id=user.id, details=f"role={user.role}")

        login_user(user)
        flash("Account created! Please complete your biodata registration below.", "success")
        return redirect(url_for("profile.create_or_edit"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            current_user.must_change_password = False
            db.session.commit()
            log_activity("change_password", user_id=current_user.id)
            flash("Password updated successfully.", "success")
            return redirect(_role_home(current_user))
    return render_template("auth/change_password.html", form=form)


def _role_home(user):
    if user.role == "admin":
        return url_for("admin.dashboard")
    if user.role == "member":
        return url_for("member.dashboard")
    return url_for("profile.create_or_edit")

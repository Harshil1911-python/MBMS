from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(f):
    return roles_required("admin")(f)


def member_or_admin_required(f):
    return roles_required("admin", "member")(f)


def candidate_required(f):
    return roles_required("groom", "bride")(f)


def active_user_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated and current_user.status != "active":
            flash("Your account has been suspended. Please contact the administrator.", "danger")
            return redirect(url_for("auth.logout"))
        return f(*args, **kwargs)
    return wrapped

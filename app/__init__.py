import os
from flask import Flask, render_template
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf, limiter


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "production")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["production"]))

    # Ensure instance/upload directories exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, "backups"), exist_ok=True)
    for folder_key in ("PHOTO_FOLDER", "DOCUMENT_FOLDER", "KUNDLI_FOLDER", "QR_FOLDER", "PDF_FOLDER"):
        os.makedirs(app.config[folder_key], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.member import member_bp
    from app.routes.profile import profile_bp
    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(member_bp, url_prefix="/member")
    app.register_blueprint(profile_bp, url_prefix="/profile")

    # Context processors
    from app.services.settings_service import get_theme_settings

    @app.context_processor
    def inject_globals():
        try:
            theme = get_theme_settings()
        except Exception:  # noqa: BLE001 - DB may not be migrated yet
            theme = {"primary": "#0b3d91", "secondary": "#ffffff", "accent": "#4a90d9",
                      "dark_mode_enabled": False, "rounded_cards": True}
        from datetime import datetime
        return {
            "org_name": app.config["ORG_NAME"],
            "footer_text": app.config["FOOTER_TEXT"],
            "footer_sub": app.config["FOOTER_SUB"],
            "theme": theme,
            "now_year": datetime.utcnow().year,
        }

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # CLI commands
    from app.cli import register_cli
    register_cli(app)

    return app

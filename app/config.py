import os
from datetime import timedelta

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    _db_url = os.environ.get("DATABASE_URL", "")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or f"sqlite:///{os.path.join(basedir, 'instance', 'mbms.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    PHOTO_FOLDER = os.path.join(UPLOAD_FOLDER, "photos")
    DOCUMENT_FOLDER = os.path.join(UPLOAD_FOLDER, "documents")
    KUNDLI_FOLDER = os.path.join(UPLOAD_FOLDER, "kundli")
    QR_FOLDER = os.path.join(basedir, "app", "static", "qr")
    PDF_FOLDER = os.path.join(basedir, "app", "static", "generated_pdf")
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60 MB per request (up to 20 photos + documents)

    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_DOC_EXT = {"pdf", "png", "jpg", "jpeg"}
    MIN_PHOTOS = 5
    MAX_PHOTOS = 20

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = None

    # Pagination
    PROFILES_PER_PAGE = 12

    # Branding
    ORG_NAME = "CITYLIGHT SINDHI SAMAJ SURAT"
    ORG_SHORT = "CSSS"
    FOOTER_TEXT = "Powered by SERENIA UPTIME"
    FOOTER_SUB = "TECH SERENIA"

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

import uuid
from datetime import datetime
import bcrypt
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)

    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # role: admin, member, groom, bride  (groom/bride collectively "candidate")
    role = db.Column(db.String(20), nullable=False, default="member", index=True)

    status = db.Column(db.String(20), nullable=False, default="active")  # active, suspended, deleted
    is_super_admin = db.Column(db.Boolean, default=False)

    must_change_password = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(64), nullable=True)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    profile = db.relationship(
        "Profile", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str):
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_member(self):
        return self.role == "member"

    @property
    def is_candidate(self):
        return self.role in ("groom", "bride")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

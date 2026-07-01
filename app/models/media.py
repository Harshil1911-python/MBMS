from datetime import datetime
from app.extensions import db


class Photo(db.Model):
    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)

    file_path = db.Column(db.String(255), nullable=False)
    thumbnail_path = db.Column(db.String(255))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"), nullable=False)

    doc_type = db.Column(db.String(30), nullable=False)  # aadhar, passport, pan, driving_license, kundli, other
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=False)  # visible on public QR page if admin allows
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

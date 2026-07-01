import uuid
from datetime import datetime, date
from app.extensions import db


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    profile_code = db.Column(db.String(20), unique=True, index=True)  # e.g. CSSS-B-0001

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    # ---------- Basic Information ----------
    full_name = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # male / female
    candidate_type = db.Column(db.String(10), nullable=False, index=True)  # bride / groom
    father_name = db.Column(db.String(150))
    mother_name = db.Column(db.String(150))
    guardian_name = db.Column(db.String(150))
    date_of_birth = db.Column(db.Date, nullable=False)
    time_of_birth = db.Column(db.String(20))
    place_of_birth = db.Column(db.String(150))
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Integer)
    blood_group = db.Column(db.String(5))
    complexion = db.Column(db.String(30))
    body_type = db.Column(db.String(30))
    nationality = db.Column(db.String(50), default="Indian")
    religion = db.Column(db.String(50), default="Hindu")
    community = db.Column(db.String(50), default="Sindhi")
    sindhi_caste = db.Column(db.String(80))
    sub_caste = db.Column(db.String(80))
    mother_tongue = db.Column(db.String(50), default="Sindhi")

    marital_status = db.Column(db.String(20), default="Single")  # Single/Widow/Widower/Divorced/Separated
    children = db.Column(db.Integer, default=0)

    # ---------- Career ----------
    occupation = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    company_business = db.Column(db.String(150))
    income_monthly = db.Column(db.Integer)
    income_yearly = db.Column(db.Integer)
    qualification = db.Column(db.String(150))
    college = db.Column(db.String(150))
    university = db.Column(db.String(150))

    # ---------- Location ----------
    current_city = db.Column(db.String(100), index=True)
    current_state = db.Column(db.String(100))
    current_country = db.Column(db.String(100), default="India")
    permanent_address = db.Column(db.Text)
    temporary_address = db.Column(db.Text)
    native_place = db.Column(db.String(100))

    # ---------- Contact ----------
    phone = db.Column(db.String(20))
    alternate_phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    whatsapp = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(150))
    emergency_contact_phone = db.Column(db.String(20))

    # ---------- Lifestyle ----------
    food_preference = db.Column(db.String(20))  # Veg/Non Veg/Jain
    smoking = db.Column(db.String(10), default="No")
    drinking = db.Column(db.String(10), default="No")
    habits = db.Column(db.Text)
    hobbies = db.Column(db.Text)
    interests = db.Column(db.Text)
    languages_known = db.Column(db.Text)
    about_yourself = db.Column(db.Text)

    # ---------- Partner Preference ----------
    pref_age_min = db.Column(db.Integer)
    pref_age_max = db.Column(db.Integer)
    pref_height_min = db.Column(db.Integer)
    pref_height_max = db.Column(db.Integer)
    pref_education = db.Column(db.String(150))
    pref_profession = db.Column(db.String(150))
    pref_income = db.Column(db.String(100))
    pref_location = db.Column(db.String(150))
    pref_lifestyle = db.Column(db.Text)

    # ---------- Astrology ----------
    manglik = db.Column(db.String(10), default="No")  # Yes/No/Partial
    rashi = db.Column(db.String(30))
    nakshatra = db.Column(db.String(30))
    mulank = db.Column(db.Integer)
    kundli_available = db.Column(db.Boolean, default=False)
    birth_chart_notes = db.Column(db.Text)
    horoscope_notes = db.Column(db.Text)

    # ---------- Medical ----------
    disability = db.Column(db.String(150))
    medical_notes = db.Column(db.Text)
    special_notes = db.Column(db.Text)

    # ---------- Declaration ----------
    declaration_accepted = db.Column(db.Boolean, default=False)
    signature_path = db.Column(db.String(255))

    # ---------- Workflow ----------
    approval_status = db.Column(db.String(20), default="pending", index=True)  # pending/approved/rejected/suspended
    admin_notes = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    featured_photo_path = db.Column(db.String(255))
    qr_path = db.Column(db.String(255))
    latest_biodata_pdf = db.Column(db.String(255))

    view_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photos = db.relationship("Photo", backref="profile", cascade="all, delete-orphan",
                              order_by="Photo.sort_order")
    documents = db.relationship("Document", backref="profile", cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("ix_profile_search", "candidate_type", "approval_status", "current_city"),
    )

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def height_display(self):
        if not self.height_cm:
            return "-"
        feet = self.height_cm // 30.48
        return f"{self.height_cm} cm ({feet:.1f} ft)"

    @property
    def is_editable(self):
        return self.approval_status in ("pending", "rejected")

    def __repr__(self):
        return f"<Profile {self.profile_code} {self.full_name}>"

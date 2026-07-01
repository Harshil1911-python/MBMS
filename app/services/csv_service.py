import csv
import io
from datetime import datetime
import pandas as pd
from app.extensions import db
from app.models import Profile, User

PROFILE_EXPORT_COLUMNS = [
    "profile_code", "full_name", "gender", "candidate_type", "date_of_birth",
    "height_cm", "weight_kg", "blood_group", "sindhi_caste", "sub_caste",
    "marital_status", "occupation", "qualification", "current_city",
    "current_state", "phone", "email", "approval_status", "created_at",
]


def export_profiles_csv(profiles):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(PROFILE_EXPORT_COLUMNS)
    for p in profiles:
        writer.writerow([getattr(p, col) for col in PROFILE_EXPORT_COLUMNS])
    output.seek(0)
    return output.getvalue()


def export_profiles_excel(profiles):
    rows = []
    for p in profiles:
        rows.append({col: getattr(p, col) for col in PROFILE_EXPORT_COLUMNS})
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Profiles")
    buf.seek(0)
    return buf


REQUIRED_IMPORT_COLUMNS = {"full_name", "gender", "candidate_type", "email", "phone", "date_of_birth"}


def import_profiles_csv(file_stream, created_by_user_id):
    """
    Bulk import candidate profiles from a CSV file-like object.
    Returns (success_count, errors[list of strings]).
    """
    text = file_stream.read()
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames or not REQUIRED_IMPORT_COLUMNS.issubset(set(reader.fieldnames)):
        missing = REQUIRED_IMPORT_COLUMNS - set(reader.fieldnames or [])
        return 0, [f"Missing required columns: {', '.join(missing)}"]

    success = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        try:
            email = row["email"].strip().lower()
            if User.query.filter_by(email=email).first():
                errors.append(f"Row {i}: email {email} already exists, skipped")
                continue

            dob = datetime.strptime(row["date_of_birth"].strip(), "%Y-%m-%d").date()

            user = User(
                full_name=row["full_name"].strip(),
                email=email,
                phone=row.get("phone", "").strip() or None,
                role=row.get("candidate_type", "groom").strip().lower(),
                status="active",
                created_by_id=created_by_user_id,
                must_change_password=True,
            )
            user.set_password("Welcome@123")
            db.session.add(user)
            db.session.flush()

            profile = Profile(
                user_id=user.id,
                full_name=row["full_name"].strip(),
                gender=row["gender"].strip().lower(),
                candidate_type=row["candidate_type"].strip().lower(),
                date_of_birth=dob,
                current_city=row.get("current_city", "").strip() or None,
                occupation=row.get("occupation", "").strip() or None,
                qualification=row.get("qualification", "").strip() or None,
                phone=row.get("phone", "").strip() or None,
                email=email,
                sindhi_caste=row.get("sindhi_caste", "").strip() or None,
                approval_status="pending",
            )
            db.session.add(profile)
            db.session.flush()
            profile.profile_code = _generate_profile_code(profile)
            success += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"Row {i}: {str(e)}")

    if success:
        db.session.commit()
    else:
        db.session.rollback()

    return success, errors


def _generate_profile_code(profile):
    prefix = "B" if profile.candidate_type == "bride" else "G"
    return f"CSSS-{prefix}-{profile.id:04d}"

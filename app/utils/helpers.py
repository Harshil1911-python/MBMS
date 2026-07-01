from difflib import SequenceMatcher
from app.models import Profile


def generate_profile_code(profile):
    prefix = "B" if profile.candidate_type == "bride" else "G"
    return f"CSSS-{prefix}-{profile.id:04d}"


def find_possible_duplicates(profile, threshold=0.82):
    """Simple duplicate detection based on name + DOB + phone similarity."""
    candidates = Profile.query.filter(
        Profile.candidate_type == profile.candidate_type,
        Profile.id != profile.id,
        Profile.is_deleted.is_(False),
    ).all()

    matches = []
    for c in candidates:
        score = SequenceMatcher(None, (profile.full_name or "").lower(), (c.full_name or "").lower()).ratio()
        same_dob = profile.date_of_birth and c.date_of_birth and profile.date_of_birth == c.date_of_birth
        same_phone = profile.phone and c.phone and profile.phone == c.phone
        if same_phone or (same_dob and score > 0.6) or score >= threshold:
            matches.append((c, round(score * 100, 1)))
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def apply_search_filters(query, args):
    """Applies GET-arg based filters onto a Profile query. `args` is a MultiDict-like (request.args)."""
    from datetime import date

    candidate_type = args.get("candidate_type")
    if candidate_type:
        query = query.filter(Profile.candidate_type == candidate_type)

    marital_status = args.get("marital_status")
    if marital_status:
        query = query.filter(Profile.marital_status == marital_status)

    city = args.get("city")
    if city:
        query = query.filter(Profile.current_city.ilike(f"%{city}%"))

    caste = args.get("sindhi_caste")
    if caste:
        query = query.filter(Profile.sindhi_caste.ilike(f"%{caste}%"))

    qualification = args.get("qualification")
    if qualification:
        query = query.filter(Profile.qualification.ilike(f"%{qualification}%"))

    occupation = args.get("occupation")
    if occupation:
        query = query.filter(Profile.occupation.ilike(f"%{occupation}%"))

    manglik = args.get("manglik")
    if manglik:
        query = query.filter(Profile.manglik == manglik)

    food_preference = args.get("food_preference")
    if food_preference:
        query = query.filter(Profile.food_preference == food_preference)

    kundli_available = args.get("kundli_available")
    if kundli_available == "yes":
        query = query.filter(Profile.kundli_available.is_(True))
    elif kundli_available == "no":
        query = query.filter(Profile.kundli_available.is_(False))

    height_min = args.get("height_min", type=int)
    if height_min:
        query = query.filter(Profile.height_cm >= height_min)
    height_max = args.get("height_max", type=int)
    if height_max:
        query = query.filter(Profile.height_cm <= height_max)

    age_min = args.get("age_min", type=int)
    age_max = args.get("age_max", type=int)
    if age_min:
        max_dob = date(date.today().year - age_min, date.today().month, date.today().day)
        query = query.filter(Profile.date_of_birth <= max_dob)
    if age_max:
        min_dob = date(date.today().year - age_max - 1, date.today().month, date.today().day)
        query = query.filter(Profile.date_of_birth >= min_dob)

    sort = args.get("sort", "recent")
    if sort == "updated":
        query = query.order_by(Profile.updated_at.desc())
    elif sort == "age_asc":
        query = query.order_by(Profile.date_of_birth.desc())
    elif sort == "age_desc":
        query = query.order_by(Profile.date_of_birth.asc())
    else:
        query = query.order_by(Profile.created_at.desc())

    return query

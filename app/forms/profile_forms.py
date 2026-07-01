from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField, IntegerField, SelectField, TextAreaField, BooleanField,
    DateField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email

MARITAL_CHOICES = [("Single", "Single"), ("Widow", "Widow"), ("Widower", "Widower"),
                    ("Divorced", "Divorced"), ("Separated", "Separated")]
YESNO = [("No", "No"), ("Yes", "Yes")]
MANGLIK_CHOICES = [("No", "No"), ("Yes", "Yes"), ("Partial", "Partial")]
FOOD_CHOICES = [("Veg", "Vegetarian"), ("Non Veg", "Non-Vegetarian"), ("Jain", "Jain")]


class ProfileForm(FlaskForm):
    # Basic
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    gender = SelectField("Gender", choices=[("male", "Male"), ("female", "Female")],
                          validators=[DataRequired()])
    candidate_type = SelectField("Bride / Groom", choices=[("bride", "Bride"), ("groom", "Groom")],
                                  validators=[DataRequired()])
    father_name = StringField("Father's Name", validators=[Optional(), Length(max=150)])
    mother_name = StringField("Mother's Name", validators=[Optional(), Length(max=150)])
    guardian_name = StringField("Guardian Name", validators=[Optional(), Length(max=150)])
    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    time_of_birth = StringField("Time of Birth", validators=[Optional(), Length(max=20)])
    place_of_birth = StringField("Place of Birth", validators=[Optional(), Length(max=150)])
    height_cm = IntegerField("Height (cm)", validators=[Optional(), NumberRange(min=100, max=250)])
    weight_kg = IntegerField("Weight (kg)", validators=[Optional(), NumberRange(min=20, max=250)])
    blood_group = SelectField("Blood Group", choices=[
        ("", "Select"), ("A+", "A+"), ("A-", "A-"), ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"), ("O+", "O+"), ("O-", "O-")], validators=[Optional()])
    complexion = SelectField("Complexion", choices=[
        ("", "Select"), ("Fair", "Fair"), ("Wheatish", "Wheatish"), ("Dark", "Dark")], validators=[Optional()])
    body_type = SelectField("Body Type", choices=[
        ("", "Select"), ("Slim", "Slim"), ("Athletic", "Athletic"), ("Average", "Average"),
        ("Heavy", "Heavy")], validators=[Optional()])
    nationality = StringField("Nationality", default="Indian", validators=[Optional(), Length(max=50)])
    religion = StringField("Religion", default="Hindu", validators=[Optional(), Length(max=50)])
    community = StringField("Community", default="Sindhi", validators=[Optional(), Length(max=50)])
    sindhi_caste = StringField("Sindhi Caste", validators=[Optional(), Length(max=80)])
    sub_caste = StringField("Sub Caste", validators=[Optional(), Length(max=80)])
    mother_tongue = StringField("Mother Tongue", default="Sindhi", validators=[Optional(), Length(max=50)])
    marital_status = SelectField("Marital Status", choices=MARITAL_CHOICES, validators=[DataRequired()])
    children = IntegerField("Children", default=0, validators=[Optional(), NumberRange(min=0, max=20)])

    # Career
    occupation = StringField("Occupation", validators=[Optional(), Length(max=100)])
    designation = StringField("Designation", validators=[Optional(), Length(max=100)])
    company_business = StringField("Company / Business", validators=[Optional(), Length(max=150)])
    income_monthly = IntegerField("Monthly Income (₹)", validators=[Optional(), NumberRange(min=0)])
    income_yearly = IntegerField("Yearly Income (₹)", validators=[Optional(), NumberRange(min=0)])
    qualification = StringField("Qualification", validators=[Optional(), Length(max=150)])
    college = StringField("College", validators=[Optional(), Length(max=150)])
    university = StringField("University", validators=[Optional(), Length(max=150)])

    # Location
    current_city = StringField("Current City", validators=[DataRequired(), Length(max=100)])
    current_state = StringField("State", validators=[Optional(), Length(max=100)])
    current_country = StringField("Country", default="India", validators=[Optional(), Length(max=100)])
    permanent_address = TextAreaField("Permanent Address", validators=[Optional()])
    temporary_address = TextAreaField("Temporary Address", validators=[Optional()])
    native_place = StringField("Native Place", validators=[Optional(), Length(max=100)])

    # Contact
    phone = StringField("Phone", validators=[DataRequired(), Length(min=10, max=15)])
    alternate_phone = StringField("Alternate Phone", validators=[Optional(), Length(max=15)])
    email = StringField("Email", validators=[Optional(), Email()])
    whatsapp = StringField("WhatsApp", validators=[Optional(), Length(max=15)])
    emergency_contact_name = StringField("Emergency Contact Name", validators=[Optional(), Length(max=150)])
    emergency_contact_phone = StringField("Emergency Contact Phone", validators=[Optional(), Length(max=15)])

    # Lifestyle
    food_preference = SelectField("Food Preference", choices=FOOD_CHOICES, validators=[Optional()])
    smoking = SelectField("Smoking", choices=YESNO, validators=[Optional()])
    drinking = SelectField("Drinking", choices=YESNO, validators=[Optional()])
    habits = TextAreaField("Habits", validators=[Optional()])
    hobbies = TextAreaField("Hobbies", validators=[Optional()])
    interests = TextAreaField("Interests", validators=[Optional()])
    languages_known = StringField("Languages Known", validators=[Optional(), Length(max=200)])
    about_yourself = TextAreaField("About Yourself", validators=[Optional(), Length(max=2000)])

    # Partner Preference
    pref_age_min = IntegerField("Preferred Age (Min)", validators=[Optional(), NumberRange(min=18, max=90)])
    pref_age_max = IntegerField("Preferred Age (Max)", validators=[Optional(), NumberRange(min=18, max=90)])
    pref_height_min = IntegerField("Preferred Height cm (Min)", validators=[Optional(), NumberRange(min=100, max=250)])
    pref_height_max = IntegerField("Preferred Height cm (Max)", validators=[Optional(), NumberRange(min=100, max=250)])
    pref_education = StringField("Preferred Education", validators=[Optional(), Length(max=150)])
    pref_profession = StringField("Preferred Profession", validators=[Optional(), Length(max=150)])
    pref_income = StringField("Preferred Income", validators=[Optional(), Length(max=100)])
    pref_location = StringField("Preferred Location", validators=[Optional(), Length(max=150)])
    pref_lifestyle = TextAreaField("Preferred Lifestyle", validators=[Optional()])

    # Astrology
    manglik = SelectField("Manglik", choices=MANGLIK_CHOICES, validators=[Optional()])
    rashi = SelectField("Rashi", choices=[("", "Select")] + [(r, r) for r in [
        "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
        "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)",
        "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"]],
        validators=[Optional()])
    nakshatra = SelectField("Nakshatra", choices=[("", "Select")] + [(n, n) for n in [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
        "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
        "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
        "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]],
        validators=[Optional()])
    mulank = IntegerField("Mulank", validators=[Optional(), NumberRange(min=1, max=9)])
    kundli_available = BooleanField("Kundli Available")
    kundli_file = FileField("Upload Kundli (PDF/Image)", validators=[
        Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image only")])
    birth_chart_notes = TextAreaField("Birth Chart Notes", validators=[Optional()])
    horoscope_notes = TextAreaField("Horoscope Notes", validators=[Optional()])

    # Medical
    disability = StringField("Disability (if any)", validators=[Optional(), Length(max=150)])
    medical_notes = TextAreaField("Medical Information", validators=[Optional()])
    special_notes = TextAreaField("Special Notes", validators=[Optional()])

    # Photos & Documents
    photo_files = MultipleFileField("Profile Photos (min 5, max 20)", validators=[
        Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"], "Images only")])
    aadhar_doc = FileField("Aadhar Card", validators=[
        Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image only")])
    passport_doc = FileField("Passport", validators=[
        Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image only")])
    pan_doc = FileField("PAN Card", validators=[
        Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image only")])
    driving_license_doc = FileField("Driving License", validators=[
        Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image only")])
    other_doc = FileField("Other Document", validators=[
        Optional(), FileAllowed(["pdf", "png", "jpg", "jpeg"], "PDF or image only")])

    declaration_accepted = BooleanField("I declare the above information is true and correct",
                                         validators=[DataRequired()])

    submit = SubmitField("Save Profile")


class AdminReviewForm(FlaskForm):
    admin_notes = TextAreaField("Admin Notes", validators=[Optional(), Length(max=2000)])
    action = SelectField("Action", choices=[
        ("approve", "Approve"), ("reject", "Reject"), ("suspend", "Suspend"), ("restore", "Restore")
    ], validators=[DataRequired()])
    submit = SubmitField("Submit")


class SearchFilterForm(FlaskForm):
    class Meta:
        csrf = False

    candidate_type = SelectField("Type", choices=[("", "All"), ("bride", "Bride"), ("groom", "Groom")])
    age_min = IntegerField("Age Min", validators=[Optional()])
    age_max = IntegerField("Age Max", validators=[Optional()])
    height_min = IntegerField("Height Min (cm)", validators=[Optional()])
    height_max = IntegerField("Height Max (cm)", validators=[Optional()])
    marital_status = SelectField("Marital Status", choices=[("", "Any")] + MARITAL_CHOICES)
    city = StringField("City", validators=[Optional()])
    sindhi_caste = StringField("Caste", validators=[Optional()])
    qualification = StringField("Qualification", validators=[Optional()])
    occupation = StringField("Occupation", validators=[Optional()])
    manglik = SelectField("Manglik", choices=[("", "Any")] + MANGLIK_CHOICES)
    food_preference = SelectField("Food Preference", choices=[("", "Any")] + FOOD_CHOICES)
    kundli_available = SelectField("Kundli Available", choices=[("", "Any"), ("yes", "Yes"), ("no", "No")])
    sort = SelectField("Sort", choices=[
        ("recent", "Recently Added"), ("updated", "Recently Updated"),
        ("age_asc", "Age: Low to High"), ("age_desc", "Age: High to Low")
    ])

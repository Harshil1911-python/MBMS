from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, Length


class SMTPSettingsForm(FlaskForm):
    server = StringField("SMTP Server", validators=[DataRequired(), Length(max=150)])
    port = IntegerField("Port", validators=[DataRequired()])
    email = StringField("SMTP Email", validators=[DataRequired(), Email()])
    password = StringField("SMTP Password", validators=[DataRequired()])
    encryption = SelectField("Encryption", choices=[("TLS", "TLS"), ("SSL", "SSL"), ("None", "None")])
    submit = SubmitField("Save SMTP Settings")


class ThemeSettingsForm(FlaskForm):
    primary = StringField("Primary Color", default="#0b3d91")
    secondary = StringField("Secondary Color", default="#ffffff")
    accent = StringField("Accent Color", default="#4a90d9")
    dark_mode_enabled = BooleanField("Enable Dark Mode Toggle")
    rounded_cards = BooleanField("Rounded Cards", default=True)
    submit = SubmitField("Save Theme")


class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Body", validators=[DataRequired()])
    is_active = BooleanField("Active", default=True)
    is_banner = BooleanField("Show as Homepage Banner")
    submit = SubmitField("Save Announcement")


class SiteSettingsForm(FlaskForm):
    org_name = StringField("Organization Name", validators=[DataRequired(), Length(max=200)])
    registration_open = BooleanField("Allow New Registrations", default=True)
    auto_approve = BooleanField("Auto-approve New Profiles", default=False)
    min_photos = IntegerField("Minimum Photos Required", default=5)
    max_photos = IntegerField("Maximum Photos Allowed", default=20)
    contact_email = StringField("Public Contact Email", validators=[Optional(), Email()])
    contact_phone = StringField("Public Contact Phone", validators=[Optional()])
    submit = SubmitField("Save Settings")

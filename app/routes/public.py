from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user

from app.extensions import db, limiter
from app.models import Profile, Announcement, Testimonial, FAQ, CMSPage, ContactMessage, Document

public_bp = Blueprint("public", __name__, template_folder="../templates/public")


@public_bp.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        if current_user.is_member:
            return redirect(url_for("member.dashboard"))
        return redirect(url_for("profile.create_or_edit"))

    banner = Announcement.query.filter_by(is_active=True, is_banner=True).order_by(
        Announcement.created_at.desc()).first()
    testimonials = Testimonial.query.filter_by(is_published=True).order_by(
        Testimonial.created_at.desc()).limit(6).all()
    stats = {
        "total_profiles": Profile.query.filter_by(approval_status="approved", is_deleted=False).count(),
        "total_brides": Profile.query.filter_by(candidate_type="bride", approval_status="approved",
                                                  is_deleted=False).count(),
        "total_grooms": Profile.query.filter_by(candidate_type="groom", approval_status="approved",
                                                  is_deleted=False).count(),
    }
    return render_template("public/home.html", banner=banner, testimonials=testimonials, stats=stats)


@public_bp.route("/about")
def about():
    page = CMSPage.query.filter_by(slug="about").first()
    return render_template("public/about.html", page=page)


@public_bp.route("/faqs")
def faqs():
    items = FAQ.query.filter_by(is_active=True).order_by(FAQ.sort_order).all()
    return render_template("public/faqs.html", faqs=items)


@public_bp.route("/success-stories")
def success_stories():
    testimonials = Testimonial.query.filter_by(is_published=True).order_by(
        Testimonial.created_at.desc()).all()
    return render_template("public/success_stories.html", testimonials=testimonials)


@public_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        if not (name and email and message):
            flash("Please fill in all required fields.", "danger")
        else:
            db.session.add(ContactMessage(name=name, email=email, phone=phone,
                                           subject=subject, message=message))
            db.session.commit()
            flash("Thank you! Your message has been sent to our team.", "success")
            return redirect(url_for("public.contact"))
    return render_template("public/contact.html")


@public_bp.route("/p/<public_id>")
def profile_view(public_id):
    """Public read-only profile page, reached via QR code scan."""
    profile = Profile.query.filter_by(public_id=public_id, approval_status="approved",
                                       is_deleted=False).first_or_404()
    public_documents = Document.query.filter_by(profile_id=profile.id, is_public=True).all()
    return render_template("public/qr_profile.html", profile=profile, public_documents=public_documents)

import os
from flask import (Blueprint, render_template, redirect, url_for, flash, request,
                    send_from_directory, current_app, abort)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Profile, Favorite, RecentlyViewed, SavedSearch
from app.forms.profile_forms import SearchFilterForm
from app.utils.decorators import member_or_admin_required
from app.utils.helpers import apply_search_filters
from app.services.biodata_pdf import generate_biodata_pdf
from app.services.qr_service import generate_profile_qr
from app.services.kundli_service import match_profiles
from app.services.settings_service import log_activity

member_bp = Blueprint("member", __name__, template_folder="../templates/member")


@member_bp.route("/dashboard")
@login_required
@member_or_admin_required
def dashboard():
    recent_profiles = (Profile.query.filter_by(approval_status="approved", is_deleted=False)
                        .order_by(Profile.created_at.desc()).limit(8).all())
    my_favorites = (Favorite.query.filter_by(user_id=current_user.id)
                     .order_by(Favorite.created_at.desc()).limit(8).all())
    recently_viewed = (RecentlyViewed.query.filter_by(user_id=current_user.id)
                        .order_by(RecentlyViewed.viewed_at.desc()).limit(8).all())
    return render_template("member/dashboard.html", recent_profiles=recent_profiles,
                            my_favorites=my_favorites, recently_viewed=recently_viewed)


@member_bp.route("/browse")
@member_bp.route("/browse/<category>")
@login_required
@member_or_admin_required
def browse(category="all"):
    form = SearchFilterForm(request.args)
    query = Profile.query.filter_by(approval_status="approved", is_deleted=False, is_archived=False)

    if category in ("bride", "groom"):
        query = query.filter(Profile.candidate_type == category)
    elif category == "married":
        query = query.filter(Profile.marital_status.in_(["Widow", "Widower"]))  # previously married statuses
    elif category == "single":
        query = query.filter(Profile.marital_status == "Single")
    elif category == "divorced":
        query = query.filter(Profile.marital_status == "Divorced")
    elif category == "widow":
        query = query.filter(Profile.marital_status == "Widow")
    elif category == "widower":
        query = query.filter(Profile.marital_status == "Widower")

    query = apply_search_filters(query, request.args)

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=current_app.config["PROFILES_PER_PAGE"], error_out=False)

    favorite_ids = {f.profile_id for f in Favorite.query.filter_by(user_id=current_user.id).all()}

    return render_template("member/browse.html", pagination=pagination, profiles=pagination.items,
                            form=form, category=category, favorite_ids=favorite_ids)


@member_bp.route("/profile/<public_id>")
@login_required
@member_or_admin_required
def view_profile(public_id):
    profile = Profile.query.filter_by(public_id=public_id, is_deleted=False).first_or_404()
    if profile.approval_status != "approved" and not current_user.is_admin:
        abort(404)

    profile.view_count = (profile.view_count or 0) + 1

    already = RecentlyViewed.query.filter_by(user_id=current_user.id, profile_id=profile.id).first()
    if already:
        already.viewed_at = db.func.now()
    else:
        db.session.add(RecentlyViewed(user_id=current_user.id, profile_id=profile.id))
    db.session.commit()

    is_favorite = Favorite.query.filter_by(user_id=current_user.id, profile_id=profile.id).first() is not None

    return render_template("member/profile_detail.html", profile=profile, is_favorite=is_favorite)


@member_bp.route("/profile/<public_id>/favorite", methods=["POST"])
@login_required
@member_or_admin_required
def toggle_favorite(public_id):
    profile = Profile.query.filter_by(public_id=public_id).first_or_404()
    fav = Favorite.query.filter_by(user_id=current_user.id, profile_id=profile.id).first()
    if fav:
        db.session.delete(fav)
        flash("Removed from favourites.", "info")
    else:
        db.session.add(Favorite(user_id=current_user.id, profile_id=profile.id))
        flash("Added to favourites.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("member.view_profile", public_id=public_id))


@member_bp.route("/profile/<public_id>/biodata")
@login_required
@member_or_admin_required
def download_biodata(public_id):
    profile = Profile.query.filter_by(public_id=public_id, is_deleted=False).first_or_404()
    if profile.approval_status != "approved" and not current_user.is_admin:
        abort(404)

    if not profile.qr_path:
        profile.qr_path = generate_profile_qr(profile)
        db.session.commit()

    pdf_rel_path = generate_biodata_pdf(profile, org_name=current_app.config["ORG_NAME"])
    profile.latest_biodata_pdf = pdf_rel_path
    db.session.commit()

    log_activity("download_biodata", user_id=current_user.id, target_type="profile", target_id=profile.id)

    directory = current_app.config["PDF_FOLDER"]
    filename = os.path.basename(pdf_rel_path)
    return send_from_directory(directory, filename, as_attachment=True,
                                download_name=f"{profile.profile_code}_biodata.pdf")


@member_bp.route("/kundli-match")
@login_required
@member_or_admin_required
def kundli_match_select():
    brides = Profile.query.filter_by(candidate_type="bride", approval_status="approved", is_deleted=False).all()
    grooms = Profile.query.filter_by(candidate_type="groom", approval_status="approved", is_deleted=False).all()
    return render_template("member/kundli_select.html", brides=brides, grooms=grooms)


@member_bp.route("/kundli-match/result")
@login_required
@member_or_admin_required
def kundli_match_result():
    bride_id = request.args.get("bride_id", type=int)
    groom_id = request.args.get("groom_id", type=int)
    bride = Profile.query.filter_by(id=bride_id, candidate_type="bride").first_or_404()
    groom = Profile.query.filter_by(id=groom_id, candidate_type="groom").first_or_404()
    result = match_profiles(bride, groom)
    return render_template("member/kundli_result.html", bride=bride, groom=groom, result=result)


@member_bp.route("/compare")
@login_required
@member_or_admin_required
def compare():
    ids = request.args.getlist("id", type=int)
    profiles = Profile.query.filter(Profile.id.in_(ids)).all() if ids else []
    return render_template("member/compare.html", profiles=profiles)


@member_bp.route("/saved-searches/save", methods=["POST"])
@login_required
@member_or_admin_required
def save_search():
    name = request.form.get("name", "My Search")
    query_string = request.form.get("query_string", "")
    db.session.add(SavedSearch(user_id=current_user.id, name=name, query_string=query_string))
    db.session.commit()
    flash("Search saved.", "success")
    return redirect(request.referrer or url_for("member.browse"))


@member_bp.route("/saved-searches")
@login_required
@member_or_admin_required
def saved_searches():
    searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(SavedSearch.created_at.desc()).all()
    return render_template("member/saved_searches.html", searches=searches)

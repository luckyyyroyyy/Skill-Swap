import os
import logging
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    request,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import User, Skill
from forms import SkillForm, EditProfileForm
from utils import find_matches, check_and_award_badges, XP_ADD_SKILL

user_bp = Blueprint("user", __name__)
logger = logging.getLogger(__name__)


@user_bp.route("/dashboard")
@login_required
def dashboard():
    from models import SwapRequest
    from forms import SkillForm

    form = SkillForm()
    category_filter = request.args.get("category")
    page = request.args.get("page", 1, type=int)
    per_page = 9

    all_matches = find_matches(current_user, category=category_filter)
    total_matches = len(all_matches)
    total_pages = max(1, (total_matches + per_page - 1) // per_page)
    page = min(page, total_pages)
    matches = all_matches[(page - 1) * per_page : page * per_page]

    offers = [s for s in current_user.skills if s.type == "offer"]
    wants = [s for s in current_user.skills if s.type == "want"]
    received_requests = (
        SwapRequest.query.filter_by(receiver_id=current_user.id)
        .filter(SwapRequest.status.in_(["pending", "accepted"]))
        .all()
    )
    sent_requests = SwapRequest.query.filter_by(
        sender_id=current_user.id
    ).all()
    return render_template(
        "dashboard.html",
        matches=matches,
        form=form,
        offers=offers,
        wants=wants,
        received_requests=received_requests,
        sent_requests=sent_requests,
        current_category=category_filter,
        page=page,
        total_pages=total_pages,
        total_matches=total_matches,
    )


@user_bp.route("/profile/<username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    offered_skills = [skill for skill in user.skills if skill.type == "offer"]
    wanted_skills = [skill for skill in user.skills if skill.type == "want"]
    
    from forms import ReviewForm
    from models import Review
    
    review_form = ReviewForm()
    has_reviewed = False
    
    if current_user.id != user.id:
        existing_review = Review.query.filter_by(
            reviewer_id=current_user.id, reviewed_user_id=user.id
        ).first()
        if existing_review:
            has_reviewed = True

    # Join Review with User to get the reviewer's details easily
    reviews_data = db.session.query(Review, User).join(
        User, Review.reviewer_id == User.id
    ).filter(
        Review.reviewed_user_id == user.id
    ).order_by(Review.created_at.desc()).all()

    return render_template(
        "profile.html",
        user=user,
        offered_skills=offered_skills,
        wanted_skills=wanted_skills,
        review_form=review_form,
        has_reviewed=has_reviewed,
        reviews_data=reviews_data,
    )


@user_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        try:
            current_user.bio = form.bio.data
            current_user.timezone = form.timezone.data

            if form.profile_pic.data:
                file = form.profile_pic.data

                # Check MIME type using python-magic
                import magic

                file_content = file.read()
                mime_type = magic.from_buffer(file_content, mime=True)
                file.seek(0)  # Reset file pointer after reading

                allowed_mimes = ["image/jpeg", "image/png"]
                if mime_type not in allowed_mimes:
                    flash(
                        "Invalid file type! Please upload a valid JPEG or PNG image.",  # noqa: E501
                        "danger",
                    )
                    return redirect(url_for("user.edit_profile"))

                filename = secure_filename(file.filename)
                filepath = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], filename
                )
                os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
                file.save(filepath)
                current_user.profile_pic = filename
                logger.info(
                    f"Profile picture updated for user {current_user.username}"
                )

            db.session.commit()
            logger.info(f"Profile updated for user {current_user.username}")
            flash("Profile updated successfully!", "success")
            return redirect(
                url_for("user.profile", username=current_user.username)
            )
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error updating profile for user {current_user.id}: {e}"
            )
            flash("An error occurred. Please try again.", "danger")

    elif request.method == "GET":
        form.bio.data = current_user.bio
        form.timezone.data = current_user.timezone

    return render_template("edit_profile.html", form=form)


@user_bp.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    try:
        current_user.is_active = False
        db.session.commit()
        logger.info(f"User {current_user.username} deactivated their account")
        flash("Your account has been deleted.", "info")
        from flask_login import logout_user

        logout_user()
        return redirect(url_for("main.landing"))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting account for user {current_user.id}: {e}")
        flash("An error occurred. Please try again.", "danger")
        return redirect(url_for("user.edit_profile"))


@user_bp.route("/add_skill", methods=["POST"])
@login_required
def add_skill():
    form = SkillForm()
    if form.validate_on_submit():
        try:
            new_skill = Skill(
                name=form.name.data,
                category=form.category.data,
                type=form.type.data,
                proficiency_level=form.proficiency_level.data,
                user_id=current_user.id,
            )
            db.session.add(new_skill)
            current_user.xp += XP_ADD_SKILL
            check_and_award_badges(current_user)
            db.session.commit()
            logger.info(
                f"User {current_user.username} added skill: {new_skill.name}"
            )
            flash(
                f"Skill added successfully! +{XP_ADD_SKILL} XP 🚀", "success"
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding skill for user {current_user.id}: {e}")
            flash("Error adding skill. Please try again.", "danger")
    else:
        for error in form.errors.values():
            flash(str(error), "danger")
    return redirect(request.referrer or url_for("user.dashboard"))

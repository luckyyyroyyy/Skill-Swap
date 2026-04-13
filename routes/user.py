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
from models import User, Skill, AvailabilitySlot, PortfolioProject
from forms import SkillForm, EditProfileForm, AvailabilityForm, PortfolioProjectForm
from utils import find_matches, check_and_award_badges, XP_ADD_SKILL, convert_availability_to_viewer_tz

user_bp = Blueprint("user", __name__)
logger = logging.getLogger(__name__)


@user_bp.route("/dashboard")
@login_required
def dashboard():
    from models import SwapRequest
    from forms import SkillForm

    form = SkillForm()
    all_matches = find_matches(current_user)
    matches = all_matches[:3]

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
    )


@user_bp.route("/discover")
@login_required
def discover():
    category_filter = request.args.get("category")
    all_matches = find_matches(current_user, category=category_filter)
    
    return render_template(
        "discover.html", 
        matches=all_matches, 
        current_category=category_filter
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

    # Availability calculation
    viewer_availability = []
    if current_user.is_authenticated and getattr(current_user, 'timezone', None):
        for slot in user.availability:
            new_day, new_start, new_end = convert_availability_to_viewer_tz(slot, user.timezone or "UTC", current_user.timezone)
            viewer_availability.append({
                'day_of_week': new_day,
                'start_time': new_start,
                'end_time': new_end
            })
    else:
        for slot in user.availability:
            viewer_availability.append({
                'day_of_week': slot.day_of_week,
                'start_time': slot.start_time,
                'end_time': slot.end_time
            })

    return render_template(
        "profile.html",
        user=user,
        offered_skills=offered_skills,
        wanted_skills=wanted_skills,
        review_form=review_form,
        has_reviewed=has_reviewed,
        reviews_data=reviews_data,
        viewer_availability=viewer_availability,
    )


@user_bp.route("/add_availability", methods=["POST"])
@login_required
def add_availability():
    form = AvailabilityForm()
    if form.validate_on_submit():
        try:
            slot = AvailabilitySlot(
                user_id=current_user.id,
                day_of_week=int(form.day_of_week.data),
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            db.session.add(slot)
            db.session.commit()
            flash("Availability added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding availability for user {current_user.id}: {e}")
            flash("An error occurred.", "danger")
    else:
        for error in form.errors.values():
            flash(str(error), "danger")
    return redirect(url_for("user.edit_profile"))


@user_bp.route("/remove_availability/<int:slot_id>", methods=["POST", "GET"])
@login_required
def remove_availability(slot_id):
    try:
        slot = db.session.get(AvailabilitySlot, slot_id)
        if slot and slot.user_id == current_user.id:
            db.session.delete(slot)
            db.session.commit()
            flash("Availability removed.", "info")
        else:
            flash("Invalid availability slot.", "warning")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing availability for user {current_user.id}: {e}")
        flash("An error occurred.", "danger")
    return redirect(url_for("user.edit_profile"))


@user_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        try:
            current_user.bio = form.bio.data
            current_user.timezone = form.timezone.data
            current_user.github_username = form.github_username.data or None
            current_user.linkedin_url = form.linkedin_url.data or None
            current_user.portfolio_url = form.portfolio_url.data or None

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
        form.github_username.data = current_user.github_username
        form.linkedin_url.data = current_user.linkedin_url
        form.portfolio_url.data = current_user.portfolio_url

    availability_form = AvailabilityForm()
    portfolio_form = PortfolioProjectForm()
    return render_template("edit_profile.html", form=form, availability_form=availability_form, portfolio_form=portfolio_form)


@user_bp.route("/add_portfolio_project", methods=["POST"])
@login_required
def add_portfolio_project():
    form = PortfolioProjectForm()
    if form.validate_on_submit():
        try:
            filename = None
            if form.image.data:
                file = form.image.data
                filename = secure_filename(file.filename)
                
                import uuid
                filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(current_app.root_path, "static", "portfolio_pics", filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)

            project = PortfolioProject(
                user_id=current_user.id,
                title=form.title.data,
                description=form.description.data or None,
                project_url=form.project_url.data or None,
                image_url=filename
            )
            db.session.add(project)
            db.session.commit()
            flash("Portfolio project added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding portfolio project: {e}")
            flash("An error occurred.", "danger")
    return redirect(url_for("user.edit_profile"))

@user_bp.route("/remove_portfolio_project/<int:project_id>", methods=["POST"])
@login_required
def remove_portfolio_project(project_id):
    project = db.session.get(PortfolioProject, project_id)
    if project and project.user_id == current_user.id:
        db.session.delete(project)
        db.session.commit()
        flash("Project removed.", "info")
    return redirect(url_for("user.edit_profile"))


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

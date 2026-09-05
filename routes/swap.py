import logging
import urllib.parse
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request, Response
from flask_login import login_required, current_user

from extensions import db
from models import User, SwapRequest, Review, Skill, SkillEndorsement
from forms import ReviewForm
from utils import (
    award_xp,
    update_rating,
    check_and_award_badges,
    create_notification,
    XP_COMPLETE_SWAP,
    XP_REVIEW,
)

swap_bp = Blueprint("swap", __name__)
logger = logging.getLogger(__name__)


@swap_bp.route("/send_swap/<int:user_id>", methods=["GET", "POST"])
@login_required
def send_swap(user_id):
    try:
        if current_user.id == user_id:
            flash("You cannot send a request to yourself.", "warning")
            return redirect(url_for("user.dashboard"))

        recipient = db.session.get(User, user_id)
        if not recipient:
            abort(404)

        existing = SwapRequest.query.filter(
            SwapRequest.sender_id == current_user.id,
            SwapRequest.receiver_id == user_id,
            SwapRequest.status == "pending",
        ).first()

        if existing:
            flash(
                "You already have a pending request with this user.", "warning"
            )
            return redirect(url_for("user.dashboard"))

        proposed_time_str = request.form.get("proposed_time")
        proposed_time = None
        if proposed_time_str:
            try:
                proposed_time = datetime.fromisoformat(proposed_time_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        swap = SwapRequest(
            sender_id=current_user.id, receiver_id=user_id, status="pending", proposed_time=proposed_time
        )
        db.session.add(swap)
        db.session.commit()

        create_notification(
            user_id, f"{current_user.username} sent you a swap request!"
        )
        logger.info(
            f"Swap request sent from {current_user.username} to {recipient.username}"  # noqa: E501
        )
        flash("Swap request sent!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error sending swap request: {e}")
        flash("An error occurred. Please try again.", "danger")
    return redirect(url_for("swap.my_swaps"))


@swap_bp.route("/my_swaps")
@login_required
def my_swaps():
    try:
        received_requests = (
            SwapRequest.query.filter_by(receiver_id=current_user.id)
            .order_by(SwapRequest.created_at.desc())
            .all()
        )
        sent_requests = (
            SwapRequest.query.filter_by(sender_id=current_user.id)
            .order_by(SwapRequest.created_at.desc())
            .all()
        )
        return render_template(
            "my_swaps.html",
            received_requests=received_requests,
            sent_requests=sent_requests,
        )
    except Exception as e:
        logger.error(f"Error loading my_swaps for user {current_user.id}: {e}")
        flash("An error occurred.", "danger")
        return redirect(url_for("user.dashboard"))


@swap_bp.route("/accept/<int:swap_id>")
@login_required
def accept_swap(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or swap.receiver_id != current_user.id:
            abort(404 if not swap else 403)
        swap.status = "accepted"
        swap.accepted_at = datetime.utcnow()
        db.session.commit()
        create_notification(
            swap.sender_id,
            f"{current_user.username} accepted your swap request!",
        )
        flash("Swap accepted! You can now chat with the user.", "success")
    except Exception as e:  # noqa: F841
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for("swap.my_swaps"))


@swap_bp.route("/reject/<int:swap_id>")
@login_required
def reject_swap(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or swap.receiver_id != current_user.id:
            abort(404 if not swap else 403)
        swap.status = "rejected"
        db.session.commit()
        create_notification(
            swap.sender_id,
            f"{current_user.username} rejected your swap request.",
        )
        flash("Swap rejected.", "info")
    except Exception as e:  # noqa: F841
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for("swap.my_swaps"))


def get_google_calendar_url(swap, user):
    if not swap.proposed_time:
        return None
    peer = swap.receiver if user.id == swap.sender_id else swap.sender
    start_dt = swap.proposed_time.strftime("%Y%m%dT%H%M%SZ")
    end_dt = (swap.proposed_time + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    title = urllib.parse.quote(f"SkillSwap Session: {user.username} & {peer.username}")
    details = urllib.parse.quote(
        f"Live skill exchange session on SkillSwap Pro with {peer.username}.\n"
        f"Interactive Workspace & Video: {request.host_url.rstrip('/')}/swap/workspace/{swap.id}"
    )
    location = urllib.parse.quote(f"{request.host_url.rstrip('/')}/swap/workspace/{swap.id}")
    return f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={start_dt}/{end_dt}&details={details}&location={location}"


@swap_bp.app_template_global()
def google_calendar_link(swap, user):
    return get_google_calendar_url(swap, user)


@swap_bp.route("/calendar/<int:swap_id>.ics")
@login_required
def export_calendar_ics(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [swap.sender_id, swap.receiver_id]:
            abort(404 if not swap else 403)
        peer = swap.receiver if current_user.id == swap.sender_id else swap.sender
        start_time = swap.proposed_time or (datetime.utcnow() + timedelta(hours=2))
        end_time = start_time + timedelta(hours=1)

        dt_format = "%Y%m%dT%H%M%SZ"
        start_str = start_time.strftime(dt_format)
        end_str = end_time.strftime(dt_format)
        now_str = datetime.utcnow().strftime(dt_format)
        workspace_url = f"{request.host_url.rstrip('/')}/swap/workspace/{swap.id}"

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//SkillSwap Pro//Session Booking//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "BEGIN:VEVENT",
            f"UID:skillswap-{swap.id}@{request.host}",
            f"DTSTAMP:{now_str}",
            f"DTSTART:{start_str}",
            f"DTEND:{end_str}",
            f"SUMMARY:SkillSwap Session with {peer.username}",
            f"DESCRIPTION:Peer knowledge exchange session between {current_user.username} and {peer.username}. Join workspace: {workspace_url}",
            f"LOCATION:{workspace_url}",
            "STATUS:CONFIRMED",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        ics_content = "\r\n".join(ics_lines)

        return Response(
            ics_content,
            mimetype="text/calendar",
            headers={"Content-Disposition": f"attachment; filename=skillswap_session_{swap.id}.ics"},
        )
    except Exception as e:
        logger.error(f"Error generating calendar .ics: {e}")
        flash("Could not export calendar file.", "danger")
        return redirect(url_for("swap.my_swaps"))


@swap_bp.route("/workspace/<int:swap_id>")
@login_required
def workspace(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [swap.sender_id, swap.receiver_id]:
            abort(404 if not swap else 403)
        peer = swap.receiver if current_user.id == swap.sender_id else swap.sender
        gcal_url = get_google_calendar_url(swap, current_user)
        return render_template("workspace.html", swap=swap, peer=peer, gcal_url=gcal_url)
    except Exception as e:
        logger.error(f"Error loading workspace for swap {swap_id}: {e}")
        flash("Could not access workspace.", "danger")
        return redirect(url_for("swap.my_swaps"))


@swap_bp.route("/workspace/<int:swap_id>/save_notes", methods=["POST"])
@login_required
def save_workspace_notes(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [swap.sender_id, swap.receiver_id]:
            return {"status": "error", "message": "Unauthorized"}, 403
        data = request.get_json(silent=True) or request.form
        notes = data.get("notes", "")
        swap.session_notes = notes
        db.session.commit()
        return {"status": "success", "message": "Notes saved"}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving workspace notes: {e}")
        return {"status": "error", "message": str(e)}, 500


@swap_bp.route("/complete/<int:swap_id>")
@login_required
def complete_swap(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [
            swap.sender_id,
            swap.receiver_id,
        ]:
            abort(404 if not swap else 403)
        if swap.status != "accepted":
            flash("Only accepted swaps can be completed.", "warning")
            return redirect(url_for("swap.my_swaps"))
        swap.status = "completed"
        swap.completed_at = datetime.utcnow()

        # Settling Time-Bank Credits (+1 Credit to both active knowledge traders)
        if not swap.credits_settled:
            if swap.sender:
                swap.sender.credits = (swap.sender.credits or 0) + 1
            if swap.receiver:
                swap.receiver.credits = (swap.receiver.credits or 0) + 1
            swap.credits_settled = True

        award_xp(swap.sender, XP_COMPLETE_SWAP)
        award_xp(swap.receiver, XP_COMPLETE_SWAP)
        check_and_award_badges(swap.sender)
        check_and_award_badges(swap.receiver)
        db.session.commit()
        flash(
            f"Swap completed! Both users earned {XP_COMPLETE_SWAP} XP and +1 Time-Bank Credit 🪙🎉",
            "success",
        )
    except Exception as e:  # noqa: F841
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for("swap.my_swaps"))


@swap_bp.route("/submit_review/<int:user_id>", methods=["POST"])
@login_required
def submit_review(user_id):
    try:
        form = ReviewForm()
        if form.validate_on_submit():
            reviewed_user = db.session.get(User, user_id)
            if not reviewed_user:
                abort(404)
            existing_review = Review.query.filter_by(
                reviewer_id=current_user.id, reviewed_user_id=user_id
            ).first()
            if existing_review:
                flash("You have already reviewed this user.", "warning")
                return redirect(
                    url_for("user.profile", username=reviewed_user.username)
                )
            review = Review(
                reviewer_id=current_user.id,
                reviewed_user_id=user_id,
                rating=form.rating.data,
                comment=form.comment.data,
            )
            db.session.add(review)

            # Peer-Verified Skill Endorsement
            endorsed_skill_id = request.form.get("endorsed_skill_id", type=int)
            endorsed_skill_name = None
            if endorsed_skill_id:
                skill = db.session.get(Skill, endorsed_skill_id)
                if skill and skill.user_id == reviewed_user.id:
                    endorsement = SkillEndorsement(
                        skill_id=skill.id,
                        endorser_id=current_user.id,
                        swap_id=None,
                    )
                    db.session.add(endorsement)
                    skill.endorsements_count = (skill.endorsements_count or 0) + 1
                    endorsed_skill_name = skill.name
                    award_xp(reviewed_user, 25)  # +25 XP bonus for verified skill endorsement

            db.session.commit()
            update_rating(reviewed_user)
            award_xp(reviewed_user, XP_REVIEW)
            check_and_award_badges(reviewed_user)

            if endorsed_skill_name:
                flash(f"Review submitted! You officially endorsed {reviewed_user.username}'s skill '{endorsed_skill_name}' ✨", "success")
            else:
                flash("Review submitted successfully!", "success")
        else:
            for error in form.errors.values():
                flash(str(error), "danger")
    except Exception as e:  # noqa: F841
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for("user.dashboard"))

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import User, SwapRequest, Review
from forms import ReviewForm
from utils import award_xp, update_rating, check_and_award_badges, create_notification, XP_COMPLETE_SWAP, XP_REVIEW

swap_bp = Blueprint('swap', __name__)
logger = logging.getLogger(__name__)

@swap_bp.route("/send_swap/<int:user_id>")
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
            SwapRequest.status == "pending"
        ).first()

        if existing:
            flash("You already have a pending request with this user.", "warning")
            return redirect(url_for("user.dashboard"))

        swap = SwapRequest(sender_id=current_user.id, receiver_id=user_id, status="pending")
        db.session.add(swap)
        db.session.commit()

        create_notification(user_id, f"{current_user.username} sent you a swap request!")
        logger.info(f"Swap request sent from {current_user.username} to {recipient.username}")
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
        received_requests = SwapRequest.query.filter_by(receiver_id=current_user.id).order_by(SwapRequest.created_at.desc()).all()
        sent_requests = SwapRequest.query.filter_by(sender_id=current_user.id).order_by(SwapRequest.created_at.desc()).all()
        return render_template("my_swaps.html", received_requests=received_requests, sent_requests=sent_requests)
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
        create_notification(swap.sender_id, f"{current_user.username} accepted your swap request!")
        flash("Swap accepted! You can now chat with the user.", "success")
    except Exception as e:
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
        create_notification(swap.sender_id, f"{current_user.username} rejected your swap request.")
        flash("Swap rejected.", "info")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for("swap.my_swaps"))

@swap_bp.route("/complete/<int:swap_id>")
@login_required
def complete_swap(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [swap.sender_id, swap.receiver_id]:
            abort(404 if not swap else 403)
        if swap.status != "accepted":
            flash("Only accepted swaps can be completed.", "warning")
            return redirect(url_for("swap.my_swaps"))
        swap.status = "completed"
        swap.completed_at = datetime.utcnow()
        award_xp(swap.sender, XP_COMPLETE_SWAP)
        award_xp(swap.receiver, XP_COMPLETE_SWAP)
        check_and_award_badges(swap.sender)
        check_and_award_badges(swap.receiver)
        db.session.commit()
        flash(f"Swap completed! Both users earned {XP_COMPLETE_SWAP} XP 🎉", "success")
    except Exception as e:
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
            existing_review = Review.query.filter_by(reviewer_id=current_user.id, reviewed_user_id=user_id).first()
            if existing_review:
                flash("You have already reviewed this user.", "warning")
                return redirect(url_for("user.profile", username=reviewed_user.username))
            review = Review(reviewer_id=current_user.id, reviewed_user_id=user_id, rating=form.rating.data, comment=form.comment.data)
            db.session.add(review)
            db.session.commit()
            update_rating(reviewed_user)
            award_xp(reviewed_user, XP_REVIEW)
            check_and_award_badges(reviewed_user)
            flash("Review submitted successfully!", "success")
        else:
            for error in form.errors.values():
                flash(str(error), "danger")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for("user.dashboard"))

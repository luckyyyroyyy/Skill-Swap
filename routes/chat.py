import logging
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from extensions import db
from models import User, SwapRequest, ChatMessage, Notification
from forms import ChatMessageForm

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)


@chat_bp.route("/chat/<int:swap_id>", methods=["GET", "POST"])
@login_required
def chat_view(swap_id):
    try:
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [
            swap.sender_id,
            swap.receiver_id,
        ]:
            abort(404 if not swap else 403)
        if swap.status != "accepted":
            flash("Chat not available for this swap.", "warning")
            return redirect(url_for("swap.my_swaps"))

        other_user = db.session.get(
            User,
            (
                swap.receiver_id
                if current_user.id == swap.sender_id
                else swap.sender_id
            ),
        )
        if not other_user:
            abort(404)

        form = ChatMessageForm()
        if form.validate_on_submit():
            try:
                message = ChatMessage(
                    swap_id=swap.id,
                    sender_id=current_user.id,
                    message=form.content.data,
                )
                db.session.add(message)
                db.session.commit()
                return redirect(url_for("chat.chat_view", swap_id=swap.id))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error sending message: {e}")
                flash("Error sending message.", "danger")

        messages = (
            ChatMessage.query.filter_by(swap_id=swap.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        for msg in messages:
            if msg.sender_id != current_user.id:
                msg.is_read = True
        db.session.commit()

        return render_template(
            "chat.html",
            swap=swap,
            messages=messages,
            other_user=other_user,
            form=form,
        )
    except Exception as e:
        logger.error(f"Error in chat route: {e}")
        flash("An error occurred.", "danger")
        return redirect(url_for("swap.my_swaps"))


@chat_bp.route("/notifications")
@login_required
def notifications():
    notes = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    # Mark as read
    for note in notes:
        note.is_read = True
    db.session.commit()
    return render_template("notifications.html", notes=notes)

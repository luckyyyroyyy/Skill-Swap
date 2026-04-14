import logging
from flask import request
from flask_login import current_user
from flask_socketio import join_room, emit
from extensions import socketio, db
from models import ChatMessage, SwapRequest

logger = logging.getLogger(__name__)

@socketio.on("join_personal_room")
def handle_join_personal_room(user_id):
    """Called in base.html for receiving toast notifications"""
    join_room(user_id)
    logger.info(f"User {user_id} joined their personal room.")

@socketio.on("join_chat_room")
def handle_join_chat_room(data):
    """Called when user enters a specific swap chat page."""
    if not current_user.is_authenticated:
        return
    swap_id = data.get("swap_id")
    if swap_id:
        room = f"swap_{swap_id}"
        join_room(room)
        logger.info(f"User {current_user.id} joined chat room: {room}")

@socketio.on("send_room_message")
def handle_send_room_message(data):
    """Called when user sends a message via WebSockets."""
    if not current_user.is_authenticated:
        return

    swap_id = data.get("swap_id")
    content = data.get("content")

    if not swap_id or not content:
        return

    try:
        # Verify access
        swap = db.session.get(SwapRequest, swap_id)
        if not swap or current_user.id not in [swap.sender_id, swap.receiver_id]:
            return

        # Save message
        message = ChatMessage(
            swap_id=swap.id,
            sender_id=current_user.id,
            message=content
        )
        db.session.add(message)
        db.session.commit()

        # Broadcast to room
        room = f"swap_{swap_id}"
        emit(
            "new_room_message", 
            {
                "sender_id": current_user.id,
                "sender_name": current_user.username,
                "message": content,
                "avatar": current_user.username[0].upper()
            }, 
            room=room,
            include_self=True
        )

        # Fire off a toast notification to the other user if they are online but not strictly in the room
        other_user_id = swap.receiver_id if current_user.id == swap.sender_id else swap.sender_id
        emit(
            "new_notification",
            {"message": f"New message from {current_user.username}"},
            room=str(other_user_id)
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error handling send_room_message: {e}")

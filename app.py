import os
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables BEFORE importing config
load_dotenv()

from extensions import db, login_manager, migrate, mail
from flask_socketio import SocketIO, join_room  # noqa: F401
from flask_login import current_user
from datetime import datetime
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("skillswap.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration based on environment
env = os.getenv("FLASK_ENV", "development")
app.config.from_object(config.get(env, config["default"]))

# Limit file uploads to 2MB
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

db.init_app(app)
migrate.init_app(app, db, render_as_batch=True)
mail.init_app(app)
login_manager.init_app(app)

# 🔥 Initialize CSRF Protection
csrf = CSRFProtect(app)

# 🔥 Initialize Limiter
from extensions import limiter, socketio  # noqa: E402

limiter.init_app(app)

# 🔥 Initialize SocketIO
socketio.init_app(app, cors_allowed_origins="*")

# Import models and routes AFTER initializing app
import models  # noqa: E402, F401
from routes import main_bp, auth_bp, user_bp, swap_bp, chat_bp  # noqa: E402

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(swap_bp)
app.register_blueprint(chat_bp)

# For readability in the current file if needed (optional, but good for context)  # noqa: E501
from models import ChatMessage, SwapRequest, Badge  # noqa: E402

# ----------------------------
# DATABASE MIGRATIONS HANDELED VIA FLASK-MIGRATE
# ----------------------------


# ----------------------------
# 🔔 UNREAD COUNT CONTEXT
# ----------------------------
@app.context_processor
def inject_unread_count():
    if current_user.is_authenticated:
        unread_count = (
            ChatMessage.query.join(SwapRequest)
            .filter(
                ChatMessage.sender_id != current_user.id,
                ChatMessage.is_read is False,
                (SwapRequest.sender_id == current_user.id)
                | (SwapRequest.receiver_id == current_user.id),
            )
            .count()
        )
    else:
        unread_count = 0

    return dict(unread_count=unread_count)


# ----------------------------
# 🔥 SOCKET.IO EVENTS
# ----------------------------


@socketio.on("join_room")
def handle_join_room(room):
    join_room(str(room))


@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated:
        return

    message = ChatMessage(
        swap_id=data["swap_id"],
        sender_id=current_user.id,
        message=data["message"],
        created_at=datetime.utcnow(),
        is_read=False,
    )

    db.session.add(message)
    db.session.commit()

    socketio.emit(
        "receive_message",
        {"message": data["message"], "sender_id": current_user.id},
        room=str(data["swap_id"]),
    )


# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

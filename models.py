from datetime import datetime
from extensions import db
from flask_login import UserMixin


# =========================
# USER MODEL
# =========================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    bio = db.Column(db.Text)
    xp = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(50), default="Beginner")
    profile_pic = db.Column(db.String(200), default="default.png")
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sent_requests = db.relationship(
        "SwapRequest",
        foreign_keys="SwapRequest.sender_id",
        backref="sender",
        lazy=True,
        cascade="all, delete",
    )
    received_requests = db.relationship(
        "SwapRequest",
        foreign_keys="SwapRequest.receiver_id",
        backref="receiver",
        lazy=True,
        cascade="all, delete",
    )
    badges = db.relationship(
        "UserBadge", backref="user", lazy=True, cascade="all, delete"
    )
    skills = db.relationship(
        "Skill", backref="user", lazy=True, cascade="all, delete"
    )

    # Level System
    def get_level(self):
        if self.xp < 100:
            return "Beginner 🌱"
        elif self.xp < 300:
            return "Skilled 🚀"
        elif self.xp < 600:
            return "Expert 🔥"
        else:
            return "Master 👑"


# =========================
# SKILL MODEL
# =========================
class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="Other")
    type = db.Column(db.String(20), nullable=False)  # offer / want

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )


# =========================
# SWAP REQUEST MODEL
# =========================
class SwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    receiver_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    status = db.Column(
        db.String(20), default="pending"
    )  # pending / accepted / rejected / completed

    accepted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# REVIEW MODEL
# =========================
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reviewer_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    reviewed_user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# BADGE MODEL
# =========================
class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # emoji or icon class


# =========================
# USER BADGE (MANY-TO-MANY)
# =========================
class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    badge_id = db.Column(
        db.Integer, db.ForeignKey("badge.id"), nullable=False, index=True
    )

    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    badge = db.relationship("Badge")


# =========================
# NOTIFICATION MODEL
# =========================
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="notifications")


# =========================
# CHAT MESSAGE MODEL
# =========================
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    swap_id = db.Column(
        db.Integer,
        db.ForeignKey("swap_request.id"),
        nullable=False,
        index=True,
    )

    sender_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship("User")
    swap = db.relationship("SwapRequest", backref="messages")

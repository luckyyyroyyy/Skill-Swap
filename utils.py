import logging
from models import (  # noqa: F401
    User,
    Skill,
    Review,
    SwapRequest,
    Badge,
    UserBadge,
    Notification,
)
from extensions import db
from sqlalchemy import or_

logger = logging.getLogger(__name__)

# =====================
# XP AND SCORING CONSTANTS
# =====================
XP_ADD_SKILL = 10
XP_COMPLETE_SWAP = 50
XP_REVIEW = 50

# Match scoring multipliers
MATCH_SKILL_MULTIPLIER = 25  # Points per mutual skill
MATCH_RATING_MULTIPLIER = 10  # Points per rating point
MATCH_XP_DIVISOR = 50  # XP points divided by this


# =========================
# XP SYSTEM
# =========================
def award_xp(user, points):
    """Award XP points to a user."""
    try:
        user.xp += points
        db.session.commit()
        logger.info(f"Awarded {points} XP to user {user.username}")
    except Exception as e:
        logger.error(f"Failed to award XP to user {user.id}: {e}")
        db.session.rollback()
        raise


# =========================
# RATING SYSTEM
# =========================
def update_rating(user):
    """Calculate and update user's average rating."""
    try:
        reviews = Review.query.filter_by(reviewed_user_id=user.id).all()

        if reviews:
            total = sum(r.rating for r in reviews)
            user.rating = round(total / len(reviews), 2)
            user.total_reviews = len(reviews)
            db.session.commit()
            logger.info(
                f"Updated rating for user {user.username}: {user.rating}"
            )
        else:
            user.rating = 0.0
            user.total_reviews = 0
            db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update rating for user {user.id}: {e}")
        db.session.rollback()
        raise


# =========================
# MATCHING SYSTEM
# =========================
def calculate_match_score(user_a, user_b):
    """
    Calculate compatibility score between two users.

    Factors:
    - Mutual skills: User A wants what B offers and vice versa
    - User B's rating/reputation
    - User B's experience level (XP)
    """
    try:
        # Get skills for both users
        a_wants = {s.name.lower() for s in user_a.skills if s.type == "want"}
        a_offers = {s.name.lower() for s in user_a.skills if s.type == "offer"}

        b_wants = {s.name.lower() for s in user_b.skills if s.type == "want"}
        b_offers = {s.name.lower() for s in user_b.skills if s.type == "offer"}

        # Calculate mutual matches
        mutual_1 = len(a_wants & b_offers)  # A wants what B offers
        mutual_2 = len(b_wants & a_offers)  # B wants what A offers

        # Weighted scoring
        skill_score = (mutual_1 + mutual_2) * MATCH_SKILL_MULTIPLIER
        rating_score = (user_b.rating or 0) * MATCH_RATING_MULTIPLIER
        xp_score = (user_b.xp or 0) / MATCH_XP_DIVISOR

        total_score = skill_score + rating_score + xp_score
        return round(total_score)
    except Exception as e:
        logger.error(f"Error calculating match score: {e}")
        return 0


def find_matches(current_user, limit=None, category=None):
    """
    Find compatible users for skill swaps.

    Args:
        current_user: User object to find matches for
        limit: Maximum number of matches to return
        category: Optional category string to filter by offered skills

    Returns:
        List of (user, score) tuples sorted by score descending
    """
    try:
        # Get all other users (database level filtering)
        users = User.query.filter(User.id != current_user.id).all()

        if category:
            filtered_users = []
            for u in users:
                offers = [s for s in u.skills if s.type == "offer"]
                if any(s.category == category for s in offers):
                    filtered_users.append(u)
            users = filtered_users

        matches = []
        for user in users:
            score = calculate_match_score(current_user, user)
            if score > 0:
                matches.append((user, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        if limit:
            matches = matches[:limit]

        logger.info(
            f"Found {len(matches)} matches for user {current_user.username}"
        )
        return matches
    except Exception as e:
        logger.error(f"Error finding matches for user {current_user.id}: {e}")
        return []


# =========================
# BADGE SYSTEM
# =========================
def check_and_award_badges(user):
    """
    Check if user qualifies for any new badges and award them.

    Badges:
    - First Swap: Completed 1 swap
    - Rising Star: Earned 200 XP
    - Skill Master: Earned 500 XP
    - Trusted Mentor: Received 5 reviews
    """
    try:
        # Count completed swaps
        completed_swaps = SwapRequest.query.filter(
            SwapRequest.status == "completed",
            or_(
                SwapRequest.sender_id == user.id,
                SwapRequest.receiver_id == user.id,
            ),
        ).count()

        reviews_count = user.total_reviews or 0

        # Get already earned badges
        earned_badges = UserBadge.query.filter_by(user_id=user.id).all()
        earned_badge_ids = {b.badge_id for b in earned_badges}

        all_badges = Badge.query.all()

        new_badges = []
        for badge in all_badges:
            if badge.id in earned_badge_ids:
                continue

            # Check badge conditions
            should_award = False
            if badge.name == "First Swap" and completed_swaps >= 1:
                should_award = True
            elif badge.name == "Rising Star" and user.xp >= 200:
                should_award = True
            elif badge.name == "Skill Master" and user.xp >= 500:
                should_award = True
            elif badge.name == "Trusted Mentor" and reviews_count >= 5:
                should_award = True

            if should_award:
                new_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                db.session.add(new_badge)
                new_badges.append(badge.name)

        if new_badges:
            db.session.commit()
            logger.info(
                f"Awarded badges to user {user.username}: {', '.join(new_badges)}"  # noqa: E501
            )

    except Exception as e:
        logger.error(f"Error awarding badges to user {user.id}: {e}")
        db.session.rollback()
        raise


# =========================
# NOTIFICATION SYSTEM
# =========================
def create_notification(user_id, message):
    """
    Create a notification for a user.

    Args:
        user_id: ID of user to notify
        message: Notification message
    """
    try:
        from extensions import socketio

        notification = Notification(user_id=user_id, message=message)
        db.session.add(notification)
        db.session.commit()
        logger.info(f"Created notification for user {user_id}")

        # Emit real-time notification
        socketio.emit(
            "new_notification", {"message": message}, room=f"user_{user_id}"
        )
    except Exception as e:
        logger.error(f"Failed to create notification for user {user_id}: {e}")
        db.session.rollback()

import logging
import difflib
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
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
        def get_similarity(s1, s2):
            return difflib.SequenceMatcher(None, s1, s2).ratio()

        a_wants = [(s.name.lower(), getattr(s, 'proficiency_level', 'Beginner')) for s in user_a.skills if s.type == "want"]
        a_offers = [(s.name.lower(), getattr(s, 'proficiency_level', 'Beginner')) for s in user_a.skills if s.type == "offer"]

        b_wants = [(s.name.lower(), getattr(s, 'proficiency_level', 'Beginner')) for s in user_b.skills if s.type == "want"]
        b_offers = [(s.name.lower(), getattr(s, 'proficiency_level', 'Beginner')) for s in user_b.skills if s.type == "offer"]

        def calc_mutual_score(wants, offers):
            score = 0
            for w_name, w_prof in wants:
                best_match = 0
                for o_name, o_prof in offers:
                    sim = get_similarity(w_name, o_name)
                    if w_name in o_name or o_name in w_name:
                        sim = max(sim, 0.85)

                    if sim > 0.6:
                        prof_bonus = 0
                        if w_prof in ['Beginner', 'Intermediate'] and o_prof == 'Expert':
                            prof_bonus = 0.25
                        elif w_prof == 'Beginner' and o_prof == 'Intermediate':
                            prof_bonus = 0.15
                        best_match = max(best_match, sim + prof_bonus)
                score += best_match
            return score

        mutual_1 = calc_mutual_score(a_wants, b_offers)
        mutual_2 = calc_mutual_score(b_wants, a_offers)

        # Timezone bonus
        timezone_bonus = 0
        if getattr(user_a, 'timezone', None) and getattr(user_b, 'timezone', None):
            if user_a.timezone == user_b.timezone and user_a.timezone != "UTC":
                timezone_bonus = 5

        # Weighted scoring (modified for semantic scores)
        skill_score = (mutual_1 + mutual_2) * 30  # Adjust multiplier for semantic ratio
        rating_score = (user_b.rating or 0) * 8
        xp_score = (user_b.xp or 0) / MATCH_XP_DIVISOR

        total_score = skill_score + rating_score + xp_score + timezone_bonus
        return min(round(total_score), 100)  # Cap at 100%
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


# =========================
# TIMEZONE UTILITIES
# =========================
def convert_availability_to_viewer_tz(slot, owner_tz_str, viewer_tz_str):
    """
    Converts an availability slot from the owner's timezone to the viewer's timezone.
    Returns (new_day_of_week, new_start_time, new_end_time)
    """
    if owner_tz_str == viewer_tz_str:
        return slot.day_of_week, slot.start_time, slot.end_time

    try:
        owner_tz = ZoneInfo(owner_tz_str if owner_tz_str != "Other" else "UTC")
        viewer_tz = ZoneInfo(viewer_tz_str if viewer_tz_str != "Other" else "UTC")
    except Exception as e:
        logger.error(f"Invalid timezone strings during conversion: {e}")
        return slot.day_of_week, slot.start_time, slot.end_time
    
    now = datetime.now(owner_tz)
    days_ahead = slot.day_of_week - now.weekday()
    if days_ahead < 0:
        days_ahead += 7
    
    target_date = now + timedelta(days=days_ahead)
    
    dt_start = datetime.combine(target_date.date(), slot.start_time, tzinfo=owner_tz)
    dt_end = datetime.combine(target_date.date(), slot.end_time, tzinfo=owner_tz)
    
    # Handle overnight slots gracefully by ensuring end > start date-wise if needed
    if slot.end_time < slot.start_time:
        dt_end += timedelta(days=1)

    viewer_dt_start = dt_start.astimezone(viewer_tz)
    viewer_dt_end = dt_end.astimezone(viewer_tz)
    
    return viewer_dt_start.weekday(), viewer_dt_start.time(), viewer_dt_end.time()

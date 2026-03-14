import pytest
import os  # noqa: F401
from app import app, db
from models import (  # noqa: F401
    User,
    Skill,
    SwapRequest,
    Review,
    Badge,
    UserBadge,
    Notification,
    ChatMessage,
)
from werkzeug.security import generate_password_hash
from config import config


@pytest.fixture
def test_client():
    """Create a test client for the app."""
    app.config.from_object(config["testing"])

    with app.app_context():
        # Clear database to prevent unique constraint failures
        db.drop_all()
        db.create_all()
        # Create default badges that exist by default in app
        from models import Badge

        default_badges = [
            Badge(
                name="First Swap",
                description="Completed first swap",
                icon="🎉",
            ),
            Badge(name="Rising Star", description="Earned 200 XP", icon="⭐"),
            Badge(name="Skill Master", description="Earned 500 XP", icon="🔥"),
            Badge(
                name="Trusted Mentor",
                description="Received 5 reviews",
                icon="🏆",
            ),
        ]
        db.session.add_all(default_badges)
        db.session.commit()

        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(test_client):
    """Create a test user."""
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            password=generate_password_hash("testpassword123"),
        )
        db.session.add(user)
        db.session.commit()
        # Detach user so it can be merged in test sessions
        db.session.refresh(user)
        db.session.expunge(user)
        return user


@pytest.fixture
def test_user2(test_client):
    """Create a second test user."""
    with app.app_context():
        user = User(
            username="testuser2",
            email="test2@example.com",
            password=generate_password_hash("testpassword123"),
        )
        db.session.add(user)
        db.session.commit()
        # Detach user so it can be merged in test sessions
        db.session.refresh(user)
        db.session.expunge(user)
        return user


class TestAuth:
    """Test authentication routes."""

    def test_landing_page(self, test_client):
        """Test landing page loads."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_register_get(self, test_client):
        """Test registration page loads."""
        response = test_client.get("/register")
        assert response.status_code == 200

    def test_register_post_invalid(self, test_client):
        """Test registration with invalid data."""
        response = test_client.post(
            "/register",
            data={
                "username": "a",  # Too short
                "email": "invalidemail",
                "password": "short",
                "confirm_password": "short",
            },
        )
        # Should fail validation
        assert response.status_code in [200, 400]

    def test_login_get(self, test_client):
        """Test login page loads."""
        response = test_client.get("/login")
        assert response.status_code == 200


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, test_user):
        """Test user is created correctly."""
        with app.app_context():
            # Merge detached user into current session
            user = db.session.merge(test_user)
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.xp == 0
            assert user.rating == 0.0

    def test_user_level(self, test_user):
        """Test user level calculation."""
        with app.app_context():
            user = db.session.merge(test_user)
            assert user.get_level() == "Beginner 🌱"

            user.xp = 150
            assert user.get_level() == "Skilled 🚀"

            user.xp = 400
            assert user.get_level() == "Expert 🔥"

            user.xp = 700
            assert user.get_level() == "Master 👑"


class TestSkillModel:
    """Test Skill model."""

    def test_skill_creation(self, test_user):
        """Test skill is created correctly."""
        with app.app_context():
            skill = Skill(
                name="Python Programming", type="offer", user_id=test_user.id
            )
            db.session.add(skill)
            db.session.commit()

            assert skill.name == "Python Programming"
            assert skill.type == "offer"
            assert skill.user_id == test_user.id


class TestSwapRequestModel:
    """Test SwapRequest model."""

    def test_swap_request_creation(self, test_user, test_user2):
        """Test swap request is created correctly."""
        with app.app_context():
            swap = SwapRequest(
                sender_id=test_user.id,
                receiver_id=test_user2.id,
                status="pending",
            )
            db.session.add(swap)
            db.session.commit()

            assert swap.sender_id == test_user.id
            assert swap.receiver_id == test_user2.id
            assert swap.status == "pending"


class TestReviewModel:
    """Test Review model."""

    def test_review_creation(self, test_user, test_user2):
        """Test review is created correctly."""
        with app.app_context():
            review = Review(
                reviewer_id=test_user.id,
                reviewed_user_id=test_user2.id,
                rating=5,
                comment="Great tutor!",
            )
            db.session.add(review)
            db.session.commit()

            assert review.rating == 5
            assert review.comment == "Great tutor!"


class TestMatchingAlgorithm:
    """Test skill matching algorithm."""

    def test_match_score_calculation(self, test_user, test_user2):
        """Test match score calculation."""
        from utils import calculate_match_score

        with app.app_context():
            # Add skills to test_user (wants Python)
            skill1 = Skill(name="python", type="want", user_id=test_user.id)
            db.session.add(skill1)

            # Add skills to test_user2 (offers Python)
            skill2 = Skill(name="python", type="offer", user_id=test_user2.id)
            db.session.add(skill2)
            db.session.commit()

            # Formally refresh objects and calculate match score
            merged_user1 = db.session.merge(test_user)
            merged_user2 = db.session.merge(test_user2)
            score = calculate_match_score(merged_user1, merged_user2)
            assert (
                score > 0
            )  # Should have positive score due to matching skills

    def test_find_matches(self, test_user, test_user2):
        """Test find matches function."""
        from utils import find_matches

        with app.app_context():
            # Add skills
            skill1 = Skill(
                name="javascript", type="want", user_id=test_user.id
            )
            skill2 = Skill(
                name="javascript", type="offer", user_id=test_user2.id
            )
            db.session.add_all([skill1, skill2])
            db.session.commit()

            merged_user1 = db.session.merge(test_user)
            matches = find_matches(merged_user1)
            assert len(matches) > 0
            assert matches[0][0].id == test_user2.id


class TestBadgeSystem:
    """Test badge system."""

    def test_badge_creation(self, test_client):
        """Test badge creation."""
        with app.app_context():
            # Test badge already exists from default initialization
            badge = Badge.query.filter_by(name="First Swap").first()
            assert badge is not None
            assert badge.name == "First Swap"

    def test_user_badge_creation(self, test_client, test_user):
        """Test user badge assignment."""
        with app.app_context():
            # Get default badge
            badge = Badge.query.filter_by(name="First Swap").first()

            user_badge = UserBadge(user_id=test_user.id, badge_id=badge.id)
            db.session.add(user_badge)
            db.session.commit()

            assert user_badge.user_id == test_user.id
            assert user_badge.badge_id == badge.id


class TestNotificationSystem:
    """Test notification system."""

    def test_notification_creation(self, test_user):
        """Test notification creation."""
        with app.app_context():
            notification = Notification(
                user_id=test_user.id,
                message="You have a new swap request!",
                is_read=False,
            )
            db.session.add(notification)
            db.session.commit()

            assert notification.message == "You have a new swap request!"
            assert notification.is_read is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

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
    SkillEndorsement,
)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
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

    def test_register_post_success(self, test_client):
        """Test registration redirects to login page instead of dashboard."""
        response = test_client.post(
            "/register",
            data={
                "username": "freshuser",
                "email": "freshuser@example.com",
                "password": "validpassword123",
                "confirm_password": "validpassword123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


    def test_login_get(self, test_client):
        """Test login page loads."""
        response = test_client.get("/login")
        assert response.status_code == 200

    def test_login_ajax_success(self, test_client, test_user):
        """Test AJAX login returns JSON with username for Apple animation."""
        response = test_client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "testpassword123",
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["username"] == "testuser"
        assert "/dashboard" in data["redirect_url"]

    def test_login_ajax_invalid(self, test_client, test_user):
        """Test AJAX login with incorrect password returns 401 JSON."""
        response = test_client.post(
            "/login",
            data={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "Invalid email or password" in data["message"]


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


class TestDashboardAndSkillManagement:
    """Test dashboard loading and skill removal."""

    def test_dashboard_authenticated(self, test_client, test_user):
        """Test dashboard renders for authenticated user."""
        test_client.post(
            "/login",
            data={"email": "test@example.com", "password": "testpassword123"},
        )
        response = test_client.get("/dashboard")
        assert response.status_code == 200
        assert b"Cyber Command" in response.data or b"Two-Domain Skill Studio" in response.data

    def test_delete_skill(self, test_client, test_user):
        """Test user can delete a skill they created."""
        test_client.post(
            "/login",
            data={"email": "test@example.com", "password": "testpassword123"},
        )
        with app.app_context():
            skill = Skill(name="Rust", category="Tech", type="offer", proficiency_level="Intermediate", user_id=test_user.id)
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        response = test_client.post(f"/delete_skill/{skill_id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Removed skill Rust" in response.data

        with app.app_context():
            deleted = db.session.get(Skill, skill_id)
            assert deleted is None


class TestRoadmapInnovations:
    """Test the 5 high-impact roadmap improvements."""

    def test_pwa_assets(self, test_client):
        """Test PWA manifest and service worker are accessible both at root and /static/."""
        for path in ["/manifest.json", "/static/manifest.json"]:
            res = test_client.get(path)
            assert res.status_code == 200
            assert b"SkillSwap Pro" in res.data

        for path in ["/sw.js", "/static/sw.js"]:
            res = test_client.get(path)
            assert res.status_code == 200
            assert b"skillswap" in res.data

    def test_calendar_ics_export(self, test_client, test_user, test_user2):
        """Test RFC 5545 .ics calendar export."""
        test_client.post(
            "/login",
            data={"email": "test@example.com", "password": "testpassword123"},
        )
        with app.app_context():
            swap = SwapRequest(
                sender_id=test_user.id,
                receiver_id=test_user2.id,
                status="accepted",
                proposed_time=datetime.utcnow() + timedelta(days=1),
            )
            db.session.add(swap)
            db.session.commit()
            swap_id = swap.id

        response = test_client.get(f"/calendar/{swap_id}.ics")
        assert response.status_code == 200
        assert response.mimetype == "text/calendar"
        assert b"BEGIN:VCALENDAR" in response.data
        assert b"SUMMARY:SkillSwap Session" in response.data
        assert b"END:VCALENDAR" in response.data

    def test_workspace_access_and_notes(self, test_client, test_user, test_user2):
        """Test workspace authorization and session notes autosave."""
        test_client.post(
            "/login",
            data={"email": "test@example.com", "password": "testpassword123"},
        )
        with app.app_context():
            swap = SwapRequest(
                sender_id=test_user.id,
                receiver_id=test_user2.id,
                status="accepted",
            )
            db.session.add(swap)
            db.session.commit()
            swap_id = swap.id

        # Access workspace as participant
        response = test_client.get(f"/workspace/{swap_id}")
        assert response.status_code == 200
        assert b"Code Sandbox" in response.data
        assert b"Markdown Scratchpad" in response.data

        # Save collaborative notes
        notes_payload = {"notes": "# Architecture Review\n- Modular components\n- Realtime websockets"}
        save_res = test_client.post(f"/workspace/{swap_id}/save_notes", json=notes_payload)
        assert save_res.status_code == 200
        assert save_res.get_json()["status"] == "success"

        with app.app_context():
            saved_swap = db.session.get(SwapRequest, swap_id)
            assert "Modular components" in saved_swap.session_notes

    def test_complete_swap_settles_timebank_credits(self, test_client, test_user, test_user2):
        """Test completing swap settles +1 time-bank skill credit to both users."""
        test_client.post(
            "/login",
            data={"email": "test@example.com", "password": "testpassword123"},
        )
        with app.app_context():
            u1 = db.session.get(User, test_user.id)
            u2 = db.session.get(User, test_user2.id)
            u1.credits = 3
            u2.credits = 3
            swap = SwapRequest(
                sender_id=u1.id,
                receiver_id=u2.id,
                status="accepted",
                credits_settled=False,
            )
            db.session.add(swap)
            db.session.commit()
            swap_id = swap.id

        response = test_client.get(f"/complete/{swap_id}", follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            updated_swap = db.session.get(SwapRequest, swap_id)
            assert updated_swap.status == "completed"
            assert updated_swap.credits_settled is True
            u1 = db.session.get(User, test_user.id)
            u2 = db.session.get(User, test_user2.id)
            assert u1.credits == 4
            assert u2.credits == 4

    def test_peer_verified_skill_endorsement(self, test_client, test_user, test_user2):
        """Test peer-verified skill endorsement increments endorsements count and awards bonus XP."""
        with app.app_context():
            skill = Skill(
                name="Kubernetes",
                category="Tech",
                type="offer",
                proficiency_level="Advanced",
                user_id=test_user2.id,
                endorsements_count=0,
            )
            db.session.add(skill)
            db.session.commit()
            skill_id = skill.id

        test_client.post(
            "/login",
            data={"email": "test@example.com", "password": "testpassword123"},
        )
        review_data = {
            "rating": 5,
            "comment": "Outstanding mentor in Kubernetes and container orchestration!",
            "endorsed_skill_id": skill_id,
        }
        res = test_client.post(f"/submit_review/{test_user2.id}", data=review_data, follow_redirects=True)
        assert res.status_code == 200

        with app.app_context():
            endorsed_skill = db.session.get(Skill, skill_id)
            assert endorsed_skill.endorsements_count == 1
            endorsements = SkillEndorsement.query.filter_by(skill_id=skill_id).all()
            assert len(endorsements) == 1
            assert endorsements[0].endorser_id == test_user.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


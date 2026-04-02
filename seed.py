from app import app
from extensions import db
from models import Badge
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_badges():
    with app.app_context():
        if not Badge.query.first():
            logger.info("Initializing default badges...")
            default_badges = [
                Badge(name="First Swap", description="Completed first swap", icon="🎉"),
                Badge(name="Rising Star", description="Earned 200 XP", icon="⭐"),
                Badge(name="Skill Master", description="Earned 500 XP", icon="🔥"),
                Badge(name="Trusted Mentor", description="Received 5 reviews", icon="🏆"),
            ]
            db.session.add_all(default_badges)
            db.session.commit()
            logger.info("Badges initialized successfully.")
        else:
            logger.info("Badges already exist in the database.")

if __name__ == "__main__":
    seed_badges()

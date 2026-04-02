import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///skillswap.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload config
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/profile_pics")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Mail configuration defaults
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 2525))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False").lower() in ["true", "1", "t"]
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@skillswap.local")


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # Fail-fast security: Production must have a real SECRET_KEY in the environment
    SECRET_KEY = os.environ.get("SECRET_KEY", "")

    @classmethod
    def init_app(cls, app):
        if not app.config["SECRET_KEY"] or app.config["SECRET_KEY"] == "dev-secret-key-change-in-production":
            raise ValueError("FATAL ERROR: A secure SECRET_KEY is required in production environment.")


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

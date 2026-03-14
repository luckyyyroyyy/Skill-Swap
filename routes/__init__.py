from .main import main_bp
from .auth import auth_bp
from .user import user_bp
from .swap import swap_bp
from .chat import chat_bp

__all__ = ["main_bp", "auth_bp", "user_bp", "swap_bp", "chat_bp"]  # noqa: F401

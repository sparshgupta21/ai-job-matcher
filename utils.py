"""
AI Job Matcher v2.0 — Shared Utilities
"""

import os
import uuid
import logging


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


def generate_session_id():
    """Generate a unique session identifier."""
    return str(uuid.uuid4())[:8]


def get_app_version():
    """Return current app version."""
    from config import APP_VERSION
    return APP_VERSION


def truncate_text(text, max_length=500, suffix="..."):
    """Truncate text to max_length, adding suffix if truncated."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - len(suffix)] + suffix


def is_running_on_spaces():
    """Check if the app is running on Hugging Face Spaces."""
    return os.environ.get("SPACE_ID") is not None


def is_running_on_colab():
    """Check if the app is running on Google Colab."""
    try:
        import google.colab  # noqa: F401
        return True
    except ImportError:
        return False

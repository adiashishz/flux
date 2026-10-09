import pytest


@pytest.fixture(autouse=True)
def _no_background_embedding(settings):
    """Tests never touch the Celery broker unless they opt in and patch the task."""
    settings.AI_EMBEDDINGS_ENABLED = False


@pytest.fixture(autouse=True)
def _hermetic_ai_settings(settings):
    """The suite must not depend on the developer's .env (which may hold a real provider and key)."""
    settings.AI_ENABLED = False
    settings.AI_PROVIDER = "anthropic"
    settings.AI_MODEL = ""
    settings.AI_API_KEY = ""
    settings.AI_BASE_URL = ""
    settings.AI_STREAM_USAGE = False
    settings.AI_PROVIDER_KEYS = {}
    settings.ANTHROPIC_MODEL = "claude-sonnet-5-5"

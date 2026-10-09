import pytest


@pytest.fixture(autouse=True)
def _no_background_embedding(settings):
    """Tests never touch the Celery broker unless they opt in and patch the task."""
    settings.AI_EMBEDDINGS_ENABLED = False

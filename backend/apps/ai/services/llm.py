import anthropic
from django.conf import settings


def get_client():
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, max_retries=2, timeout=60.0)

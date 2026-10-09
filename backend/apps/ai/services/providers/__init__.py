"""Model vendors behind one interface. Pick one with AI_PROVIDER; see docs/ai-assistant.md."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from django.conf import settings

from apps.ai.services.providers.base import LLMError, Provider, StructuredOutputError  # noqa: F401
from apps.ai.services.providers.presets import PRESETS


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    kind: str
    base_url: str
    api_key: str
    model: str
    problem: str | None


def resolve(name=None, model=None):
    """Works out which vendor, URL, key and model to use, and what (if anything) is missing.

    Vendor specific keys always win. The generic AI_API_KEY, AI_MODEL and AI_BASE_URL only ever
    apply to the provider named in AI_PROVIDER, so asking for another vendor (the evals can) never
    sends it a key that belongs elsewhere."""
    configured = settings.AI_PROVIDER
    name = name or configured
    preset = PRESETS.get(name)
    if preset is None:
        return ProviderConfig(name, "", "", "", "", f"Unknown AI_PROVIDER '{name}'. Use one of: {', '.join(PRESETS)}.")

    is_default = name == configured
    key = settings.AI_PROVIDER_KEYS.get(name, "") or (settings.AI_API_KEY if is_default else "")
    base_url = (settings.AI_BASE_URL if is_default and settings.AI_BASE_URL else preset.base_url)
    model = model or (settings.AI_MODEL if is_default else "")
    if not model and preset.kind == "anthropic":
        model = settings.ANTHROPIC_MODEL

    problem = None
    if preset.needs_key and not key:
        problem = f"No API key for '{name}'. Set {name.upper()}_API_KEY or AI_API_KEY."
    elif preset.kind == "openai" and not base_url:
        problem = "Set AI_BASE_URL for the openai_compatible provider."
    elif not model:
        problem = f"Set AI_MODEL to a model your '{name}' account can use."
    return ProviderConfig(name, preset.kind, base_url, key, model, problem)


def provider_status(name=None, model=None):
    config = resolve(name, model)
    return {
        "enabled": settings.AI_ENABLED,
        "configured": config.problem is None,
        "provider": config.name,
        "model": config.model,
        "problem": config.problem,
    }


def is_ready():
    status = provider_status()
    return status["enabled"] and status["configured"]


_override = ContextVar("provider_override", default=None)


@contextmanager
def use_provider(name=None, model=None):
    """Make get_provider() default to this vendor and model inside the block (used by the evals
    to compare models). Generic keys are never applied to a vendor other than AI_PROVIDER."""
    token = _override.set((name, model))
    try:
        yield
    finally:
        _override.reset(token)


def get_provider(name=None, model=None):
    if name is None and model is None and _override.get():
        name, model = _override.get()
    config = resolve(name, model)
    if config.problem:
        raise LLMError(config.problem)
    if config.kind == "anthropic":
        from apps.ai.services.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(config.api_key, config.model)
    from apps.ai.services.providers.openai_compat import OpenAICompatProvider

    return OpenAICompatProvider(config.name, config.base_url, config.api_key, config.model)

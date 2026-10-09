import pytest

from apps.ai.services import providers
from apps.ai.services.providers import get_provider, is_ready, provider_status, resolve
from apps.ai.services.providers.anthropic_provider import AnthropicProvider
from apps.ai.services.providers.base import LLMError


@pytest.fixture(autouse=True)
def clean(settings):
    settings.AI_ENABLED = True
    settings.AI_PROVIDER = "anthropic"
    settings.AI_MODEL = ""
    settings.AI_API_KEY = ""
    settings.AI_BASE_URL = ""
    settings.AI_PROVIDER_KEYS = {}
    settings.ANTHROPIC_MODEL = "claude-default"


def test_anthropic_works_with_just_a_key_and_uses_the_default_model(settings):
    settings.AI_PROVIDER_KEYS = {"anthropic": "sk-a"}
    config = resolve()
    assert (config.problem, config.model, config.api_key) == (None, "claude-default", "sk-a")


def test_anthropic_model_can_be_overridden_with_ai_model(settings):
    settings.AI_PROVIDER_KEYS = {"anthropic": "sk-a"}
    settings.AI_MODEL = "claude-other"
    assert resolve().model == "claude-other"


def test_a_missing_key_is_reported_by_name(settings):
    assert "ANTHROPIC_API_KEY" in resolve().problem


def test_gemini_needs_an_explicit_model_so_no_stale_default_is_baked_in(settings):
    settings.AI_PROVIDER = "gemini"
    settings.AI_API_KEY = "g-key"
    config = resolve()
    assert config.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert "AI_MODEL" in config.problem
    settings.AI_MODEL = "some-model"
    assert resolve().problem is None


def test_the_generic_key_only_applies_to_the_configured_provider(settings):
    settings.AI_PROVIDER = "groq"
    settings.AI_API_KEY = "groq-key"
    settings.AI_MODEL = "m"
    assert resolve("groq").api_key == "groq-key"
    other = resolve("gemini", "m2")
    assert other.api_key == "" and "No API key for 'gemini'" in other.problem


def test_a_vendor_key_beats_the_generic_key(settings):
    settings.AI_PROVIDER = "gemini"
    settings.AI_API_KEY = "generic"
    settings.AI_PROVIDER_KEYS = {"gemini": "specific"}
    settings.AI_MODEL = "m"
    assert resolve().api_key == "specific"


def test_ai_model_and_base_url_do_not_leak_to_another_provider(settings):
    settings.AI_PROVIDER = "groq"
    settings.AI_MODEL = "groq-model"
    settings.AI_BASE_URL = "https://proxy.example/v1"
    settings.AI_PROVIDER_KEYS = {"gemini": "g"}
    other = resolve("gemini")
    assert other.model == "" and other.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_ollama_needs_no_key_and_defaults_to_the_host_machine(settings):
    settings.AI_PROVIDER = "ollama"
    settings.AI_MODEL = "llama-local"
    config = resolve()
    assert config.problem is None and config.api_key == ""
    assert config.base_url == "http://host.docker.internal:11434/v1"


def test_the_base_url_can_be_overridden_for_the_configured_provider(settings):
    settings.AI_PROVIDER = "ollama"
    settings.AI_MODEL = "m"
    settings.AI_BASE_URL = "http://localhost:11434/v1"
    assert resolve().base_url == "http://localhost:11434/v1"


def test_openai_compatible_needs_a_base_url(settings):
    settings.AI_PROVIDER = "openai_compatible"
    settings.AI_MODEL = "m"
    assert "AI_BASE_URL" in resolve().problem
    settings.AI_BASE_URL = "http://localhost:1234/v1"
    assert resolve().problem is None


def test_an_unknown_provider_lists_the_valid_ones(settings):
    settings.AI_PROVIDER = "skynet"
    problem = resolve().problem
    assert "Unknown AI_PROVIDER 'skynet'" in problem and "gemini" in problem and "ollama" in problem


def test_status_reports_enabled_configured_and_the_problem(settings):
    settings.AI_ENABLED = False
    status = provider_status()
    assert status["enabled"] is False and status["configured"] is False and status["provider"] == "anthropic"
    assert "ANTHROPIC_API_KEY" in status["problem"]


def test_is_ready_needs_both_the_flag_and_a_configuration(settings):
    settings.AI_PROVIDER_KEYS = {"anthropic": "k"}
    assert is_ready()
    settings.AI_ENABLED = False
    assert not is_ready()


def test_get_provider_builds_the_anthropic_adapter(settings):
    settings.AI_PROVIDER_KEYS = {"anthropic": "k"}
    provider = get_provider()
    assert isinstance(provider, AnthropicProvider) and provider.model == "claude-default"


def test_get_provider_raises_the_problem_as_an_llm_error():
    with pytest.raises(LLMError, match="No API key"):
        get_provider()

from apps.ai.services.providers import get_provider
from apps.ai.services.providers.base import LLMError, StructuredOutputError  # noqa: F401  (re-exported)


def structured_completion(*, system, messages, output_model):
    """One call whose answer must match a Pydantic model, on whichever provider is configured.
    Returns (parsed_output, usage). Raises LLMError with a message safe to show."""
    return get_provider().structured(system=system, messages=messages, output_model=output_model)

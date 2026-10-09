import anthropic
from django.conf import settings


class LLMError(Exception):
    """A model call failed in a way the user can be told about."""


class StructuredOutputError(LLMError):
    pass


def get_client():
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, max_retries=2, timeout=60.0)


def describe_api_error(exc):
    if isinstance(exc, anthropic.AuthenticationError):
        return "The AI service rejected the API key."
    if isinstance(exc, anthropic.RateLimitError):
        return "The AI service is rate limiting requests. Try again in a moment."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not reach the AI service."
    return "The AI service returned an error."


def structured_completion(*, system, messages, output_model):
    """One non streaming call whose answer must match a Pydantic model.
    Returns (parsed_output, usage). Raises LLMError with a message safe to show."""
    try:
        response = get_client().messages.parse(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.AI_MAX_TOKENS,
            system=system,
            messages=messages,
            output_format=output_model,
        )
    except anthropic.APIError as exc:
        raise LLMError(describe_api_error(exc)) from exc

    if response.parsed_output is None:
        raise StructuredOutputError(f"The model did not return a valid plan (stop reason: {response.stop_reason}).")
    usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return response.parsed_output, usage

import anthropic
from django.conf import settings

from apps.ai.services.providers.base import LLMError, Provider, StructuredOutputError, ToolCall, TurnResult

STOP_REASONS = {"tool_use": "tool_use", "max_tokens": "max_tokens", "refusal": "refusal"}


def describe_api_error(exc):
    if isinstance(exc, anthropic.AuthenticationError):
        return "The AI service rejected the API key."
    if isinstance(exc, anthropic.RateLimitError):
        return "The AI service is rate limiting requests. Try again in a moment."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not reach the AI service."
    return "The AI service returned an error."


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def _client(self):
        return anthropic.Anthropic(api_key=self.api_key, max_retries=2, timeout=60.0)

    def stream_turn(self, *, system, messages, tools):
        try:
            with self._client().messages.stream(
                model=self.model,
                max_tokens=settings.AI_MAX_TOKENS,
                system=system,
                tools=tools,
                messages=messages,
            ) as stream:
                for event in stream:
                    if event.type == "text":
                        yield ("text", event.text)
                final = stream.get_final_message()
        except anthropic.APIError as exc:
            raise LLMError(describe_api_error(exc)) from exc

        yield (
            "turn",
            TurnResult(
                text="".join(block.text for block in final.content if block.type == "text"),
                tool_calls=[ToolCall(b.id, b.name, b.input) for b in final.content if b.type == "tool_use"],
                stop_reason=STOP_REASONS.get(final.stop_reason, "end_turn"),
                usage={"input_tokens": final.usage.input_tokens, "output_tokens": final.usage.output_tokens},
            ),
        )

    def structured(self, *, system, messages, output_model):
        try:
            response = self._client().messages.parse(
                model=self.model,
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

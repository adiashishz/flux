"""Any vendor that speaks the OpenAI chat completions API: Gemini, Groq, OpenRouter, Mistral, Ollama,
LM Studio and more. The adapter is written defensively because free tiers and local models deviate
from the spec in small ways (tool call deltas without an index, malformed argument JSON, a missing
finish_reason, no usage numbers)."""
import json
import re

import openai
from django.conf import settings
from pydantic import ValidationError

from apps.ai.services.providers.base import LLMError, Provider, StructuredOutputError, ToolCall, TurnResult

FINISH_REASONS = {"tool_calls": "tool_use", "function_call": "tool_use", "length": "max_tokens", "content_filter": "refusal"}
FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
MAX_PROVIDER_MESSAGE = 200


def to_openai_messages(system, messages):
    """Canonical conversation (Anthropic style blocks) to chat completions messages."""
    converted = [{"role": "system", "content": system}]
    for message in messages:
        content = message["content"]
        if isinstance(content, str):
            converted.append({"role": message["role"], "content": content})
        elif message["role"] == "assistant":
            entry = {"role": "assistant", "content": "".join(b["text"] for b in content if b["type"] == "text") or None}
            calls = [
                {"id": b["id"], "type": "function", "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}
                for b in content
                if b["type"] == "tool_use"
            ]
            if calls:
                entry["tool_calls"] = calls
            converted.append(entry)
        else:
            for block in content:
                if block["type"] == "tool_result":
                    prefix = "Error: " if block.get("is_error") else ""
                    converted.append({"role": "tool", "tool_call_id": block["tool_use_id"], "content": prefix + block["content"]})
                elif block["type"] == "text":
                    converted.append({"role": "user", "content": block["text"]})
    return converted


def to_openai_tools(tools):
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in tools
    ]


def parse_json_text(text):
    """JSON from a model answer, tolerating code fences and a sentence around the object."""
    text = text.strip()
    fenced = FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


class OpenAICompatProvider(Provider):
    def __init__(self, name, base_url, api_key, model):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def _client(self):
        # Local servers ignore the key but the SDK insists on a non empty one.
        return openai.OpenAI(api_key=self.api_key or "not-needed", base_url=self.base_url, max_retries=2, timeout=60.0)

    def _describe(self, exc):
        who = self.name
        if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
            return f"{who} rejected the API key."
        if isinstance(exc, openai.RateLimitError):
            return f"{who} is rate limiting requests (free tiers allow only a few per minute). Try again in a moment."
        if isinstance(exc, openai.APIConnectionError):
            hint = " Is Ollama running and listening on 0.0.0.0?" if who == "ollama" else ""
            return f"Could not reach {who} at {self.base_url}.{hint}"
        if isinstance(exc, openai.NotFoundError):
            return f"{who} does not know the model '{self.model}'."
        if isinstance(exc, openai.BadRequestError):
            return f"{who} rejected the request: {str(exc.message)[:MAX_PROVIDER_MESSAGE]}"
        return f"{who} returned an error."

    # ---- chat turns -------------------------------------------------------------------------

    def stream_turn(self, *, system, messages, tools):
        request = {
            "model": self.model,
            "messages": to_openai_messages(system, messages),
            "max_tokens": settings.AI_MAX_TOKENS,
            "stream": True,
        }
        if tools:
            request["tools"] = to_openai_tools(tools)
        if settings.AI_STREAM_USAGE:
            request["stream_options"] = {"include_usage": True}

        text_parts, slots, finish = [], {}, None
        usage = {"input_tokens": 0, "output_tokens": 0}
        try:
            for chunk in self._client().chat.completions.create(**request):
                if getattr(chunk, "usage", None):
                    usage = {"input_tokens": chunk.usage.prompt_tokens or 0, "output_tokens": chunk.usage.completion_tokens or 0}
                for choice in chunk.choices or []:  # the usage only chunk has no choices
                    delta = choice.delta
                    if delta is not None and delta.content:
                        text_parts.append(delta.content)
                        yield ("text", delta.content)
                    for fragment in (delta.tool_calls or []) if delta is not None else []:
                        self._merge_tool_fragment(slots, fragment)
                    finish = choice.finish_reason or finish
        except openai.APIError as exc:
            raise LLMError(self._describe(exc)) from exc

        calls = [self._finish_call(number, slot) for number, slot in enumerate(slots.values(), start=1)]
        stop = FINISH_REASONS.get(finish, "end_turn")
        if calls and stop == "end_turn":
            stop = "tool_use"  # some servers say "stop" even when they asked for tools
        yield ("turn", TurnResult(text="".join(text_parts), tool_calls=calls, stop_reason=stop, usage=usage))

    @staticmethod
    def _merge_tool_fragment(slots, fragment):
        """Streaming tool calls arrive in pieces. Pieces are matched by index; when a server omits
        the index, by id; a piece with neither continues the most recent call."""
        index = getattr(fragment, "index", None)
        key = index if index is not None else (fragment.id or (list(slots)[-1] if slots else 0))
        slot = slots.setdefault(key, {"id": "", "name": "", "arguments": ""})
        if fragment.id and not slot["id"]:
            slot["id"] = fragment.id
        function = fragment.function
        if function is not None:
            if function.name and not slot["name"]:
                slot["name"] = function.name
            slot["arguments"] += function.arguments or ""

    @staticmethod
    def _finish_call(number, slot):
        call_id = slot["id"] or f"call_{number}"
        try:
            arguments = parse_json_text(slot["arguments"]) if slot["arguments"].strip() else {}
        except ValueError as exc:
            return ToolCall(call_id, slot["name"], {}, error=f"Your arguments were not valid JSON ({exc}). Send a JSON object.")
        if not isinstance(arguments, dict):
            return ToolCall(call_id, slot["name"], {}, error="Your arguments must be a JSON object.")
        return ToolCall(call_id, slot["name"], arguments)

    # ---- structured output ------------------------------------------------------------------

    def structured(self, *, system, messages, output_model):
        schema = output_model.model_json_schema()
        usage = {"input_tokens": 0, "output_tokens": 0}
        modes = [
            ({"type": "json_schema", "json_schema": {"name": output_model.__name__, "schema": schema}}, system),
            (
                {"type": "json_object"},
                system + "\n\nRespond with a single JSON object that matches this JSON schema, and nothing else:\n" + json.dumps(schema),
            ),
        ]
        conversation = list(messages)
        last_error = None
        for mode, (response_format, mode_system) in enumerate(modes):
            for attempt in range(2):  # the second attempt feeds the validation error back once
                try:
                    response = self._client().chat.completions.create(
                        model=self.model,
                        messages=to_openai_messages(mode_system, conversation),
                        max_tokens=settings.AI_MAX_TOKENS,
                        response_format=response_format,
                    )
                except openai.BadRequestError as exc:
                    if mode == 0:  # json_schema is not supported here: try plain JSON mode
                        break
                    raise LLMError(self._describe(exc)) from exc
                except openai.APIError as exc:
                    raise LLMError(self._describe(exc)) from exc

                if getattr(response, "usage", None):
                    usage["input_tokens"] += response.usage.prompt_tokens or 0
                    usage["output_tokens"] += response.usage.completion_tokens or 0
                text = response.choices[0].message.content or ""
                try:
                    return output_model.model_validate(parse_json_text(text)), usage
                except (ValueError, ValidationError) as exc:
                    last_error = exc
                    conversation = [
                        *messages,
                        {"role": "assistant", "content": text},
                        {"role": "user", "content": f"That answer was not valid ({str(exc)[:300]}). Reply with only the corrected JSON object."},
                    ]
            else:
                break  # both attempts answered but neither validated: no point switching modes
        raise StructuredOutputError("The model did not return valid JSON for the plan.") from last_error

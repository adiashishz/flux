import json
import logging

import anthropic
from django.conf import settings

from apps.ai.services.llm import get_client
from apps.ai.services.prompts import build_system_prompt
from apps.ai.tools import run_tool, tool_definitions

logger = logging.getLogger(__name__)

MAX_TOOL_RESULT_CHARS = 8000


def _error_message(exc):
    if isinstance(exc, anthropic.AuthenticationError):
        return "The AI service rejected the API key."
    if isinstance(exc, anthropic.RateLimitError):
        return "The AI service is rate limiting requests. Try again in a moment."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Could not reach the AI service."
    return "The AI service returned an error."


def _assistant_blocks(content):
    blocks = []
    for block in content:
        if block.type == "text" and block.text:
            blocks.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
    return blocks


def run_chat(messages, board_id=None):
    """Tool use loop. Yields event dicts: text, tool_call, tool_result, confirmation_required,
    done, error. The conversation is stateless: the client sends the text turns every time."""
    client = get_client()
    system = build_system_prompt(board_id)
    conversation = [{"role": m["role"], "content": m["content"]} for m in messages]
    usage = {"input_tokens": 0, "output_tokens": 0}

    for iteration in range(1, settings.AI_MAX_ITERATIONS + 1):
        try:
            with client.messages.stream(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                system=system,
                tools=tool_definitions(),
                messages=conversation,
            ) as stream:
                for event in stream:
                    if event.type == "text":
                        yield {"type": "text", "text": event.text}
                final = stream.get_final_message()
        except anthropic.APIError as exc:
            logger.exception("Anthropic call failed")
            yield {"type": "error", "message": _error_message(exc)}
            return

        usage["input_tokens"] += final.usage.input_tokens
        usage["output_tokens"] += final.usage.output_tokens
        tool_uses = [block for block in final.content if block.type == "tool_use"]

        if final.stop_reason != "tool_use" or not tool_uses:
            yield {"type": "done", "stop_reason": final.stop_reason, "iterations": iteration, "usage": usage}
            return

        conversation.append({"role": "assistant", "content": _assistant_blocks(final.content)})
        results = []
        for use in tool_uses:
            yield {"type": "tool_call", "id": use.id, "name": use.name, "input": use.input}
            ok, data = run_tool(use.name, use.input)
            yield {"type": "tool_result", "id": use.id, "name": use.name, "ok": ok, "result": data}
            if ok and data.get("requires_confirmation"):
                yield {
                    "type": "confirmation_required",
                    "action": "delete_card",
                    "card_id": data["card_id"],
                    "title": data["title"],
                    "board_id": data["board_id"],
                }
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": json.dumps(data)[:MAX_TOOL_RESULT_CHARS],
                    "is_error": not ok,
                }
            )
        conversation.append({"role": "user", "content": results})

    yield {
        "type": "error",
        "message": f"Stopped after {settings.AI_MAX_ITERATIONS} steps without finishing. Try a simpler request.",
    }

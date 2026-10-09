import json
import logging

from django.conf import settings

from apps.ai.services.prompts import build_system_prompt
from apps.ai.services.providers import get_provider
from apps.ai.services.providers.base import LLMError, assistant_blocks
from apps.ai.tools import run_tool, tool_definitions

logger = logging.getLogger(__name__)

MAX_TOOL_RESULT_CHARS = 8000


def run_chat(messages, board_id=None):
    """Tool use loop. Yields event dicts: text, tool_call, tool_result, confirmation_required,
    done, error. The conversation is stateless: the client sends the text turns every time."""
    try:
        provider = get_provider()
    except LLMError as exc:
        yield {"type": "error", "message": str(exc)}
        return

    system = build_system_prompt(board_id)
    conversation = [{"role": m["role"], "content": m["content"]} for m in messages]
    usage = {"input_tokens": 0, "output_tokens": 0}

    for iteration in range(1, settings.AI_MAX_ITERATIONS + 1):
        turn = None
        try:
            for kind, payload in provider.stream_turn(system=system, messages=conversation, tools=tool_definitions()):
                if kind == "text":
                    yield {"type": "text", "text": payload}
                else:
                    turn = payload
        except LLMError as exc:
            logger.warning("Model call failed: %s (%s)", exc, exc.__cause__)
            yield {"type": "error", "message": str(exc)}
            return

        usage["input_tokens"] += turn.usage["input_tokens"]
        usage["output_tokens"] += turn.usage["output_tokens"]

        if turn.stop_reason != "tool_use" or not turn.tool_calls:
            yield {"type": "done", "stop_reason": turn.stop_reason, "iterations": iteration, "usage": usage}
            return

        conversation.append({"role": "assistant", "content": assistant_blocks(turn)})
        results = []
        for call in turn.tool_calls:
            yield {"type": "tool_call", "id": call.id, "name": call.name, "input": call.arguments}
            if call.error:
                ok, data = False, {"error": call.error}
            else:
                ok, data = run_tool(call.name, call.arguments)
            yield {"type": "tool_result", "id": call.id, "name": call.name, "ok": ok, "result": data}
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
                    "tool_use_id": call.id,
                    "content": json.dumps(data)[:MAX_TOOL_RESULT_CHARS],
                    "is_error": not ok,
                }
            )
        conversation.append({"role": "user", "content": results})

    yield {
        "type": "error",
        "message": f"Stopped after {settings.AI_MAX_ITERATIONS} steps without finishing. Try a simpler request.",
    }

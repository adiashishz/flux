import copy
from types import SimpleNamespace

from apps.ai.services.providers.base import LLMError, Provider, ToolCall, TurnResult


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def tool_use_block(tool_use_id, name, arguments):
    return SimpleNamespace(type="tool_use", id=tool_use_id, name=name, input=arguments)


def final_message(*blocks, stop_reason=None):
    if stop_reason is None:
        stop_reason = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return SimpleNamespace(
        content=list(blocks),
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


class FakeStream:
    def __init__(self, final):
        self.final = final

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        for block in self.final.content:
            if block.type == "text":
                yield SimpleNamespace(type="text", text=block.text)

    def get_final_message(self):
        return self.final


class FakeClient:
    """Plays back scripted final messages, one per model call, and records every request."""

    def __init__(self, *finals):
        self.finals = list(finals)
        self.calls = []
        self.messages = self

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeStream(self.finals.pop(0))


STOP = {"tool_use": "tool_use", "end_turn": "end_turn", "max_tokens": "max_tokens"}


def turn_from_message(message):
    """Converts an Anthropic shaped final_message(...) into the vendor neutral TurnResult."""
    return TurnResult(
        text="".join(b.text for b in message.content if b.type == "text"),
        tool_calls=[ToolCall(b.id, b.name, b.input) for b in message.content if b.type == "tool_use"],
        stop_reason=STOP.get(message.stop_reason, "end_turn"),
        usage={"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens},
    )


class FakeProvider(Provider):
    """Scripted provider: one answer per model call. Records every request (copied at call time).
    Pass an exception instance in place of an answer to make that call fail."""

    name = "fake"
    model = "fake-model"

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def stream_turn(self, *, system, messages, tools):
        self.calls.append({"system": system, "messages": copy.deepcopy(messages), "tools": tools})
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        turn = answer if isinstance(answer, TurnResult) else turn_from_message(answer)
        if turn.text:
            yield ("text", turn.text)
        yield ("turn", turn)

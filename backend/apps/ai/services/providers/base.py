from dataclasses import dataclass, field


class LLMError(Exception):
    """A model call failed in a way the user can be told about. The message is safe to show."""


class StructuredOutputError(LLMError):
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    error: str | None = None  # set when the model sent arguments we could not parse


@dataclass
class TurnResult:
    """One model answer, the same shape for every vendor."""

    text: str = ""
    tool_calls: list = field(default_factory=list)
    stop_reason: str = "end_turn"  # end_turn | tool_use | max_tokens | refusal
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})


class Provider:
    """What the chat loop and the planner need from a model vendor.

    The conversation is passed in a canonical shape (Anthropic style blocks): user and assistant
    turns are strings or lists of text, tool_use and tool_result blocks. Each adapter converts it."""

    name = ""
    model = ""

    def stream_turn(self, *, system, messages, tools):
        """Yields ("text", str) pieces as they arrive, then exactly one ("turn", TurnResult)."""
        raise NotImplementedError

    def structured(self, *, system, messages, output_model):
        """One call whose answer must match a Pydantic model. Returns (parsed, usage)."""
        raise NotImplementedError


def assistant_blocks(turn):
    """The canonical assistant message for a turn, to append to the conversation."""
    blocks = []
    if turn.text:
        blocks.append({"type": "text", "text": turn.text})
    blocks.extend({"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments} for c in turn.tool_calls)
    return blocks

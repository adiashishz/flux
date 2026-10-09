from types import SimpleNamespace


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

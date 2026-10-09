import json

BLOCK_NODES = {"paragraph", "heading", "listItem", "taskItem", "codeBlock", "blockquote"}
MAX_CHARS = 4000


def tiptap_to_text(raw):
    """Plain text from TipTap JSON, falling back to the raw string for legacy markdown notes."""
    if not raw:
        return ""
    try:
        document = json.loads(raw)
    except (TypeError, ValueError):
        return raw.strip()
    if not isinstance(document, dict):
        return raw.strip()

    parts = []

    def walk(node):
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        for child in node.get("content") or []:
            walk(child)
        if node.get("type") in BLOCK_NODES:
            parts.append("\n")

    walk(document)
    return "".join(parts).strip()


def build_card_text(card):
    sections = [card.title, card.description, tiptap_to_text(card.content_markdown)]
    return "\n".join(section for section in sections if section)[:MAX_CHARS]

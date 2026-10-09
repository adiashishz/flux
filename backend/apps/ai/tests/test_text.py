import json

from apps.ai.services.text import build_card_text, tiptap_to_text
from apps.workspace.models import Card


def doc(*paragraphs):
    return json.dumps(
        {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]} for text in paragraphs],
        }
    )


def test_tiptap_paragraphs_become_lines():
    assert tiptap_to_text(doc("Buy milk", "Call Sam")) == "Buy milk\nCall Sam"


def test_nested_list_text_is_extracted():
    raw = json.dumps(
        {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "one"}]}]},
                        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "two"}]}]},
                    ],
                }
            ],
        }
    )
    assert tiptap_to_text(raw).split() == ["one", "two"]


def test_legacy_markdown_falls_back_to_the_raw_text():
    assert tiptap_to_text("# Heading\nsome notes") == "# Heading\nsome notes"


def test_non_object_json_falls_back_to_the_raw_text():
    assert tiptap_to_text("[1, 2]") == "[1, 2]"


def test_empty_content_is_empty():
    assert tiptap_to_text("") == ""
    assert tiptap_to_text(None) == ""


def test_card_text_joins_title_description_and_notes():
    card = Card(title="Plan trip", description="Summer", content_markdown=doc("Book flights"))
    assert build_card_text(card) == "Plan trip\nSummer\nBook flights"


def test_card_text_skips_empty_sections():
    assert build_card_text(Card(title="Only title")) == "Only title"


def test_card_text_is_capped():
    assert len(build_card_text(Card(title="t" * 6000))) == 4000

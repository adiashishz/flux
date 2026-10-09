import time

from django.db import transaction

from apps.ai.evals.world import cards_in_column, column_keys, snapshot
from apps.ai.services import chat
from apps.ai.services.search import scoped_search
from apps.ai.tools import scoped_boards
from apps.workspace.models import Card

MUTATING = {"create_card", "update_card", "move_card"}


def _ok_calls(events, name=None):
    results = {e["id"]: e for e in events if e["type"] == "tool_result" and e["ok"]}
    return [e for e in events if e["type"] == "tool_call" and e["id"] in results and (name is None or e["name"] == name)]


def _created(world, before):
    keys = column_keys(world)
    return [
        (keys[str(card.column_id)], card)
        for card in Card.objects.filter(column__in=world.columns.values())
        if str(card.id) not in before
    ]


def evaluate_check(check, world, before, events):
    """Returns (passed, message). Checks look at the database after the run, not at the model's words."""
    kind = check["type"]
    card = world.cards.get(check.get("card"))
    if card is not None:
        card = Card.objects.filter(id=card.id).first()

    if kind == "created_card":
        for column_key, new in _created(world, before):
            if column_key != check["column"]:
                continue
            if check["title_contains"].lower() not in new.title.lower():
                continue
            if check.get("description_contains", "").lower() in new.description.lower():
                return True, ""
        return False, f"no new card in {check['column']} matching {check['title_contains']!r}"

    if kind == "created_cards":
        titles = [new.title.lower() for column_key, new in _created(world, before) if column_key == check["column"]]
        missing = [t for t in check["titles_contain"] if not any(t in title for title in titles)]
        return (not missing), f"missing cards: {missing}"

    if kind == "card_in_column":
        ok = card is not None and card.column_id == world.columns[check["column"]].id
        return ok, f"card {check['card']} is not in {check['column']}"

    if kind == "card_at_index":
        ordered = [str(c.id) for c in cards_in_column(world, check["column"])]
        ok = card is not None and str(card.id) in ordered and ordered.index(str(card.id)) == check["index"]
        return ok, f"card {check['card']} is not at index {check['index']} of {check['column']}"

    if kind == "card_title_contains":
        return (card is not None and check["text"].lower() in card.title.lower()), f"title is {card.title if card else None!r}"

    if kind == "card_exists":
        return ((card is not None) == check["exists"]), f"card {check['card']} exists={card is not None}"

    if kind == "called":
        return bool(_ok_calls(events, check["tool"])), f"{check['tool']} was not called"

    if kind == "called_any":
        names = {e["name"] for e in _ok_calls(events)}
        return bool(names & set(check["tools"])), f"called {sorted(names)}"

    if kind == "no_mutation":
        changed = snapshot(world) != before
        mutated = [e["name"] for e in _ok_calls(events) if e["name"] in MUTATING]
        return (not changed and not mutated), f"changed={changed} mutating calls={mutated}"

    raise ValueError(f"Unknown check type {kind!r}")


def run_case(world, case):
    """Runs one prompt through the real chat loop inside a savepoint that is always rolled back."""
    savepoint = transaction.savepoint()
    try:
        before = snapshot(world)
        board_id = world.boards[case["board"]].id if case.get("board") else None
        started = time.monotonic()
        events = []
        with scoped_search(world.card_ids), scoped_boards([b.id for b in world.boards.values()]):
            for event in chat.run_chat([{"role": "user", "content": case["prompt"]}], board_id=board_id):
                events.append(event)

        failures = []
        for check in case["checks"]:
            passed, message = evaluate_check(check, world, before, events)
            if not passed:
                failures.append(f"{check['type']}: {message}")

        done = next((e for e in events if e["type"] == "done"), {})
        error = next((e["message"] for e in events if e["type"] == "error"), None)
        if error:
            failures.append(f"model error: {error}")
        return {
            "id": case["id"],
            "passed": not failures,
            "failures": failures,
            "tool_calls": [e["name"] for e in events if e["type"] == "tool_call"],
            "iterations": done.get("iterations"),
            "tokens": sum(done.get("usage", {}).values()),
            "seconds": round(time.monotonic() - started, 1),
        }
    finally:
        transaction.savepoint_rollback(savepoint)


def run_tools(world, dataset, pause=0.0):
    results = []
    for number, case in enumerate(dataset["cases"]):
        if number and pause:
            time.sleep(pause)  # free tiers allow only a few requests per minute
        results.append(run_case(world, case))
    passed = sum(r["passed"] for r in results)
    return {
        "cases": len(results),
        "passed": passed,
        "accuracy": passed / len(results),
        "total_tokens": sum(r["tokens"] for r in results),
        "results": results,
    }

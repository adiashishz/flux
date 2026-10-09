# AI Assistant

A chat panel ("Ask AI" in the sidebar) where Claude can read the workspace and change it through tools, a "Plan my week" agent, and an eval harness. Semantic search (Phase 1) is described in `CLAUDE.md`.

## How it works

```
AIPanel ──POST /api/v1/ai/chat/ (text turns + current board id)──► ChatView
                                                                   │  validates, rate limits, checks AI_ENABLED
                                                                   ▼
                                                              run_chat()  ◄── tool-use loop, max AI_MAX_ITERATIONS
                                                                   │  Anthropic Messages API (streamed)
                                                                   ▼
                                                              run_tool() ──► CardService / selectors (same code as the HTTP API)
Server-Sent Events ◄── text · tool_call · tool_result · confirmation_required · done · error
```

- **Stateless server.** The client sends the text turns of the conversation (newest 20, max 4000 characters each) on every request. Tool-use blocks are not stored between requests, so the model re-reads the board with tools when it needs to.
- **Tools** (`apps/ai/tools.py`): `list_boards`, `get_board`, `search_cards` (the Phase 1 semantic search), `create_card`, `update_card` (title and description only, never the notes), `move_card` (finds the source column itself), `delete_card`.
- **Deleting is never automatic.** `delete_card` only returns `requires_confirmation`. The loop emits `confirmation_required`, and the panel shows Delete and Keep buttons. Delete calls the normal `DELETE /cards/:id/` endpoint, so a person always makes the final call.
- **Errors the model can fix** (bad ids, missing fields, service validation errors) go back to it as `is_error` tool results instead of failing the request.
- **Limits:** `AI_MAX_ITERATIONS` (default 6), `AI_MAX_TOKENS` (default 2048), `AI_RATE_LIMIT` (default `20/min`, per process cache), request validation in `ChatRequestSerializer`.
- **Streaming:** gunicorn runs `gthread` workers (2 workers x 8 threads, 120 s timeout) so open streams do not pin a worker. nginx has a dedicated `/api/v1/ai/` location with `proxy_buffering off` and a 300 s read timeout.
- **Frontend:** `services/aiApi.ts` (`streamChat`, fetch plus `ReadableStream`, not axios), `utils/sse.ts` (incremental parser), `features/ai/chatState.ts` (pure reducer), `hooks/useAssistantChat.ts`. After a mutating tool succeeds, the board and card queries are invalidated, and the refresh waits while a card is being dragged.

## Plan my week (agent)

A button in the panel (visible when a board is open) starts a background run: **gather** the board's open cards, **plan** (Claude, schema validated with Pydantic), **validate** every card id, **repair** once if the plan used unknown or duplicate ids, then **write** the result.

- Runs as a Celery task tracked in `AssistantRun` (status, step log, token counts). `POST /api/v1/ai/plans/` returns 202 and the UI polls `GET /api/v1/ai/runs/<id>/` every 2 seconds. A run stuck longer than `AI_RUN_STALE_SECONDS` (10 minutes) is marked failed when polled, and a finished run is never overwritten.
- Done columns and the "This Week" column itself are never planned, so earlier plans do not feed the next one.
- The model only picks cards, days and one line reasons. Card titles come from the database and the saved document is rendered by our own code as TipTap JSON, so no model written markup reaches the editor.
- The result is a card in a "This Week" column (created if missing, reused if present). If the plan is still invalid after one repair the run fails and nothing is written.
- Cards have no due date field, so the plan lives in the card's notes, not in dates.

## Evals

`make eval` (or `uv run python manage.py run_evals`) measures the assistant. It builds a 30 card corpus through the real services inside a transaction that is rolled back, so your real cards are never read or changed.

- **Retrieval** (needs no API key, runs the local model): 28 paraphrased queries plus 4 unrelated ones. Reports recall@1, recall@5, MRR, a score cutoff sweep, and the misses.
- **Tool calling** (`--live`, calls the Anthropic API): 12 prompts scored by the database state afterwards (card created in the right column, card moved, nothing changed on a read only question, delete only asks, and so on).
- It exits non zero when `--min-recall` (0.85), `--min-mrr` (0.7) or, with `--live`, `--min-tool-accuracy` (0.8) is missed.

Measured on 2026-10-09 with `BAAI/bge-small-en-v1.5`: recall@1 0.96, recall@5 1.00, MRR 0.97. The right card scored 0.75 on median and the best unrelated card 0.57, so `AI_SEARCH_MIN_SCORE` is now 0.55 (it keeps recall@5 at 1.00 and cuts answers to unrelated queries from 4/4 to 2/4; 0.6 answers none of them but loses one right answer).

Read those numbers with care: the corpus is 30 cards, the queries were written by the same person who wrote the cards, and the cards are clearly different from each other. They show the plumbing and the calibration work, not production accuracy. Grow `datasets/` with real, messier cards to tighten them. The tool calling score has not been measured yet because it needs a live key.

## Turning it on

Off by default. Set these in `docker/.env` (or `backend/.env` for local runs) and restart the backend:

```
AI_ENABLED=true
ANTHROPIC_API_KEY=<your key>
ANTHROPIC_MODEL=claude-sonnet-5-5   # optional
```

Without both `AI_ENABLED=true` and a key the endpoint returns `503 {"detail": "The AI assistant is not enabled."}`.

## Known limits

- No user accounts yet, so anyone who can reach the API can spend the key. The flag and the rate limit are the only guards until the auth work in `FUTURE_PLANS.md`.
- The rate limit counter lives in each gunicorn process, so the effective limit is up to 2x the configured value.
- The assistant cannot edit a card's notes (they are stored as TipTap JSON).

## Tests

- Backend: `make test`. Tools, the loop (with a scripted fake client), and the endpoint are covered in `apps/ai/tests/`.
- Frontend: `pnpm test` in `frontend/` covers the SSE parser and the chat reducer.
- The real SDK was also checked against a local stub that speaks Anthropic's streaming wire format, through gunicorn and nginx. That run proved text arrives incrementally and deletes never execute.

# AI Assistant

Phase 2 of the assistant: a chat panel ("Ask AI" in the sidebar) where Claude can read the workspace and change it through tools. Phase 1 (semantic search) is described in `CLAUDE.md`.

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

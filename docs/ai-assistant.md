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

`make eval` (or `uv run python manage.py run_evals`) measures the assistant. It builds a 30 card corpus through the real services inside a transaction that is rolled back, so your real cards are never changed. The retrieval eval only ranks the eval corpus, and the live tool eval is limited to the eval's own boards and cards (`scoped_boards`, `scoped_search`), so a hosted model never sees your real board titles.

- **Retrieval** (needs no API key, runs the local model): 28 paraphrased queries plus 4 unrelated ones. Reports recall@1, recall@5, MRR, a score cutoff sweep, and the misses.
- **Tool calling** (`--live`, calls the Anthropic API): 12 prompts scored by the database state afterwards (card created in the right column, card moved, nothing changed on a read only question, delete only asks, and so on).
- It exits non zero when `--min-recall` (0.85), `--min-mrr` (0.7) or, with `--live`, `--min-tool-accuracy` (0.8) is missed.

Measured on 2026-10-09 with `BAAI/bge-small-en-v1.5`: recall@1 0.96, recall@5 1.00, MRR 0.97. The right card scored 0.75 on median and the best unrelated card 0.57, so `AI_SEARCH_MIN_SCORE` is now 0.55 (it keeps recall@5 at 1.00 and cuts answers to unrelated queries from 4/4 to 2/4; 0.6 answers none of them but loses one right answer).

Read those numbers with care: the corpus is 30 cards, the queries were written by the same person who wrote the cards, and the cards are clearly different from each other. They show the plumbing and the calibration work, not production accuracy. Grow `datasets/` with real, messier cards to tighten them. 
Tool calling, measured on 2026-10-09 against the real Gemini API (`gemini-3.5-flash-lite`, free tier): **12 of 12 cases passed** (`make eval ARGS="--live --pause 30"`, about 25 model calls over 6 minutes). Same caveats: 12 cases written by the same person, one run, a non deterministic model, and token counts show 0 because Gemini's compatible endpoint does not report usage by default. Repeat it per model before trusting a number, and add messier prompts.

## Model providers

The assistant is not tied to one vendor. `AI_PROVIDER` picks one of:

| Provider | How it connects | Needs |
|---|---|---|
| `anthropic` (default) | Anthropic SDK | `ANTHROPIC_API_KEY` (model defaults to `ANTHROPIC_MODEL`) |
| `gemini` | OpenAI compatible endpoint of Google AI Studio | `GEMINI_API_KEY`, `AI_MODEL` |
| `groq` | OpenAI compatible | `GROQ_API_KEY`, `AI_MODEL` |
| `openrouter` | OpenAI compatible (`:free` models exist) | `OPENROUTER_API_KEY`, `AI_MODEL` |
| `mistral` | OpenAI compatible | `MISTRAL_API_KEY`, `AI_MODEL` |
| `ollama` | OpenAI compatible, local, no key | `AI_MODEL` (a pulled model that supports tools) |
| `openai_compatible` | any other server (LM Studio, vLLM, a proxy) | `AI_BASE_URL`, `AI_MODEL` |

- **No default model** for anything except Anthropic, on purpose: free tiers retire and rename models often, and a stale default fails in a confusing way. `AI_MODEL` says which model to call.
- **Keys:** a vendor key (`GEMINI_API_KEY` ...) always wins. The generic `AI_API_KEY`, `AI_MODEL` and `AI_BASE_URL` only apply to the provider named in `AI_PROVIDER`, so comparing vendors in the evals never sends one vendor's key to another.
- `GET /api/v1/ai/status/` reports `{enabled, configured, provider, model, problem}` (never a key). The Ask AI panel uses it to show the model in use, or what is missing, instead of failing on the first message.
- **Architecture:** `apps/ai/services/providers/` has one interface (`stream_turn`, `structured`) and two adapters: `anthropic_provider.py` and `openai_compat.py`. The chat loop, the tools and the planner only see a vendor neutral `TurnResult` and `ToolCall`. To add a vendor with its own protocol, write another adapter. Most vendors only need a preset line in `presets.py`.

### Free providers: what to know

- **Limits and model lists change often.** Check the provider's own limits page before relying on a number. Reported limits at the time of writing (from third party sources, verify them): Groq free about 30 requests and 8,000 tokens per minute per model; OpenRouter `:free` models about 20 requests per minute; Gemini free limits are shown in AI Studio.
- **Prompt size matters on small token budgets.** The plan prompt is capped at `AI_PLAN_MAX_CARDS` (default 80) cards with 120 character descriptions. The tool definitions are about a thousand tokens.
- **Gemini free tier:** prompts and responses may be used by Google to improve its products. Do not put private notes through it.
- **Ollama:** the backend runs in Docker, so Ollama must listen on all interfaces (`OLLAMA_HOST=0.0.0.0 ollama serve`); the containers reach it at `host.docker.internal`. For a backend outside Docker set `AI_BASE_URL=http://localhost:11434/v1`. Small local models often call tools badly; run the evals on the model you pick.
- **Gemini thought signatures:** newer Gemini models attach `extra_content.google.thought_signature` to every tool call and reject the next request with a 400 if it is not sent back. The adapter keeps any vendor `extra_content` on a tool call and echoes it in the assistant message (found by running the real API: a first live eval scored 0 of 12 because of it).
- **Quirks the adapter already handles:** tool call chunks without an `index`, `stop` as the finish reason when tools were called, missing usage numbers (token counts show 0 unless `AI_STREAM_USAGE=true` works on your provider), malformed tool argument JSON (sent back to the model as an error so it can retry), `json_schema` response format not supported (falls back to JSON mode, tolerates code fences, one repair retry).
- **Free tier pacing:** one model had a limit of 5 requests per minute during testing, and a chat uses about 4 model calls. `run_evals --pause SECONDS` spaces the cases out; the limits are shown in AI Studio and change.
- **Compare models:** `make eval ARGS="--live --provider gemini --model <model>"` and the same for `ollama` print the tool calling accuracy per model.

## Turning it on

Off by default. Set these in `docker/.env` (or `backend/.env` for local runs) and restart the backend. Copy the blocks from `docker/.env.example`. For example Gemini:

```
AI_ENABLED=true
AI_PROVIDER=gemini
AI_MODEL=<a model your AI Studio key can call>
GEMINI_API_KEY=<your key>
```

or a local Ollama (no key):

```
AI_ENABLED=true
AI_PROVIDER=ollama
AI_MODEL=<a pulled model that supports tools>
```

Unless `AI_ENABLED=true` and the provider is fully configured, the chat and plan endpoints return `503 {"detail": "The AI assistant is not enabled."}` and the panel explains what is missing.

## Known limits

- No user accounts yet, so anyone who can reach the API can spend the key. The flag and the rate limit are the only guards until the auth work in `FUTURE_PLANS.md`.
- The rate limit counter lives in each gunicorn process, so the effective limit is up to 2x the configured value.
- The assistant cannot edit a card's notes (they are stored as TipTap JSON).

## Tests

- Backend: `make test`. Tools, the loop (with a scripted `FakeProvider`), both provider adapters (with fake SDK clients that replay vendor quirks), provider configuration, and the endpoints are covered in `apps/ai/tests/`.
- Frontend: `pnpm test` in `frontend/` covers the SSE parser and the chat reducer.
- Both real SDKs were also checked against local stub servers that speak Anthropic's streaming wire format and the OpenAI chat completions format (including a variant with every quirk above), through gunicorn, nginx and the Celery worker. Those runs proved text arrives incrementally, deletes never execute, malformed tool arguments are recovered from, and plan my week works with and without `json_schema` support. The OpenAI adapter and Gemini were then checked against the real Gemini API.

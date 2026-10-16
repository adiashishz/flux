# Flux

A lightweight productivity workspace: boards, columns, cards and markdown notes, with an optional AI assistant that can search the workspace, change it through tools, and plan your week.

## Features

- **Workspaces, boards, columns, cards** with drag and drop reordering (atomic, row locked, integer positions) and a TipTap notes editor per card.
- **Semantic search:** find cards by meaning, not keywords. Local embeddings (`BAAI/bge-small-en-v1.5`, 384 dimensions) in PostgreSQL with pgvector (HNSW, cosine), kept fresh by a Celery task.
- **Ask AI:** a streaming chat panel where the model reads the workspace and creates, updates and moves cards through tools. Deleting is never automatic: the model can only ask, and a person confirms.
- **Plan my week:** an agent that picks open cards and days, validates the plan, repairs it once if needed, and writes a plan card. Runs as a tracked Celery job.
- **Any model vendor:** the assistant sits behind a provider interface. Anthropic, Gemini, Groq, OpenRouter, Mistral, Ollama (local, no key) or any OpenAI compatible server.
- **Evals:** `make eval` measures search quality (recall@1, recall@5, MRR, a score cutoff sweep) and, with `--live`, tool calling accuracy for the model you configured.

The AI features are off by default. The rest of the app works without them. See [docs/ai-assistant.md](docs/ai-assistant.md) for the design, limits and measured numbers.

## Stack

- **Backend:** Django 6, DRF, PostgreSQL 16 with pgvector, Celery and Redis, fastembed
- **Frontend:** React 19, Vite 8, TypeScript, Tailwind v4, shadcn/ui, TanStack Query, Zustand
- **AI:** provider layer in `backend/apps/ai/services/providers/` (Anthropic SDK and an OpenAI compatible adapter), tool use loop streamed over Server-Sent Events

## Quick start (Docker)

```bash
cp docker/.env.example docker/.env     # then edit SECRET_KEY and, optionally, the AI settings
make up                                # builds and starts db, redis, backend, worker, frontend
```

App: http://localhost:5800
API: http://localhost:7000/api/v1/

## Local development

```bash
cp backend/.env.example backend/.env
make dev                               # starts only Postgres (5434) and Redis (6380)

# backend
cd backend && uv sync && uv run python manage.py migrate && cd ..
make backend-start                     # serves on :7000

# Celery worker (embeddings, plan my week), in another terminal
make worker

# frontend
cd frontend
pnpm install
pnpm dev                               # http://localhost:3000, proxies /api to :7000
```

## Turning on the AI assistant

Set these in `docker/.env` (Docker) or `backend/.env` (local) and restart the backend:

```
AI_ENABLED=true
AI_PROVIDER=gemini          # anthropic | gemini | groq | openrouter | mistral | ollama | openai_compatible
AI_MODEL=<a model your account can call>
GEMINI_API_KEY=<your key>   # or AI_API_KEY; Ollama needs no key
```

`AI_MODEL` is required for every provider except Anthropic. Free tiers rename and retire models often, so nothing is hard coded. The Ask AI panel shows which model is in use, or what is missing, instead of failing on the first message. Provider notes (free tier limits, Ollama in Docker, Gemini quirks) are in [docs/ai-assistant.md](docs/ai-assistant.md#model-providers).

## Tests and evals

```bash
make test                                   # backend (pytest); requires make dev
cd frontend && pnpm test                    # frontend (vitest)
make eval                                   # search quality, runs the local model, no key needed
make eval ARGS="--live --pause 30"          # also scores tool calling against your configured model
make eval ARGS="--live --provider ollama --model <model>"   # compare another model
```

The eval corpus is small (30 cards, 28 queries, 12 tool cases) and written by the same person who wrote the cards, so treat the numbers as a check on the plumbing and calibration, not production accuracy.

## Docs

- [AI assistant](docs/ai-assistant.md): architecture, tools, plan my week, evals, providers, known limits
- [Drag and drop](docs/drag-and-drop.md), [TipTap editor](docs/tiptap-editor.md), [Caching](docs/caching.md), [Auth](docs/auth.md), [User](docs/user.md)
- [Future plans](FUTURE_PLANS.md)

## Known limits

There are no user accounts yet, so anyone who can reach the API can use the configured model key. The AI flag and a per process rate limit are the only guards until the auth work in [FUTURE_PLANS.md](FUTURE_PLANS.md).

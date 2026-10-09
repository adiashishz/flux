# Flux — Claude Code Instructions

## Project

Flux is a lightweight productivity workspace: workspaces → boards → columns → cards → markdown notes.
Personal boards (no workspace) live under "My Boards".
Location: `/home/skrrt/coding/flux`
**Philosophy:** fast, minimal, maintainable, server-first.
Backend is the single source of truth. Reference patterns from alpha7 at `/home/skrrt/code/alpha7` (same stack, same developer).

---

## ⚠️ Hard Rules — Do Not Deviate

1. **APIView pattern only** — never `ModelViewSet` or `DefaultRouter`
2. **Integer positions** (1000, 2000, 3000) — never FloatField
3. **Backend calculates all positions** via `CardService.move_card()` — frontend only sends `card_id`, `source_column_id`, `destination_column_id`, `destination_index`
4. **EditorPanel stays mounted** in `AppLayout` at all times (conditionally visible, never unmounted)
5. **No ViewSets** — each endpoint is a separate `APIView` subclass
6. **Tailwind v4** — `@tailwindcss/vite` plugin, theme in `src/index.css` `@theme {}` block, NO `tailwind.config.js`
7. **shadcn/ui** — do not import `@radix-ui` directly in feature code; all primitives via `src/components/ui/`
8. **Top-down data flow** — only `WorkspaceList`, `BoardList`, `BoardView`, `Sidebar`, `EditorPanel`, `SearchDialog`, and `AIPanel` fetch data; all other components receive props
9. **Zustand for UI state only** — `selectedCardId`, `editorPanelOpen`, `sidebarOpen`, `searchOpen`, `aiPanelOpen`, `isDragging`. All data comes from the API.
10. **3-layer API pattern** — `services/api.ts` → `services/*Api.ts` → `hooks/queries/use*.ts`. No business logic in hooks or services.

---

## Tech Stack

| Tool | Version |
|------|---------|
| Python | >=3.12 (uv) |
| Django | 6.0+ |
| DRF | 3.15+ |
| psycopg | 3.2+ (binary) |
| PostgreSQL | 16 with pgvector (`pgvector/pgvector:pg16`) |
| Celery + Redis | Redis is the broker only (not an app cache) |
| fastembed | local ONNX embeddings, `BAAI/bge-small-en-v1.5` (384 dims) |
| Node | 22 |
| pnpm | 10.32.1 |
| React | 19.x |
| Vite | 8.x |
| Tailwind | v4 (via @tailwindcss/vite) |
| @tanstack/react-query | v5 |
| zustand | latest |
| axios | latest |
| @dnd-kit/sortable | ^10.0.0 |
| shadcn/ui | latest (Tailwind v4 compatible) |

---

## Running Locally

### Docker (Postgres + Redis)
```bash
cd ~/coding/flux
make dev                    # postgres (pgvector) on :5434, redis on :6380
make down                   # stop
```

### Backend
```bash
cd ~/coding/flux/backend
uv run python manage.py runserver 7000          # API on :7000
uv run python manage.py makemigrations          # only when models change
uv run python manage.py migrate                 # only when models change
uv run python manage.py embed_cards             # backfill card embeddings (first run downloads the model)
uv run celery -A config worker -l info          # or: make worker (embeds cards after saves)
uv run pytest                                   # or: make test (needs make dev first)
```

### Frontend
```bash
cd ~/coding/flux/frontend
pnpm dev                    # app on :3000
```

API docs: http://localhost:7000/api/docs/

---

## Backend — Key Notes

- **Postgres port:** 5434 (mapped from container's 5432)
- **DRF auth disabled** — `DEFAULT_AUTHENTICATION_CLASSES: []`, `DEFAULT_PERMISSION_CLASSES: [AllowAny]` in both `base.py` and `development.py`
- **`django.contrib.auth` in INSTALLED_APPS** — required by DRF even with auth disabled
- **Settings module:** `DJANGO_SETTINGS_MODULE=config.settings.development` (set in `.env`)
- **Service layer:** card create, update, and delete live in `CardService` (not in the views), so the HTTP API and the AI tools share one code path
- **`apps/ai`:** `CardEmbedding` (pgvector, HNSW cosine index), `GET /api/v1/ai/search/?q=`, Celery task `embed_card` queued after commit by a `post_save` signal. Embeddings are skipped when the text hash and model are unchanged. A broker outage is logged and never fails a card save.
- **Assistant:** `POST /api/v1/ai/chat/` streams SSE from a tool-use loop (`apps/ai/services/chat.py`, tools in `apps/ai/tools.py`). Off unless `AI_ENABLED=true` and a provider is configured (`AI_PROVIDER`: anthropic, gemini, groq, openrouter, mistral, ollama, openai_compatible; model vendors sit behind `apps/ai/services/providers/`). Also `POST /api/v1/ai/plans/` (plan my week as a Celery job) and `manage.py run_evals` (`make eval`). See `docs/ai-assistant.md`.
- **Tests:** `uv run pytest` (pytest-django + factory_boy). `AI_EMBEDDINGS_ENABLED` is forced off in `conftest.py`. Frontend: `pnpm test` (vitest) for the SSE parser and chat reducer.
- **Env examples:** `backend/.env.example` and `docker/.env.example`. Copy to `.env` locally.

---

## Frontend — Key Notes

- **shadcn `components.json`** — aliases use `src/` prefix (not `@/`). Do not change.
- **shadcn component imports** use `@/lib/utils` — do not edit these imports
- **`src/lib/utils.ts`** — re-export shim for shadcn compat only, do not add logic here
- **Tailwind v4** — no `tailwind.config.js`, all tokens in `src/index.css` `@theme {}` block
- **Vite proxy** — `/api` → `http://localhost:7000` (set in `vite.config.ts`)
- **EditorPanel auto-save** — debounced 800ms, sends `content_preview` (first 200 plain-text chars) with every save
- **Editor content format** — stored as **TipTap JSON** (`editor.getJSON()` serialised to string) in the `content_markdown` DB field. The field name is legacy; the value is always JSON now. Loading: tries `JSON.parse` first (new format), falls back to `@tiptap/markdown` `manager.parse()` for older markdown content. `content_preview` is extracted via `editor.getText()` (plain text, no markup). Do **not** switch back to markdown storage — JSON preserves all structure (empty list items, blank paragraphs) that markdown cannot round-trip.

---

## Frontend Structure

```
frontend/src/
├── app/                         ← RouterProvider, Providers
├── features/
│   ├── workspace/
│   │   ├── WorkspaceList.tsx    ← DATA OWNER
│   │   └── components/
│   │       └── CreateWorkspaceDialog.tsx
│   ├── board/
│   │   ├── BoardList.tsx        ← DATA OWNER (personal + workspace mode)
│   │   ├── BoardView.tsx        ← DATA OWNER
│   │   └── components/
│   │       └── CreateBoardDialog.tsx
│   ├── column/
│   │   ├── Column.tsx
│   │   └── components/AddColumnButton.tsx
│   ├── card/
│   │   ├── CardList.tsx
│   │   └── components/Card.tsx
│   └── editor/
│       ├── EditorPanel.tsx      ← DATA OWNER (always mounted)
│       └── components/
├── components/
│   ├── ui/                      ← shadcn primitives only
│   └── layout/                  ← AppLayout, Sidebar, Toolbar
├── services/
│   ├── api.ts                   ← axios instance
│   ├── workspacesApi.ts
│   ├── boardsApi.ts
│   └── cardsApi.ts
├── hooks/
│   ├── useDebounce.ts
│   └── queries/
│       ├── useWorkspaces.ts
│       ├── useBoards.ts
│       └── useCards.ts
├── store/ui.ts                  ← Zustand UI state only
├── utils/                       ← cn, formatDate, relativeTime
├── lib/utils.ts                 ← shadcn re-export shim
├── types/index.ts
└── routes/index.tsx
```

### Routes
```
/                                → redirect to /boards
/boards                          → My Boards (personal)
/boards/:id                      → BoardView
/workspaces                      → WorkspaceList
/workspaces/:workspaceId         → BoardList (scoped)
/workspaces/:workspaceId/boards/:id → BoardView
```

---

## Context Mockups

Design reference (read before any UI changes):
- `context/mockup.png` — visual reference
- `context/mockup.html` — layout/spacing reference. Do NOT copy HTML literally into React.

---

## Future Plans

Planned features and ideas that are **not yet being built** live in `FUTURE_PLANS.md` at the project root. Read it before suggesting new features — the idea may already be scoped there. Add new ideas to that file rather than implementing them speculatively.

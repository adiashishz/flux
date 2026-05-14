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
8. **Top-down data flow** — only `WorkspaceList`, `BoardList`, `BoardView`, `Sidebar`, and `EditorPanel` fetch data; all other components receive props
9. **Zustand for UI state only** — `selectedCardId`, `editorPanelOpen`, `sidebarOpen`. All data comes from the API.
10. **3-layer API pattern** — `services/api.ts` → `services/*Api.ts` → `hooks/queries/use*.ts`. No business logic in hooks or services.

---

## Tech Stack

| Tool | Version |
|------|---------|
| Python | >=3.12 (uv) |
| Django | 6.0+ |
| DRF | 3.15+ |
| psycopg | 3.2+ (binary) |
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

### Docker (Postgres)
```bash
cd ~/coding/flux/docker
docker compose up -d        # postgres on :5434
docker compose down         # stop
```

### Backend
```bash
cd ~/coding/flux/backend
uv run python manage.py runserver 7000          # API on :7000
uv run python manage.py makemigrations          # only when models change
uv run python manage.py migrate                 # only when models change
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

---

## Frontend — Key Notes

- **shadcn `components.json`** — aliases use `src/` prefix (not `@/`). Do not change.
- **shadcn component imports** use `@/lib/utils` — do not edit these imports
- **`src/lib/utils.ts`** — re-export shim for shadcn compat only, do not add logic here
- **Tailwind v4** — no `tailwind.config.js`, all tokens in `src/index.css` `@theme {}` block
- **Vite proxy** — `/api` → `http://localhost:7000` (set in `vite.config.ts`)
- **EditorPanel auto-save** — debounced 800ms, sends `content_preview` (first 200 chars) with every save

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

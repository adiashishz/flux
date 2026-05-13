# Flux — Claude Code Instructions

## Project

Flux is a lightweight productivity workspace: boards → columns → cards → markdown notes.
Location: `/home/skrrt/coding/flux`
**Philosophy:** fast, minimal, maintainable, server-first. Not a Notion clone. Not a Jira clone.
Backend is the single source of truth. Reference patterns from alpha7 at `/home/skrrt/code/alpha7` (same stack, same developer).

---

## Build Status

| Layer | Status |
|-------|--------|
| Backend models, serializers, services, API views | ✅ Complete |
| Migrations applied, DB running | ✅ Complete |
| Frontend UI | ✅ Complete |
| API wiring (hooks, services, real data) | ✅ Complete |

---

## ⚠️ Hard Rules — Do Not Deviate

1. **APIView pattern only** — never `ModelViewSet` or `DefaultRouter`
2. **Integer positions** (1000, 2000, 3000) — never FloatField
3. **Backend calculates all positions** via `CardService.move_card()` — frontend only sends `card_id`, `source_column_id`, `destination_column_id`, `destination_index`
4. **EditorPanel stays mounted** in `AppLayout` at all times (conditionally visible, never unmounted)
5. **No ViewSets** — each endpoint is a separate `APIView` subclass
6. **Tailwind v4** — `@tailwindcss/vite` plugin, theme in `src/index.css` `@theme {}` block, NO `tailwind.config.js`
7. **shadcn/ui** — do not import `@radix-ui` directly in feature code; all primitives via `src/components/ui/`
8. **Top-down data flow** — only `BoardView`, `Sidebar`, and `EditorPanel` fetch data; all other components receive props
9. **Zustand for UI state only** — `selectedCardId`, `editorPanelOpen`, `sidebarOpen`. All data comes from the API.

---

## Tech Stack & Exact Versions

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
| @vitejs/plugin-react | ^6.0.0 |
| Tailwind | v4 (via @tailwindcss/vite) |
| tailwind-merge | ^3.0.0 |
| @tanstack/react-query | v5 |
| zustand | latest |
| axios | latest |
| @dnd-kit/sortable | ^10.0.0 |
| shadcn/ui | latest (Tailwind v4 compatible) |
| vite-plugin-pwa | ^0.21.0 |

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
pnpm build                  # production build
```

API docs: http://localhost:7000/api/docs/

---

## Backend — Key Notes

- **Postgres port:** 5434 (mapped from container's 5432) — set in `docker/docker-compose.yml` and `backend/.env`
- **DRF auth disabled** — `DEFAULT_AUTHENTICATION_CLASSES: []`, `DEFAULT_PERMISSION_CLASSES: [AllowAny]` in both `base.py` and `development.py`. No login required.
- **`django.contrib.auth` is in INSTALLED_APPS** — required by DRF even with auth disabled
- **Settings module:** `DJANGO_SETTINGS_MODULE=config.settings.development` (set in `.env`)

---

## API Endpoints

```
GET  POST          /api/v1/boards/
GET  PATCH DELETE  /api/v1/boards/<uuid>/
GET                /api/v1/boards/<uuid>/detail/   ← nested board+columns+cards
POST               /api/v1/boards/<uuid>/columns/
PATCH DELETE       /api/v1/columns/<uuid>/
POST               /api/v1/columns/<uuid>/cards/
PATCH DELETE       /api/v1/cards/<uuid>/
POST               /api/v1/cards/<uuid>/move/
GET                /api/v1/search/?q=<query>
```

---

## Data Models

**BaseModel** (abstract): id (UUID pk), created_at, updated_at

**Board**: title (CharField 255), Meta.ordering=["-created_at"]

**Column**: board (FK→Board, cascade), title (CharField 255), position (IntegerField default=1000), Meta.ordering=["position"]

**Card**: column (FK→Column, cascade), title (CharField 500), content_markdown (TextField blank), content_preview (TextField blank, first 200 chars), position (IntegerField default=1000), Meta.ordering=["position"]

**Positioning strategy:** Spaced 1000, 2000, 3000. On move: midpoint between neighbors; if gap < 10, rebalance entire column (reset to 1000, 2000, 3000...).

---

## Serializers

- `BoardSerializer` — id, title, created_at, updated_at, column_count
- `BoardDetailSerializer` — above + nested columns (with nested cards)
- `ColumnSerializer` — id, board_id, title, position, card_count + nested cards (read-only)
- `CardSerializer` — id, column_id, title, content_preview, position, created_at, updated_at
- `CardDetailSerializer` — above + content_markdown, column_title
- `CardMoveSerializer` — source_column_id, destination_column_id, destination_index (int ≥ 0)

---

## Service Layer

**`CardService`** (`services/card_service.py`) — only file with business logic:
- `move_card(card_id, source_column_id, dest_column_id, dest_index)` → validates, calculates position, updates DB, returns card
- `rebalance_column(column_id)` → resets all positions to 1000, 2000, 3000... via bulk_update

**`board_selectors.py`**:
- `get_board_detail(board_id)` → `Board.objects.prefetch_related("columns__cards").get(id=board_id)`

---

## Frontend Data Flow (Top-Down)

```
AppLayout
  └── Sidebar       fetches GET /boards  (list only)
  └── BoardView     fetches GET /boards/:id/detail → passes columns[] down as props
        └── Column  PRESENTATIONAL — receives column + cards[] as props, no fetch
              └── Card  PRESENTATIONAL — receives card as prop, no fetch
  └── EditorPanel   fetches GET /cards/:id on selection; mutates PATCH /cards/:id
```

Only 3 data-fetching points: Sidebar, BoardView, EditorPanel.

---

## 3-Layer API Pattern

```
Layer 1 — src/services/api.ts          axios instance, baseURL: '/api/v1/'
Layer 2 — src/services/boardsApi.ts    thin one-liner functions, returns r.data
          src/services/cardsApi.ts
Layer 3 — src/hooks/queries/useBoards.ts   React Query hooks + key factories
          src/hooks/queries/useCards.ts
```

- Layer 2 functions: no state, no error handling, just `api.method(...).then(r => r.data)`
- Layer 3 mutations call `qc.invalidateQueries` on success
- Components call hooks directly — no business logic in hooks

### Cache Invalidation Rules

| Action | Invalidates |
|--------|------------|
| createBoard / deleteBoard | boardKeys.all |
| createColumn / updateColumn / deleteColumn | boardKeys.detail(boardId) |
| createCard / deleteCard / moveCard | boardKeys.detail(boardId) |
| updateCard | cardKeys.detail(cardId) |

---

## Frontend Folder Structure

```
frontend/src/
├── app/
│   ├── App.tsx                  ← RouterProvider
│   └── providers.tsx            ← QueryClientProvider + TooltipProvider
├── features/
│   ├── board/
│   │   ├── BoardView.tsx        ← DATA OWNER: fetches board detail, passes props down
│   │   ├── BoardList.tsx        ← DATA OWNER: fetches board list
│   │   └── components/
│   │       └── CreateBoardDialog.tsx
│   ├── column/
│   │   ├── Column.tsx           ← PRESENTATIONAL: renders one column + its cards
│   │   └── components/
│   │       └── AddColumnButton.tsx
│   ├── card/
│   │   ├── CardList.tsx         ← PRESENTATIONAL: maps cards → Card
│   │   └── components/
│   │       └── Card.tsx         ← PRESENTATIONAL leaf, opens EditorPanel on click
│   └── editor/
│       ├── EditorPanel.tsx      ← DATA OWNER: always mounted, fetches + auto-saves card
│       └── components/
│           ├── MarkdownEditor.tsx
│           └── MarkdownPreview.tsx
├── components/
│   ├── ui/                      ← shadcn primitives only
│   └── layout/
│       ├── AppLayout.tsx
│       ├── Sidebar.tsx          ← DATA OWNER: fetches board list
│       └── Toolbar.tsx
├── services/
│   ├── api.ts                   ← axios instance (Layer 1)
│   ├── boardsApi.ts             ← boards + columns functions (Layer 2)
│   └── cardsApi.ts              ← cards functions (Layer 2)
├── hooks/
│   ├── useDebounce.ts           ← generic debounce hook
│   └── queries/
│       ├── useBoards.ts         ← boardKeys + board/column hooks (Layer 3)
│       └── useCards.ts          ← cardKeys + card hooks (Layer 3)
├── store/
│   └── ui.ts                    ← Zustand: selectedCardId, editorPanelOpen, sidebarOpen
├── utils/
│   ├── cn.ts                    ← clsx + twMerge
│   ├── formatDate.ts            ← ISO → "May 8", returns '—' for null
│   └── relativeTime.ts          ← ISO → "2 min ago", returns '—' for null
├── lib/
│   └── utils.ts                 ← re-exports cn from utils/cn (shadcn compat, do not change)
├── types/
│   └── index.ts                 ← Board, Column, Card, CardDetail, BoardDetail
├── routes/
│   └── index.tsx
├── main.tsx
└── index.css                    ← @theme tokens (NO tailwind.config.js)
```

### Component Rules
- `src/components/ui/` — shadcn primitives only, never feature-specific logic
- `src/components/layout/` — globally shared layout shells (AppLayout, Sidebar, Toolbar)
- `src/features/<feature>/` — one parent component at root (data owner or presentational parent)
- `src/features/<feature>/components/` — all child components for that feature
- Data flows **top-down via props** — children never fetch, never import from sibling features
- No direct `@radix-ui` imports in feature code — always go through `src/components/ui/`

---

## Zustand Store (UI state only)

```typescript
interface UIState {
  selectedCardId: string | null
  editorPanelOpen: boolean
  sidebarOpen: boolean
  setSelectedCard: (id: string | null) => void
  openEditor: () => void
  closeEditor: () => void
  toggleSidebar: () => void
}
```

---

## Frontend — Key Notes

- **shadcn `components.json`** — aliases use `src/` prefix (not `@/`). Do not change back to `@/`.
- **shadcn component imports** use `@/lib/utils` and `@/components/ui/` — resolve via `tsconfig.app.json`. Do not edit these imports.
- **`src/lib/utils.ts`** is a re-export shim for shadcn compatibility — do not add logic here.
- **Tailwind v4** — no `tailwind.config.js`, all tokens in `src/index.css` `@theme {}` block.
- **EditorPanel auto-save** — debounced 800ms on title and content, sends `content_preview` (first 200 chars) alongside `content_markdown`.
- **Vite proxy** — `/api` → `http://localhost:7000` (set in `vite.config.ts`).

---

## Context Mockups

Design reference (read before any UI changes):
- `context/mockup.png` — visual reference
- `context/mockup.html` — layout/spacing reference. Do NOT copy HTML literally into React.

# Flux — Claude Code Instructions

## ✅ What Is Already Done

The following has been completed and must NOT be redone:

### Root structure — complete
- `/home/skrrt/coding/flux/` with `backend/`, `frontend/`, `docs/`, `context/`, `docker/`, `.github/`, `.claude/`
- `.gitignore`, `README.md`

### Backend — scaffold complete, implementations empty
All directories and `__init__.py` files exist. These files have **real content**:
- `backend/pyproject.toml` — deps: django, drf, psycopg, drf-spectacular, cors-headers, gunicorn, whitenoise, python-decouple
- `backend/manage.py`
- `backend/config/settings/base.py` — full settings (DB, DRF, CORS, logging)
- `backend/config/settings/development.py` — DEBUG=True, CORS allow all
- `backend/config/settings/production.py` — security headers
- `backend/config/urls.py` — routes to `apps.workspace.api.v1.urls` + drf-spectacular
- `backend/config/wsgi.py`
- `backend/.env` — DB_NAME=flux, DB_USER=flux, DB_PASSWORD=flux, DB_HOST=localhost

These files exist but are **empty placeholders** (implement next):
- `backend/apps/core/models.py`
- `backend/apps/workspace/models/board.py`, `column.py`, `card.py`, `__init__.py`
- `backend/apps/workspace/serializers/board_serializers.py`, `column_serializers.py`, `card_serializers.py`
- `backend/apps/workspace/services/card_service.py`
- `backend/apps/workspace/selectors/board_selectors.py`
- `backend/apps/workspace/api/v1/boards.py`, `columns.py`, `cards.py`, `urls.py`

### Frontend — directory structure complete, all files empty
All dirs and placeholder `.tsx`/`.ts` files exist under `frontend/src/`. None have content yet.

### Docker — complete
- `docker/docker-compose.yml` — postgres:16-alpine on :5432, DB=flux/flux/flux

### Context mockups — present
- `context/mockup.png` — visual design reference (read before building any UI)
- `context/mockup.html` — HTML layout reference (study structure, do NOT copy literally)

---

## ▶️ Where to Start Next

**Start here:** implement the empty backend files in this order:
1. `backend/apps/core/models.py` — BaseModel abstract
2. `backend/apps/workspace/models/` — Board, Column, Card (integer positions)
3. Run `uv sync` then `uv run python manage.py makemigrations && migrate`
4. `backend/apps/workspace/serializers/` — board, column, card serializers
5. `backend/apps/workspace/services/card_service.py` — move_card + rebalance_column
6. `backend/apps/workspace/selectors/board_selectors.py` — get_board_detail prefetch
7. `backend/apps/workspace/api/v1/` — APIView classes + urls.py
8. Verify: `curl http://localhost:8000/api/v1/boards/` returns `[]`

**Then:** frontend — install deps, vite.config.ts, index.css @theme, shadcn init, then components.
**Before any UI code:** read `context/mockup.png` and `context/mockup.html` for layout reference.

---

## ⚠️ Hard Rules — Do Not Deviate

1. **APIView pattern only** — never `ModelViewSet` or `DefaultRouter`
2. **Integer positions** (1000, 2000, 3000) — never FloatField
3. **Backend calculates all positions** via `CardService.move_card()` — frontend only sends `card_id`, `source_column_id`, `destination_column_id`, `destination_index`
4. **EditorPanel stays mounted** in `AppLayout` at all times (conditionally visible, never unmounted)
5. **No ViewSets** — each endpoint is a separate `APIView` subclass
6. **Tailwind v4** — `@tailwindcss/vite` plugin, theme in `src/index.css` `@theme {}` block, NO `tailwind.config.js`
7. **shadcn/ui** wraps radix — do not import `@radix-ui` directly in feature code; run `npx shadcn@latest init` to set up
8. **Top-down data flow** — only `BoardView`, `Sidebar`, and `EditorPanel` fetch data; all other components receive props

---

## Project

Flux is a lightweight productivity workspace: boards → columns → cards → markdown notes.
Location: `/home/skrrt/coding/flux`
**Philosophy:** fast, minimal, maintainable, server-first. Not a Notion clone. Not a Jira clone.
Backend is the single source of truth. Reference patterns from alpha7 at `/home/skrrt/code/alpha7` (same stack, same developer).

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
| Vite | **8.x** (not 6) |
| @vitejs/plugin-react | **^6.0.0** (not ^4) |
| Tailwind | v4 (via @tailwindcss/vite) |
| tailwind-merge | **^3.0.0** (not ^2) |
| @dnd-kit/sortable | **^10.0.0** (not ^8) |
| shadcn/ui | latest (Tailwind v4 compatible) |
| vite-plugin-pwa | ^0.21.0 |

---

## package.json Dependencies

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^5.0.0",
    "axios": "^1.0.0",
    "@dnd-kit/core": "^6.0.0",
    "@dnd-kit/sortable": "^10.0.0",
    "@dnd-kit/utilities": "^3.0.0",
    "react-markdown": "^9.0.0",
    "lucide-react": "^0.577.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^3.0.0",
    "class-variance-authority": "^0.7.0"
  },
  "devDependencies": {
    "vite": "^8.0.0",
    "@vitejs/plugin-react": "^6.0.0",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "vite-plugin-pwa": "^0.21.0",
    "typescript": "^5.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0"
  }
}
```

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
GET                /api/v1/search/?q=<query>        ← PostgreSQL FTS
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
- `CardDetailSerializer` — above + content_markdown
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

## Frontend Folder Structure

```
frontend/src/
├── app/
│   ├── App.tsx              ← QueryClientProvider + RouterProvider
│   └── providers.tsx
├── features/
│   ├── board/
│   │   ├── BoardView.tsx        ← DATA OWNER
│   │   ├── BoardList.tsx        ← DATA OWNER
│   │   └── CreateBoardDialog.tsx
│   ├── column/
│   │   ├── Column.tsx           ← PRESENTATIONAL
│   │   └── AddColumnButton.tsx
│   ├── card/
│   │   ├── Card.tsx             ← PRESENTATIONAL
│   │   └── CardList.tsx         ← PRESENTATIONAL
│   └── editor/
│       ├── EditorPanel.tsx      ← DATA OWNER (always mounted)
│       ├── MarkdownEditor.tsx   ← PRESENTATIONAL
│       └── MarkdownPreview.tsx  ← PRESENTATIONAL
├── components/
│   ├── ui/                  ← shadcn components (Button, Input, Textarea, Dialog, DropdownMenu)
│   └── layout/
│       ├── AppLayout.tsx
│       ├── Sidebar.tsx
│       └── Toolbar.tsx
├── services/api.ts          ← axios instance + typed helpers
├── store/ui.ts              ← Zustand: selectedCardId, editorOpen, sidebarOpen
├── hooks/
│   ├── useBoards.ts         ← ['boards']
│   ├── useBoard.ts          ← ['boards', id, 'detail']
│   ├── useCard.ts           ← ['cards', id]
│   └── useDebounce.ts
├── routes/index.tsx
├── lib/utils.ts             ← cn() helper
├── types/index.ts           ← Board, Column, Card, CardDetail, BoardDetail
├── main.tsx
└── index.css                ← @theme tokens (NO tailwind.config.js)
```

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

## Layout Shell

```tsx
// AppLayout.tsx
<div className="flex h-screen overflow-hidden">
  <Sidebar />                    // w-64, shrink-0
  <div className="flex flex-col flex-1 min-w-0">
    <Toolbar />                  // h-12
    <main className="flex-1 overflow-hidden">
      <Outlet />                 // BoardView here
    </main>
  </div>
  <EditorPanel />                // w-[450px], always mounted, CSS translate for show/hide
</div>
```

BoardView: `flex flex-row gap-4 overflow-x-auto h-full p-6`, each column `w-80 flex-shrink-0`.

---

## vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        runtimeCaching: [{ urlPattern: /\/api\/v1\/boards/, handler: 'StaleWhileRevalidate', options: { cacheName: 'boards-cache' } }]
      }
    })
  ],
  server: { port: 3000, proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } } },
  resolve: { alias: { '@': '/src' } }
})
```

---

## Tailwind Theme (src/index.css)

```css
@import "tailwindcss";

@theme {
  --color-bg: #F8FAFC;
  --color-sidebar: #1E293B;
  --color-sidebar-hover: #334155;
  --color-surface: #FFFFFF;
  --color-border: #E2E8F0;
  --color-text: #0F172A;
  --color-text-2: #475569;
  --color-text-3: #94A3B8;
  --color-accent: #0D9488;
  --color-accent-hover: #0F766E;
  --font-sans: 'Inter', system-ui, sans-serif;
  --radius-sm: 4px; --radius-md: 8px; --radius-lg: 12px; --radius-xl: 16px;
}

@layer base {
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { @apply font-sans; }
}
```

(Study context/mockup.html and context/mockup.png before finalising colours.)

---

## shadcn/ui Setup

```bash
npx shadcn@latest init   # select Tailwind v4, installs to src/components/ui/
```

Add: Button, Input, Textarea, Dialog, DropdownMenu, Tooltip, ScrollArea, Separator

---

## Running Locally

```bash
cd docker && docker compose up -d          # postgres on :5432
cd backend && uv sync
uv run python manage.py migrate
uv run python manage.py runserver          # API on :8000

cd frontend && pnpm install
pnpm dev                                   # app on :3000
```

API docs: http://localhost:8000/api/docs/

---

## Context Mockups

Before writing any UI component:
1. Read `context/mockup.png`
2. Read `context/mockup.html`

Study layout, spacing, component hierarchy. Do NOT copy HTML literally into React.

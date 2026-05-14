# Flux — Future Plans

This file tracks features and ideas planned for future development. Nothing here is being built yet.

---

## Auth & Sync

Add user accounts so boards are tied to an identity and accessible from any device. No real-time collaboration — just server-state-as-truth, one user per account.

**Concept:**
- Register / log in with email + password
- JWT tokens — stored in `localStorage`, sent via `Authorization: Bearer` header on every request
- All data (workspaces, boards, columns, cards) is scoped to the logged-in user
- "Sync" is just React Query refetching from the hosted backend — no websockets or CRDTs needed

**Backend changes:**

_Settings_
```python
# Replace in base.py / development.py
DEFAULT_AUTHENTICATION_CLASSES: ["rest_framework_simplejwt.authentication.JWTAuthentication"]
DEFAULT_PERMISSION_CLASSES: ["rest_framework.permissions.IsAuthenticated"]
```

_New endpoints_
```
POST /api/v1/auth/register/    → create user, return tokens
POST /api/v1/auth/login/       → return access + refresh tokens
POST /api/v1/auth/refresh/     → rotate access token
POST /api/v1/auth/logout/      → blacklist refresh token
```

_Model changes_
```
Workspace   →  add user FK (owner)
Board       →  add user FK (owner)
```
Column and Card are already scoped transitively through Board → Workspace.

_All APIView `get_queryset` calls filter by `request.user`_ — users never see each other's data.

**Frontend changes:**
- `/login` and `/register` routes — simple forms, no sidebar/layout
- `authApi.ts` + `useAuth.ts` hook for token management
- Axios interceptor in `api.ts` — attaches `Authorization` header, handles 401 → redirect to `/login`
- Token stored in `localStorage`; on app load, check token validity before rendering `AppLayout`
- Zustand `ui.ts` gets a `currentUser` slice (id, email) populated after login

**Frontend auth flow:**
```
App loads
  └── token in localStorage?
        yes → validate (GET /api/v1/auth/me/) → render AppLayout
        no  → redirect to /login
```

**"From anywhere" requirement — hosting:**
Sync only works if the backend is reachable outside localhost. Recommended targets:
- **Fly.io** — free tier, Postgres addon, Docker-native (easy fit for this stack)
- **Railway** — zero-config Django + Postgres deploys
- **Self-hosted VPS** — full control, nginx + gunicorn + managed Postgres

**Implementation order (when the time comes):**
1. Add `djangorestframework-simplejwt`, wire auth endpoints
2. Add `user` FK to Workspace + Board, write migrations
3. Scope all APIView queries to `request.user`
4. Frontend: login/register pages + axios interceptor
5. Deploy backend to Fly.io / Railway
6. Point frontend `VITE_API_URL` at the hosted backend

**What this is NOT (intentionally out of scope for v1):**
- Multi-user collaboration on the same board
- Real-time sync (websockets / CRDTs)
- OAuth / social login (email + password only to start)
- Email verification / password reset (add later)

---

## Projects (Sidebar Section)

Add a third top-level section to the sidebar alongside **My Boards** and **Workspaces**.

**Concept:**
- Sidebar gets a new "Projects" section
- Each project is a focused unit of work — think a product launch, a client engagement, a research initiative
- A project contains boards, and each board contains columns + cards (same hierarchy as workspaces)
- Clicking a project in the sidebar opens that project's board list
- Clicking a board opens columns/cards as usual

**How it differs from Workspaces:**
- Workspaces are broad organizational folders (e.g. "School", "Work", "Personal")
- Projects are specific, time-bounded efforts (e.g. "Website Redesign Q3", "Client Onboarding — Acme")
- Projects may eventually have additional metadata: status (active/archived), due date, owner, description

**Model:**
```
Project
  id (UUID)
  title
  status  (active | archived)  ← future field
  created_at, updated_at

Board  →  workspace FK (nullable)
       →  project FK (nullable)   ← new FK, same pattern as workspace
```

**Routes (future):**
```
/projects                          → ProjectList
/projects/:projectId               → BoardList (scoped to project)
/projects/:projectId/boards/:id    → BoardView
```

**Sidebar layout (future):**
```
  My Boards
──────────────────────────────
WORKSPACES          [+]
  • School
  • Work
──────────────────────────────
PROJECTS            [+]
  • Website Redesign Q3
  • Client Onboarding — Acme
──────────────────────────────
  Quick search…
```

**Implementation notes (when the time comes):**
- Follow the exact same pattern as Workspace: new model, nullable FK on Board, serializers, APIView endpoints, 3-layer frontend
- `BoardList` will need a third mode alongside personal and workspace
- `CreateBoardDialog` gets a `projectId` prop path
- Board can belong to a workspace OR a project OR neither (My Boards) — mutually exclusive

---

## App Header

The header was removed to keep the UI minimal — the sidebar handles all navigation and the content area is uncluttered. When auth and collaboration are added, a top header bar will make sense.

**Vision:**
```
┌──────────────────────────────────────────────────────────────────────┐
│  [← breadcrumb: My Boards / Q3 Launch / BoardView]   [🔍]  [🔔]  [👤] │
└──────────────────────────────────────────────────────────────────────┘
```

**Planned contents:**
- **Breadcrumb** — workspace → board path (links back to each level)
- **Global search** — wire to existing `GET /api/v1/search/?q=` endpoint
- **Notifications bell** — activity on boards you follow
- **User profile/avatar** — name, logout, settings

**Implementation notes (when the time comes):**
- Add a `<Header />` component in `src/components/layout/`
- Mount it in `AppLayout` above `<main>` (no per-page imports)
- Breadcrumb reads from route params + query cache — no extra API calls
- Keep sidebar expand button in `AppLayout` (absolute-positioned, already there)

---

## Editor Enhancements

Extend the TipTap editor in `EditorPanel` with richer content types. The current stack (`StarterKit`, `Underline`, `TaskList`, `TaskItem`, `tiptap-markdown`) is the base — all additions follow the same extension pattern.

**Low effort — drop-in TipTap extensions:**

| Feature | Package | Notes |
|---|---|---|
| Syntax-highlighted code blocks | `@tiptap/extension-code-block-lowlight` + `lowlight` | Replaces plain `code` block with language-aware highlighting |
| Tables | `@tiptap/extension-table` | Render and edit markdown tables in-editor |
| Text color / highlight | `@tiptap/extension-color` + `@tiptap/extension-highlight` | Colour-coded text, like a highlighter pen |
| Horizontal rule | already in StarterKit | Just needs a toolbar button wired up |

**Medium effort:**

- **Image support** — `@tiptap/extension-image`. Paste or drag an image URL, renders inline. For file uploads, a backend endpoint stores the file and returns a URL that the extension inserts.
- **Slash commands** — typing `/` opens an inline command palette (heading, list, table, image, etc.). Very Notion-like UX. There are community TipTap extensions for this; alternatively hand-roll a `ReactRenderer` suggestion plugin.
- **Collapsible sections** — a custom TipTap node; fold a heading and its content body. Useful for long cards.

**Higher effort — custom nodes:**

- **Drawing / freehand canvas** — embed [Excalidraw](https://excalidraw.com) as a React component mounted inside a custom TipTap node. The drawing serialises to SVG, stored as part of the card content. Good for diagrams and wireframes.
- **Embed blocks** — paste a URL (YouTube, GitHub, tweet) and get a rich preview card rendered as a TipTap node. Requires a backend `/api/v1/unfurl/?url=` endpoint that fetches Open Graph metadata.
- **File attachments** — not an editor node but surfaced in `EditorPanel` below the editor. Upload PDFs or files via a backend endpoint, listed as download links on the card.

**Implementation notes (when the time comes):**
- Add extensions one at a time — each is its own PR
- Toolbar in `TipTapEditor.tsx` grows a button per new extension; keep it icon-only with tooltips to avoid clutter
- `tiptap-markdown` handles serialisation — verify each new node round-trips correctly to markdown before shipping
- Excalidraw embed: store SVG in a new `card_drawings` JSON field or as a separate model; do not bloat `content_markdown`
- Image upload endpoint: `POST /api/v1/uploads/` → returns `{ url }` — store files in `/media/`, served via Django in dev and a CDN/object store in prod

---

## Remove shadcn/ui — Build Own Component Library

Replace all shadcn/ui primitives with hand-rolled components that match Flux's exact design language. The goal is full ownership — no third-party base UI opinions, no `@base-ui/react` dependency, no `src/lib/utils.ts` shim.

**Components to replace (current shadcn usage):**
- `Button` — used in dialogs and forms
- `Dialog` — create board/workspace modals
- `DropdownMenu` — column/card context menus
- `Input`, `Textarea` — form fields
- `ScrollArea` — editor and sidebar scrolling
- `Separator` — sidebar dividers
- `Tooltip` — toolbar hints in TipTapEditor

**Approach:**
- Build each component in `src/components/ui/` as a plain React + Tailwind v4 component — no Radix, no base-ui
- Match the existing visual style exactly so no UI regressions
- Remove `components.json`, `src/lib/utils.ts` shim, and all `@base-ui/react` / `@radix-ui` packages once migration is complete
- Replace one component at a time, ship each as its own PR

**Implementation order (when the time comes):**
1. `Button`, `Input`, `Textarea` — stateless, trivial to replace
2. `Separator`, `ScrollArea` — minimal behaviour
3. `Tooltip` — needs positioning logic (use CSS or a tiny custom hook)
4. `DropdownMenu` — needs focus trap + keyboard nav
5. `Dialog` — needs portal, focus trap, escape handling

---

## Export — JSON & Markdown

Allow users to download their data at the board or card level.

**Scope:**
- **Board export** — entire board (all columns + cards + card content) as a single file
- **Card export** — individual card (title, description, content) as a single file

**Formats:**
- **JSON** — structured dump, useful for backups or importing into other tools
- **Markdown** — human-readable; board exports as a single `.md` file with each column as a heading and cards as sections beneath it

**Rough JSON shape (board):**
```json
{
  "title": "My Board",
  "exported_at": "2026-05-15T10:00:00Z",
  "columns": [
    {
      "title": "To Do",
      "cards": [
        { "title": "Card I", "description": "...", "content": "..." }
      ]
    }
  ]
}
```

**Rough Markdown shape (board):**
```markdown
# My Board

## To Do

### Card I
> This is a description for card

[card content here]
```

**Implementation notes (when the time comes):**
- Backend: add `GET /api/v1/boards/:id/export/?format=json` and `?format=markdown` endpoints — backend renders the file, sets `Content-Disposition: attachment`
- Frontend: export button in the board header (three-dot menu or dedicated icon); card export from the EditorPanel toolbar
- No new models needed — pure read/serialise

---

## Other Ideas (Parking Lot)

- **Card due dates** — add `due_date` field to Card, show in card UI
- **Renameable app** — app name ("Flux") is hardcoded in `Sidebar.tsx` and `index.html`. When needed, centralise it in `src/config.ts` (`APP_NAME`, `APP_INITIAL`) and update those two files. One-line change after that.
- **Card labels/tags** — lightweight tagging system for cards
- ~~**Drag-and-drop**~~ ✅ — reorder cards within a column, move cards across columns, reorder columns, reorder boards. See `docs/drag-and-drop.md`.
- **Search** — wire the existing `GET /api/v1/search/?q=` endpoint to the Quick Search bar
- **Board templates** — create a board with predefined columns (e.g. "To Do / In Progress / Done")
- **Archive** — soft-delete boards/cards instead of hard delete

---

## Desktop / Packaging

Ship Flux as a native desktop app (or a one-command launcher) for Linux and Windows — no browser, no manual server setup.

**Two approaches:**

### Option A — Tauri desktop app (full native experience)
Wrap the Vite/React frontend in a Tauri shell. Tauri spawns the Django backend as a sidecar process on a random local port and serves the frontend as static files. SQLite replaces Postgres (one-line settings change; Django supports it natively).

```
Tauri shell
  └── spawns Django (PyInstaller bundle) on a random local port
  └── serves Vite frontend as static files
  └── SQLite file in user's app data dir
       Linux:   ~/.local/share/flux/flux.db
       Windows: %APPDATA%\flux\flux.db
```

**Effort:** significant — a few weeks for cross-platform packaging stability.
**Payoff:** one-click install, offline use, no browser or Docker required.

### Option B — Shell script launcher (low-effort, good-enough)
A `flux.sh` / `flux.bat` that starts Docker (Postgres), the Django backend, and opens the browser automatically. No packaging, no bundling — just a convenient entry point.

**Effort:** a day or two.
**Payoff:** "one command to run" UX without touching the stack.

**Implementation notes (when the time comes):**
- Option A: migrate `DATABASES` setting to SQLite in a new `desktop.py` settings file; use PyInstaller for the Python bundle; Tauri `sidecar` config to manage the Django process lifecycle
- Option A: CI matrix builds needed: `ubuntu-latest`, `windows-latest` (GitHub Actions)
- Option B: script lives at repo root — `flux.sh` (bash) + `flux.bat` (Windows batch); checks for Docker and opens `http://localhost:3000` after health-check passes

---

## Feature Index

All planned features at a glance:

| Feature | Summary |
|---------|---------|
| **Projects** | Third sidebar section for time-bounded efforts, sits alongside Workspaces |
| **App Header** | Breadcrumb + global search + notifications + user profile bar |
| ~~**Drag-and-drop**~~ ✅ | Cards (within column + cross-column), columns, and boards are all draggable and reorderable. See `docs/drag-and-drop.md`. |
| **Search** | Wire `GET /api/v1/search/?q=` to a Quick Search bar in the sidebar/header |
| **Card due dates** | `due_date` field on Card model, displayed in card UI |
| **Card labels/tags** | Lightweight colour-coded tagging system for cards |
| **Board templates** | Create a board with predefined columns (e.g. "To Do / In Progress / Done") |
| **Archive** | Soft-delete for boards and cards instead of hard delete |
| **Renameable app** | Centralise app name in `src/config.ts` so a single change renames the whole app |
| **Desktop app (Tauri)** | Native Linux/Windows app — Tauri shell + PyInstaller Django sidecar + SQLite |
| **Launcher script** | `flux.sh` / `flux.bat` that starts Docker + backend and opens the browser in one command |
| **Auth & Sync** | JWT login/register, user-scoped data, hosted backend — access your boards from any device |
| **Own component library** | Replace all shadcn/ui primitives with hand-rolled Tailwind v4 components; remove all Radix/base-ui dependencies |
| **Export (JSON & Markdown)** | Download boards or individual cards as JSON (structured backup) or Markdown (human-readable) |
| **Editor — syntax highlighting** | Code blocks with language-aware highlighting via `@tiptap/extension-code-block-lowlight` |
| **Editor — tables** | Render and edit markdown tables in-editor via `@tiptap/extension-table` |
| **Editor — slash commands** | `/` command palette for inserting blocks (Notion-style) |
| **Editor — image support** | Inline images via URL paste or file upload to backend `/api/v1/uploads/` |
| **Editor — drawing** | Excalidraw canvas embedded as a TipTap node; serialises to SVG stored on the card |
| **Editor — embeds** | Paste a URL → rich preview card (YouTube, GitHub, tweet) via backend unfurl endpoint |

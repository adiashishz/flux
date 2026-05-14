# Flux — Future Plans

This file tracks features and ideas planned for future development. Nothing here is being built yet.

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

## Other Ideas (Parking Lot)

- **Card due dates** — add `due_date` field to Card, show in card UI
- **Renameable app** — app name ("Flux") is hardcoded in `Sidebar.tsx` and `index.html`. When needed, centralise it in `src/config.ts` (`APP_NAME`, `APP_INITIAL`) and update those two files. One-line change after that.
- **Card labels/tags** — lightweight tagging system for cards
- **Drag-and-drop** — reorder cards within a column and move across columns (`@dnd-kit/sortable` already installed)
- **Search** — wire the existing `GET /api/v1/search/?q=` endpoint to the Quick Search bar
- **Board templates** — create a board with predefined columns (e.g. "To Do / In Progress / Done")
- **Archive** — soft-delete boards/cards instead of hard delete

---

## Feature Index

All planned features at a glance:

| Feature | Summary |
|---------|---------|
| **Projects** | Third sidebar section for time-bounded efforts, sits alongside Workspaces |
| **App Header** | Breadcrumb + global search + notifications + user profile bar |
| **Drag-and-drop** | Reorder and move cards across columns (`@dnd-kit/sortable` already installed) |
| **Search** | Wire `GET /api/v1/search/?q=` to a Quick Search bar in the sidebar/header |
| **Card due dates** | `due_date` field on Card model, displayed in card UI |
| **Card labels/tags** | Lightweight colour-coded tagging system for cards |
| **Board templates** | Create a board with predefined columns (e.g. "To Do / In Progress / Done") |
| **Archive** | Soft-delete for boards and cards instead of hard delete |
| **Renameable app** | Centralise app name in `src/config.ts` so a single change renames the whole app |

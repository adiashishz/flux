# Caching Strategy

## Overview

Flux uses **TanStack Query (React Query)** as its only caching layer — entirely client-side, in-memory. There is no Redis, no server-side cache, and no service worker cache. This is intentional: Flux is a single-user app with no real-time collaboration, so data only changes when *you* change it. The goal is simple: **API calls fire only when something is actually intended to be saved or fetched for the first time.**

---

## Global Configuration

Configured once in `src/app/providers.tsx`:

```ts
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      gcTime: 10 * 60 * 1000,         // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})
```

### Why these values for Flux

| Option | Value | Reason |
|--------|-------|--------|
| `staleTime` | 5 min | Single user — data only changes when you change it. Clicking a card, opening/closing the editor, and navigating back to a board all serve from cache within this window. |
| `gcTime` | 10 min | Keeps board and card data in memory while the user is working. Navigating between boards doesn't re-fetch. |
| `refetchOnWindowFocus` | `false` | Users constantly switch tabs while writing notes. Without this, every tab switch would trigger background re-fetches. |
| `retry` | `1` | Fail fast. One retry is enough to handle a transient network hiccup. Don't hammer the API on errors. |

---

## Query Keys

All query keys are defined as constants to ensure consistent cache targeting:

```ts
// useBoards.ts
export const boardKeys = {
  all: ["boards"],                          // board list
  detail: (id) => ["boards", id, "detail"], // single board + its columns + cards
}

// useCards.ts
export const cardKeys = {
  detail: (id) => ["cards", id],            // single card with full markdown content
}
```

TanStack Query uses **prefix matching** for invalidation. `invalidateQueries({ queryKey: ["boards"] })` invalidates both `["boards"]` and `["boards", id, "detail"]` — every key that starts with `["boards"]`.

---

## Mutation Invalidation Map

Each mutation targets only the queries that need to reflect the change. Nothing broader.

| Mutation | Invalidates / Updates | Why |
|----------|----------------------|-----|
| `useCreatePersonalBoard` | `boardKeys.all` | New board appears in the board list |
| `useUpdateBoard` | `boardKeys.all` | Title/description change reflected in board list |
| `useDeleteBoard` | `boardKeys.all` | Board removed from list |
| `useCreateColumn` | `boardKeys.detail(boardId)` | New column appears in board view |
| `useUpdateColumn` | `boardKeys.detail(boardId)` + `["cards"]` | Column title updates in board view AND in any open card's `column_title` field |
| `useDeleteColumn` | `boardKeys.detail(boardId)` | Column removed from board view |
| `useCreateCard` | `boardKeys.detail(boardId)` | New card appears in the column |
| `useUpdateCard` | `setQueryData(cardKeys.detail(id), response)` | See below |
| `useDeleteCard` | `boardKeys.detail(boardId)` | Card removed from column |
| `useMoveCard` | `boardKeys.detail(boardId)` | Card position/column updated in board view |

---

## `useUpdateCard` — No Re-fetch on Save

Card updates (title edits, content saves from the editor) are the most frequent mutation in the app. Using `invalidateQueries` here would trigger a GET after every debounced save — wasteful.

Instead, the server's PATCH response is written directly into the cache:

```ts
// hooks/queries/useCards.ts
onSuccess: (updatedCard, { id }) => {
  qc.setQueryData(cardKeys.detail(id), updatedCard)
}
```

The PATCH fires to persist to the database. The response (a full `CardDetail` object) replaces the cached value in-place. No follow-up GET is made.

---

## Dirty-check Guard in EditorPanel

TipTap's `onUpdate` fires when the editor initialises with content (not just when the user types). Without a guard, this would trigger a PATCH on every card open even if nothing changed.

`EditorPanel` tracks the last server-persisted values in refs:

```ts
const savedTitle = useRef("")
const savedContent = useRef("")

// On card load:
savedTitle.current = card.title
savedContent.current = card.content_markdown

// Before firing PATCH:
if (debouncedContent === savedContent.current) return  // skip — nothing changed
if (debouncedTitle === savedTitle.current) return
```

This means a PATCH is sent **only when the value has actually changed from what the server last returned.** Opening a card, closing it, switching cards — zero writes.

---

## Data Flow: Read Path

```
User clicks a card
       │
       ▼
useCard(id) — is data in cache and staleTime not expired?
       │
   YES │                          NO
       ▼                          ▼
Serve from memory         GET /api/v1/cards/:id/
(zero HTTP)               Store in cache
                          Serve to component
```

---

## Data Flow: Write Path

```
User types in editor
       │
       ▼
TipTapEditor.onUpdate → setContent(markdown)
       │
       ▼
useDebounce(content, 1500ms) — wait for pause in typing
       │
       ▼
dirty check: debouncedContent === savedContent.current?
       │
   YES │                          NO
       ▼                          ▼
    skip                 PATCH /api/v1/cards/:id/
                                  │
                                  ▼
                         setQueryData(cardKeys.detail(id), response)
                         (cache updated, no follow-up GET)
```

---

## What is NOT cached

- **Search results** — `GET /api/v1/search/?q=` is intentionally not cached. Search is always live.
- **Authentication** — auth is disabled in this version of Flux.

---

## Why not Redis?

Redis is a server-side cache that speeds up database queries when the server receives a request. The problem Flux had was the **frontend making HTTP requests it shouldn't make at all** — not that those requests were slow. Redis would have made redundant requests faster, not eliminated them. The right tool was a client-side cache with a `staleTime` that prevents the request from being issued in the first place.

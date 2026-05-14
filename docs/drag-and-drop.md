# Drag-and-Drop

Flux supports drag-and-drop reordering at three levels: **boards** (grid), **columns** (horizontal), and **cards** (vertical, including cross-column moves). All three use the same stack and the same position-based persistence pattern.

---

## Stack

| Layer | Library |
|-------|---------|
| DnD primitives | `@dnd-kit/core` |
| Sortable utilities | `@dnd-kit/sortable` |
| CSS transforms | `@dnd-kit/utilities` |

---

## Backend Pattern

Every draggable entity has an integer `position` field. Positions are spaced 1000 apart (1000, 2000, 3000 …). A move inserts the item by calculating a midpoint — no mass-rewrite of sibling positions on every drag.

```
Item A  position=1000
Item B  position=2000   ← drag B between C and D
Item C  position=3000
Item D  position=4000

After: A=1000, C=3000, B=3500, D=4000
```

When a gap shrinks below 10 units, the service **rebalances** the entire list back to multiples of 1000.

### Services

Each level has a dedicated service following identical logic:

| Service | File | Scope |
|---------|------|-------|
| `CardService` | `backend/apps/workspace/services/card_service.py` | Cards within a column |
| `ColumnService` | `backend/apps/workspace/services/column_service.py` | Columns within a board |
| `BoardService` | `backend/apps/workspace/services/board_service.py` | Boards within a workspace (or personal) |

All three share the same structure:

```python
class XxxService:
    POSITION_STEP = 1000
    REBALANCE_THRESHOLD = 10

    @staticmethod
    @transaction.atomic
    def move_xxx(item_id, ..., dest_index): ...   # main entry point

    @staticmethod
    def _calculate_position(ordered_siblings, dest_index): ...  # midpoint logic

    @staticmethod
    def _needs_rebalance(...): ...                # gap check

    @staticmethod
    @transaction.atomic
    def rebalance_xxx(...): ...                   # bulk position reset
```

### Endpoints

```
POST /api/v1/cards/:id/move/
  body: { source_column_id, destination_column_id, destination_index }

POST /api/v1/columns/:id/move/
  body: { board_id, destination_index }

POST /api/v1/boards/:id/move/
  body: { destination_index }
```

`destination_index` is always **0-based** and is calculated by the frontend from the visual order at the time of drop. The backend ignores it as a raw index — it only uses it to look up adjacent siblings and compute a midpoint position.

---

## Frontend Pattern

### Component Hierarchy

```
BoardList          ← DndContext (boards grid)
  SortableContext  ← board IDs, rectSortingStrategy
    SortableBoardCard (useSortable)

BoardView          ← DndContext (columns + cards, shared)
  SortableContext  ← column IDs, horizontalListSortingStrategy
    Column (useSortable — column drag handle on header)
      SortableContext  ← card IDs per column, verticalListSortingStrategy
        Card (useSortable)
  DragOverlay
    BoardCardOverlay | DragOverlayCard | ColumnDragOverlay
```

### Key Files

| File | Role |
|------|------|
| `frontend/src/features/board/BoardList.tsx` | DnD context for board grid |
| `frontend/src/features/board/BoardView.tsx` | DnD context for columns + cards |
| `frontend/src/features/column/Column.tsx` | Sortable column; drag handle on header; droppable card area |
| `frontend/src/features/card/components/Card.tsx` | Sortable card |
| `frontend/src/features/card/CardList.tsx` | Passes `activeCardId` down for overlay opacity |
| `frontend/src/features/card/components/DragOverlayCard.tsx` | Floating card overlay |

### Sensor

All three contexts use `PointerSensor` with `activationConstraint: { distance: 8 }`. This means a tap/click never starts a drag — at least 8px of pointer movement is required. This keeps card clicks (open editor) and column title clicks (rename) working normally.

```typescript
const sensors = useSensors(
  useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
)
```

### Type Discrimination

`BoardView` handles both cards and columns in a single `DndContext`. They are distinguished via `data.type` passed to `useSortable`:

```typescript
// Card
useSortable({ id: card.id, data: { type: "card" } })

// Column
useSortable({ id: column.id, data: { type: "column" } })
```

Event handlers read `active.data.current?.type` to dispatch to the correct branch.

### Column Drag Handle

`{...listeners}` from `useSortable` are applied only to the **column header div**, not the entire column. This means cards inside the column remain independently draggable while the header is the grab target for column reordering.

The dropdown menu trigger and the rename input both call `e.stopPropagation()` on `onPointerDown` so clicking them doesn't start a column drag.

### Empty Column Drop Target

Without extra wiring, dropping a card into an empty column fails silently — there are no sortable items to land on. The fix is `useDroppable({ id: column.id })` on the card area div. Event handlers check both card IDs and column IDs when resolving the drop target:

```typescript
const destColumn =
  board.columns.find(col => col.cards.some(c => c.id === overId)) ?? // landed on a card
  board.columns.find(col => col.id === overId)                        // landed on empty column area
```

### Cross-Column Card Moves — `onDragOver`

When a card is dragged across a column boundary, `handleDragOver` updates the React Query cache immediately so the card appears in the new column while still dragging:

```typescript
function handleDragOver(event) {
  // only fires for cards crossing a column boundary
  qc.setQueryData(boardKeys.detail(boardId), (old) => ({
    ...old,
    columns: old.columns.map(col => {
      if (col.id === sourceColumn.id)
        return { ...col, cards: col.cards.filter(c => c.id !== activeId) }
      if (col.id === destColumn.id) {
        const newCards = [...col.cards]
        newCards.splice(insertAt, 0, { ...activeCard, column_id: destColumn.id })
        return { ...col, cards: newCards }
      }
      return col
    }),
  }))
}
```

### Stale Closure Problem — Why `sourceColumnId` is Captured at Drag Start

`handleDragEnd` cannot look up `sourceColumn` from the current board state because `onDragOver` has already mutated the cache — the card is now in the destination column, so `sourceColumn` lookup returns `undefined` and the function exits without making an API call.

The fix: `sourceColumnId` is captured in `handleDragStart` and stored in the `activeItem` state, before any cache mutations happen.

```typescript
type ActiveItem =
  | { type: "card"; data: CardType; sourceColumnId: string }  // ← captured at drag start
  | { type: "column"; data: ColumnType & { cards: CardType[] } }
```

`handleDragEnd` reads the **live cache** via `qc.getQueryData()` (not the stale React closure `board`) and uses the saved `sourceColumnId` for the API call.

### Column-over-Card Resolution

When dragging a column, `over.id` often resolves to a **card inside the target column** (because cards are sortable items too). The column branch of `handleDragEnd` resolves this:

```typescript
const resolvedOverColumnId =
  currentBoard.columns.find(col => col.id === overId)?.id ??
  currentBoard.columns.find(col => col.cards.some(c => c.id === overId))?.id
```

### Optimistic Updates + Rollback

All three move operations follow the same pattern:

```typescript
const snapshot = qc.getQueryData(queryKey)

qc.setQueryData(queryKey, optimisticState)   // update UI immediately

mutate(payload, {
  onError: () => qc.setQueryData(queryKey, snapshot)  // revert on failure
})
// onSuccess (in the mutation hook) calls invalidateQueries → reconciles with server positions
```

---

## `destination_index` Calculation

The index sent to the backend is the **0-based visual position** of the item after the drop, in the destination list (excluding the item itself for the API computation — the backend handles this via `.exclude(id=item_id)`).

| Scenario | How `destination_index` is computed |
|----------|-------------------------------------|
| Same-column card reorder | `arrayMove(cards, oldIndex, newIndex)` → `newIndex` |
| Cross-column card move | Card position in `destColumn.cards` after `onDragOver` updated the cache |
| Column reorder | `arrayMove(columns, oldIndex, newIndex)` → `newIndex` |
| Board reorder | `arrayMove(boards, oldIndex, newIndex)` → `newIndex` |

---

## Adding DnD to a New Entity

Follow this checklist:

1. **Model** — add `position = models.IntegerField(default=1000)`, change `Meta.ordering = ["position"]`
2. **Service** — copy `CardService` pattern, scope siblings correctly
3. **Serializer** — add `XxxMoveSerializer` with `destination_index` field
4. **View** — add `XxxMoveView` (POST `/:id/move/`)
5. **URL** — register the move endpoint
6. **`boardsApi.ts` / relevant API file** — add `moveXxx()` function
7. **Hook** — add `useMoveXxx()` with `onSuccess` invalidation
8. **Component** — add `useSortable`, apply `ref`, `style`, `attributes`, `listeners`
9. **Parent** — wrap with `DndContext` + `SortableContext`, implement `handleDragStart` / `handleDragEnd`, add `DragOverlay`

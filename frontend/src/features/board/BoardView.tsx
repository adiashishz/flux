import { useState } from "react"
import { useParams } from "react-router-dom"
import { usePageTitle } from "@/hooks/usePageTitle"
import { Kanban, List, Calendar } from "lucide-react"
import {
  DndContext,
  DragOverlay,
  closestCorners,
  useSensor,
  useSensors,
  PointerSensor,
  type DragStartEvent,
  type DragOverEvent,
  type DragEndEvent,
} from "@dnd-kit/core"
import { SortableContext, arrayMove, horizontalListSortingStrategy } from "@dnd-kit/sortable"
import { useQueryClient } from "@tanstack/react-query"
import { Column } from "@/features/column/Column"
import { AddColumnButton } from "@/features/column/components/AddColumnButton"
import { DragOverlayCard } from "@/features/card/components/DragOverlayCard"
import { useBoard, boardKeys, useMoveColumn } from "@/hooks/queries/useBoards"
import { useMoveCard } from "@/hooks/queries/useCards"
import { cn } from "@/utils/cn"
import type { BoardDetail, Card as CardType, Column as ColumnType } from "@/types"

const VIEWS = [
  { label: "Kanban", icon: Kanban },
  { label: "List", icon: List },
  { label: "Calendar", icon: Calendar },
] as const

type ActiveItem =
  | { type: "card"; data: CardType; sourceColumnId: string }
  | { type: "column"; data: ColumnType & { cards: CardType[] } }

function ColumnDragOverlay({ column }: { column: ColumnType & { cards: CardType[] } }) {
  return (
    <div className="w-80 flex flex-col shrink-0 opacity-95 rotate-1 cursor-grabbing">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-semibold text-[#0F172A] text-sm truncate">{column.title}</h3>
        <span className="bg-slate-100 text-[#475569] text-xs rounded-full px-2 py-0.5 font-medium shrink-0">
          {column.cards.length}
        </span>
      </div>
      <div className="flex flex-col gap-2">
        {column.cards.map(card => (
          <div key={card.id} className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4">
            <p className="font-semibold text-[#0F172A] text-sm mb-1 leading-snug">{card.title}</p>
            {card.description && (
              <p className="text-xs text-[#475569] line-clamp-2">{card.description}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export function BoardView() {
  const { id } = useParams<{ id: string }>()
  const [activeView, setActiveView] = useState<string>("Kanban")
  const [activeItem, setActiveItem] = useState<ActiveItem | null>(null)

  const { data: board, isLoading, isError } = useBoard(id ?? "")
  const qc = useQueryClient()
  const { mutate: moveCard } = useMoveCard(board?.id ?? "")
  const { mutate: moveColumn } = useMoveColumn(board?.id ?? "")

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  )

  usePageTitle(board?.title ?? "")

  function handleDragStart(event: DragStartEvent) {
    if (!board) return
    const type = event.active.data.current?.type as "card" | "column"

    if (type === "card") {
      const sourceCol = board.columns.find(col => col.cards.some(c => c.id === event.active.id))
      const card = sourceCol?.cards.find(c => c.id === event.active.id)
      if (card && sourceCol) setActiveItem({ type: "card", data: card, sourceColumnId: sourceCol.id })
    } else if (type === "column") {
      const col = board.columns.find(c => c.id === event.active.id)
      if (col) setActiveItem({ type: "column", data: col })
    }
  }

  function handleDragOver(event: DragOverEvent) {
    if (!board) return
    const { active, over } = event
    if (!over) return

    if (active.data.current?.type !== "card") return

    const activeId = active.id as string
    const overId = over.id as string

    const sourceColumn = board.columns.find(col => col.cards.some(c => c.id === activeId))
    const destColumn =
      board.columns.find(col => col.cards.some(c => c.id === overId)) ??
      board.columns.find(col => col.id === overId)

    if (!sourceColumn || !destColumn) return
    if (sourceColumn.id === destColumn.id) return

    qc.setQueryData<BoardDetail>(boardKeys.detail(board.id), (old) => {
      if (!old) return old
      const activeCard = sourceColumn.cards.find(c => c.id === activeId)!
      const overIndex = destColumn.cards.findIndex(c => c.id === overId)
      const insertAt = overIndex === -1 ? destColumn.cards.length : overIndex

      return {
        ...old,
        columns: old.columns.map(col => {
          if (col.id === sourceColumn.id) {
            return { ...col, cards: col.cards.filter(c => c.id !== activeId) }
          }
          if (col.id === destColumn.id) {
            const newCards = [...col.cards]
            newCards.splice(insertAt, 0, { ...activeCard, column_id: destColumn.id })
            return { ...col, cards: newCards }
          }
          return col
        }),
      }
    })
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    // Save before clearing — sourceColumnId is captured at drag start, before onDragOver mutations
    const savedItem = activeItem
    setActiveItem(null)

    if (!over || !board) return

    const activeId = active.id as string
    const overId = over.id as string
    const type = active.data.current?.type as "card" | "column"
    const boardId = board.id

    // Always read the live cache — onDragOver may have already moved cards between columns
    const currentBoard = qc.getQueryData<BoardDetail>(boardKeys.detail(boardId))
    if (!currentBoard) return

    if (type === "card" && savedItem?.type === "card") {
      const sourceColumnId = savedItem.sourceColumnId

      const destColumn =
        currentBoard.columns.find(col => col.cards.some(c => c.id === overId)) ??
        currentBoard.columns.find(col => col.id === overId)
      if (!destColumn) return

      if (sourceColumnId === destColumn.id) {
        // Same-column reorder: onDragOver never touched the cache, so currentBoard is the original order
        const cards = destColumn.cards
        const oldIndex = cards.findIndex(c => c.id === activeId)
        const newIndex = cards.findIndex(c => c.id === overId)
        if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) return

        const reordered = arrayMove(cards, oldIndex, newIndex)
        const snapshot = qc.getQueryData<BoardDetail>(boardKeys.detail(boardId))

        qc.setQueryData<BoardDetail>(boardKeys.detail(boardId), (old) => {
          if (!old) return old
          return {
            ...old,
            columns: old.columns.map(col =>
              col.id === destColumn.id ? { ...col, cards: reordered } : col
            ),
          }
        })

        moveCard(
          { id: activeId, payload: { source_column_id: sourceColumnId, destination_column_id: destColumn.id, destination_index: newIndex } },
          { onError: () => qc.setQueryData(boardKeys.detail(boardId), snapshot) }
        )
      } else {
        // Cross-column: onDragOver already placed the card in destColumn in the cache
        const cardPositionInDest = destColumn.cards.findIndex(c => c.id === activeId)
        const destination_index = cardPositionInDest === -1 ? destColumn.cards.length : cardPositionInDest
        const snapshot = qc.getQueryData<BoardDetail>(boardKeys.detail(boardId))

        moveCard(
          { id: activeId, payload: { source_column_id: sourceColumnId, destination_column_id: destColumn.id, destination_index } },
          { onError: () => qc.setQueryData(boardKeys.detail(boardId), snapshot) }
        )
      }
    } else if (type === "column") {
      // over.id can be a card inside the target column (nested sortable) — resolve to column ID
      const resolvedOverColumnId =
        currentBoard.columns.find(col => col.id === overId)?.id ??
        currentBoard.columns.find(col => col.cards.some(c => c.id === overId))?.id
      if (!resolvedOverColumnId) return

      const oldIndex = currentBoard.columns.findIndex(col => col.id === activeId)
      const newIndex = currentBoard.columns.findIndex(col => col.id === resolvedOverColumnId)
      if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) return

      const reordered = arrayMove([...currentBoard.columns], oldIndex, newIndex)
      const snapshot = qc.getQueryData<BoardDetail>(boardKeys.detail(boardId))

      qc.setQueryData<BoardDetail>(boardKeys.detail(boardId), (old) => {
        if (!old) return old
        return { ...old, columns: reordered }
      })

      moveColumn(
        { id: activeId, payload: { board_id: boardId, destination_index: newIndex } },
        { onError: () => qc.setQueryData(boardKeys.detail(boardId), snapshot) }
      )
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full border-2 border-[#0D9488] border-t-transparent animate-spin" />
        </div>
      </div>
    )
  }

  if (isError || !board) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex items-center justify-center text-sm text-[#94A3B8]">
          Could not load board.
        </div>
      </div>
    )
  }

  const activeCardId = activeItem?.type === "card" ? activeItem.data.id : undefined

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-col flex-1 overflow-hidden">
        <div className="px-6 pt-5 pb-0 shrink-0">
          <h1 className="text-xl font-bold text-[#0F172A] mb-3">{board.title}</h1>
          <div className="flex items-center gap-1">
            {VIEWS.map(({ label, icon: Icon }) => (
              <button
                key={label}
                onClick={() => setActiveView(label)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium border-b-2 transition-colors",
                  activeView === label
                    ? "border-[#0D9488] text-[#0D9488]"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                )}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>
        </div>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <SortableContext items={board.columns.map(c => c.id)} strategy={horizontalListSortingStrategy}>
            <div className="flex flex-row gap-6 overflow-x-auto flex-1 px-6 pt-4 pb-6 items-start">
              {board.columns.map((column) => (
                <Column key={column.id} column={column} boardId={board.id} activeCardId={activeCardId} />
              ))}
              <AddColumnButton boardId={board.id} />
            </div>
          </SortableContext>

          <DragOverlay dropAnimation={null}>
            {activeItem?.type === "card" && <DragOverlayCard card={activeItem.data} />}
            {activeItem?.type === "column" && <ColumnDragOverlay column={activeItem.data} />}
          </DragOverlay>
        </DndContext>
      </div>
    </div>
  )
}

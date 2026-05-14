import { useState, useRef, useEffect } from "react"
import { MoreHorizontal, Plus } from "lucide-react"
import { SortableContext, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable"
import { useDroppable } from "@dnd-kit/core"
import { CSS } from "@dnd-kit/utilities"
import { CardList } from "@/features/card/CardList"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useDeleteColumn, useUpdateColumn } from "@/hooks/queries/useBoards"
import { useCreateCard } from "@/hooks/queries/useCards"
import { cn } from "@/lib/utils"
import type { Column as ColumnType, Card } from "@/types"

interface ColumnProps {
  column: ColumnType & { cards: Card[] }
  boardId: string
  activeCardId?: string
}

export function Column({ column, boardId, activeCardId }: ColumnProps) {
  const { mutate: deleteColumn } = useDeleteColumn(boardId)
  const { mutate: updateColumn } = useUpdateColumn(boardId)
  const { mutate: createCard } = useCreateCard(boardId)

  const [editing, setEditing] = useState(false)
  const [titleValue, setTitleValue] = useState(column.title)
  const inputRef = useRef<HTMLInputElement>(null)

  const {
    attributes,
    listeners,
    setNodeRef: setColumnRef,
    transform,
    transition,
    isDragging: isColumnDragging,
  } = useSortable({ id: column.id, data: { type: "column" } })

  const colStyle = { transform: CSS.Transform.toString(transform), transition }

  const { setNodeRef: setDropRef } = useDroppable({ id: column.id })

  useEffect(() => {
    if (editing) inputRef.current?.select()
  }, [editing])

  function commitTitle() {
    const trimmed = titleValue.trim()
    if (trimmed && trimmed !== column.title) {
      updateColumn({ id: column.id, data: { title: trimmed } })
    } else {
      setTitleValue(column.title)
    }
    setEditing(false)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") commitTitle()
    if (e.key === "Escape") { setTitleValue(column.title); setEditing(false) }
  }

  return (
    <div
      ref={setColumnRef}
      style={colStyle}
      className={cn("w-80 flex flex-col shrink-0 max-h-full", isColumnDragging && "opacity-40")}
    >
      {/* Header — drag handle for column */}
      <div
        className="flex items-center justify-between mb-3 cursor-grab active:cursor-grabbing"
        {...attributes}
        {...listeners}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {editing ? (
            <input
              ref={inputRef}
              value={titleValue}
              onChange={(e) => setTitleValue(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={handleKeyDown}
              onPointerDown={(e) => e.stopPropagation()}
              className="font-semibold text-[#0F172A] text-sm bg-transparent outline-none w-full p-0"
            />
          ) : (
            <h3
              className="font-semibold text-[#0F172A] text-sm truncate"
              onClick={() => setEditing(true)}
              title="Click to rename"
            >
              {column.title}
            </h3>
          )}
          {!editing && (
            <span className="bg-slate-100 text-[#475569] text-xs rounded-full px-2 py-0.5 font-medium shrink-0">
              {column.cards.length}
            </span>
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger
            className="p-1 rounded-md text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors ml-1 shrink-0"
            onPointerDown={(e) => e.stopPropagation()}
          >
            <MoreHorizontal size={16} />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuItem onClick={() => setEditing(true)}>
              Rename
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-red-600"
              onClick={() => deleteColumn(column.id)}
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Cards — droppable area */}
      <div ref={setDropRef} className="flex-1 overflow-y-auto">
        <SortableContext items={column.cards.map(c => c.id)} strategy={verticalListSortingStrategy}>
          <CardList cards={column.cards} activeCardId={activeCardId} />
        </SortableContext>
      </div>

      <button
        onClick={() => createCard({ columnId: column.id, title: "New card" })}
        className="flex items-center justify-center gap-2 mt-3 h-10 w-full rounded-xl border-2 border-dashed border-[#E2E8F0] text-[#94A3B8] text-sm hover:border-[#0D9488] hover:text-[#0D9488] transition-colors"
      >
        <Plus size={15} />
        Add card
      </button>
    </div>
  )
}

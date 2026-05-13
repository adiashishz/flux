import { MoreHorizontal, Plus } from "lucide-react"
import { CardList } from "@/features/card/CardList"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useDeleteColumn } from "@/hooks/queries/useBoards"
import { useCreateCard } from "@/hooks/queries/useCards"
import type { Column as ColumnType, Card } from "@/types"

interface ColumnProps {
  column: ColumnType & { cards: Card[] }
  boardId: string
}

export function Column({ column, boardId }: ColumnProps) {
  const { mutate: deleteColumn } = useDeleteColumn(boardId)
  const { mutate: createCard } = useCreateCard(boardId)

  return (
    <div className="w-80 flex flex-col shrink-0 max-h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-[#0F172A] text-sm">{column.title}</h3>
          <span className="bg-slate-100 text-[#475569] text-xs rounded-full px-2 py-0.5 font-medium">
            {column.cards.length}
          </span>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="p-1 rounded-md text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors">
              <MoreHorizontal size={16} />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuItem
              className="text-red-600"
              onClick={() => deleteColumn(column.id)}
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-y-auto">
        <CardList cards={column.cards} />
      </div>

      {/* Add card — placeholder, full impl in next phase */}
      <button
        onClick={() => createCard({ columnId: column.id, title: "New card" })}
        className="flex items-center gap-1.5 mt-3 px-2 py-1.5 rounded-md text-[#94A3B8] text-sm hover:bg-slate-100 hover:text-[#475569] transition-colors w-full"
      >
        <Plus size={14} />
        Add card
      </button>
    </div>
  )
}

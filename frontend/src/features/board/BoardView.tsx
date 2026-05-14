import { useState } from "react"
import { useParams } from "react-router-dom"
import { Kanban, List, Calendar } from "lucide-react"
import { Column } from "@/features/column/Column"
import { AddColumnButton } from "@/features/column/components/AddColumnButton"
import { useBoard } from "@/hooks/queries/useBoards"
import { cn } from "@/utils/cn"

const VIEWS = [
  { label: "Kanban", icon: Kanban },
  { label: "List", icon: List },
  { label: "Calendar", icon: Calendar },
] as const

export function BoardView() {
  const { id } = useParams<{ id: string }>()
  const [activeView, setActiveView] = useState<string>("Kanban")
  const { data: board, isLoading, isError } = useBoard(id ?? "")

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
        <div className="flex flex-row gap-6 overflow-x-auto flex-1 px-6 pt-4 pb-6 items-start">
          {board.columns.map((column) => (
            <Column key={column.id} column={column} boardId={board.id} />
          ))}
          <AddColumnButton boardId={board.id} />
        </div>
      </div>
    </div>
  )
}

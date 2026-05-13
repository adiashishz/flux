import { useParams } from "react-router-dom"
import { Toolbar } from "@/components/layout/Toolbar"
import { Column } from "@/features/column/Column"
import { AddColumnButton } from "@/features/column/components/AddColumnButton"
import { useBoard } from "@/hooks/queries/useBoards"

export function BoardView() {
  const { id } = useParams<{ id: string }>()
  const { data: board, isLoading, isError } = useBoard(id ?? "")

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <Toolbar title="Loading…" />
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full border-2 border-[#0D9488] border-t-transparent animate-spin" />
        </div>
      </div>
    )
  }

  if (isError || !board) {
    return (
      <div className="flex flex-col h-full">
        <Toolbar title="Board not found" />
        <div className="flex-1 flex items-center justify-center text-sm text-[#94A3B8]">
          Could not load board.
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <Toolbar title={board.title} />
      <div className="flex flex-row gap-6 overflow-x-auto h-full p-6 items-start">
        {board.columns.map((column) => (
          <Column key={column.id} column={column} boardId={board.id} />
        ))}
        <AddColumnButton boardId={board.id} />
      </div>
    </div>
  )
}

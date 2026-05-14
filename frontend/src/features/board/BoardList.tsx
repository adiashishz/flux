import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Plus, SlidersHorizontal, Kanban, List, Calendar, MoreVertical, Pencil, Trash2 } from "lucide-react"
import { CreateBoardDialog } from "./components/CreateBoardDialog"
import { EditBoardDialog } from "./components/EditBoardDialog"
import { cn } from "@/utils/cn"
import { useBoards, useDeleteBoard } from "@/hooks/queries/useBoards"
import { useWorkspace } from "@/hooks/queries/useWorkspaces"
import relativeTime from "@/utils/relativeTime"
import type { Board } from "@/types"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const VIEWS = [
  { label: "Kanban", icon: Kanban },
  { label: "List", icon: List },
  { label: "Calendar", icon: Calendar },
] as const

export function BoardList() {
  const navigate = useNavigate()
  const { workspaceId } = useParams<{ workspaceId?: string }>()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingBoard, setEditingBoard] = useState<Board | null>(null)
  const [activeView, setActiveView] = useState<string>("Kanban")
  const { mutate: deleteBoard } = useDeleteBoard()

  const { data: personalBoards, isLoading: personalLoading } = useBoards()
  const { data: workspace, isLoading: workspaceLoading } = useWorkspace(workspaceId)

  const isWorkspaceMode = !!workspaceId
  const boards: Board[] = isWorkspaceMode ? (workspace?.boards ?? []) : (personalBoards ?? [])
  const isLoading = isWorkspaceMode ? workspaceLoading : personalLoading
  const title = isWorkspaceMode ? (workspace?.title ?? "Loading…") : "My Boards"

  function boardHref(boardId: string) {
    return isWorkspaceMode
      ? `/workspaces/${workspaceId}/boards/${boardId}`
      : `/boards/${boardId}`
  }

  return (
    <div className="flex flex-col h-full bg-[#E2E8F0]">
      <div className="flex-1 overflow-y-auto p-8">
        <h1 className="text-xl font-bold text-[#0F172A] mb-5">{title}</h1>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-[#0F172A]">All Boards</h2>
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

          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#CBD5E1] bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors">
              <SlidersHorizontal size={14} />
              Filters
            </button>
            <button
              onClick={() => setDialogOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0D9488] text-white text-sm font-medium hover:bg-[#0F766E] transition-colors"
            >
              <Plus size={14} />
              New Board
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 bg-white rounded-xl border border-[#E2E8F0] animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4">
            {boards.map((board) => (
              <div
                key={board.id}
                className="relative flex flex-col items-start p-5 h-36 bg-white rounded-xl border border-[#E2E8F0] shadow-sm hover:shadow-md hover:border-[#0D9488]/30 transition-all cursor-pointer"
                onClick={() => navigate(boardHref(board.id))}
              >
                <p className="font-semibold text-[#0F172A] text-sm pr-6">{board.title}</p>
                <p className="flex-1 mt-2 text-xs text-[#94A3B8] line-clamp-2">
                  {board.description || "No description"}
                </p>
                <p className="text-xs text-[#94A3B8] mt-auto pt-2">
                  {board.column_count} columns · Updated {relativeTime(board.updated_at)}
                </p>

                {/* Three-dot menu */}
                <div
                  className="absolute top-3 right-3"
                  onClick={(e) => e.stopPropagation()}
                >
                  <DropdownMenu>
                    <DropdownMenuTrigger className="p-1 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
                      <MoreVertical size={14} />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => setEditingBoard(board)}>
                        <Pencil size={13} className="mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => deleteBoard(board.id)}
                        className="text-red-600 focus:text-red-600"
                      >
                        <Trash2 size={13} className="mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <CreateBoardDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        workspaceId={workspaceId}
      />
      <EditBoardDialog
        board={editingBoard}
        onClose={() => setEditingBoard(null)}
      />
    </div>
  )
}

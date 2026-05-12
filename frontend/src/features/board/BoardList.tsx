import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Plus, LayoutGrid } from "lucide-react"
import { Toolbar } from "@/components/layout/Toolbar"
import { CreateBoardDialog } from "./components/CreateBoardDialog"

const MOCK_BOARDS = [
  { id: "1", title: "Content Marketing Pipeline", column_count: 5, updated_at: "2 hours ago" },
  { id: "2", title: "Feature Roadmap Q4", column_count: 4, updated_at: "Yesterday" },
  { id: "3", title: "Design System", column_count: 3, updated_at: "3 days ago" },
]

export function BoardList() {
  const navigate = useNavigate()
  const [dialogOpen, setDialogOpen] = useState(false)

  return (
    <div className="flex flex-col h-full">
      <Toolbar title="My Boards" />
      <div className="flex-1 overflow-y-auto p-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[#0F172A]">All Boards</h2>
          <button
            onClick={() => setDialogOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0D9488] text-white text-sm font-medium hover:bg-[#0F766E] transition-colors"
          >
            <Plus size={14} />
            New Board
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {MOCK_BOARDS.map((board) => (
            <button
              key={board.id}
              onClick={() => navigate(`/boards/${board.id}`)}
              className="flex flex-col items-start gap-3 p-5 bg-white rounded-xl border border-[#E2E8F0] shadow-sm hover:shadow-md hover:border-[#0D9488]/30 transition-all text-left"
            >
              <div className="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center">
                <LayoutGrid size={20} className="text-[#0D9488]" />
              </div>
              <div>
                <p className="font-semibold text-[#0F172A] text-sm mb-1">{board.title}</p>
                <p className="text-xs text-[#94A3B8]">{board.column_count} columns · Updated {board.updated_at}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <CreateBoardDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  )
}

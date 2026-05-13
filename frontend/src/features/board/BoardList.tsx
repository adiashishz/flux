import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Plus, LayoutGrid, SlidersHorizontal, Kanban, List, Calendar } from "lucide-react"
import { Toolbar } from "@/components/layout/Toolbar"
import { CreateBoardDialog } from "./components/CreateBoardDialog"
import { cn } from "@/lib/utils"

const MOCK_BOARDS = [
  { id: "1", title: "Content Marketing Pipeline", column_count: 5, updated_at: "2 hours ago" },
  { id: "2", title: "Feature Roadmap Q4", column_count: 4, updated_at: "Yesterday" },
  { id: "3", title: "Design System", column_count: 3, updated_at: "3 days ago" },
]

const VIEWS = [
  { label: "Kanban", icon: Kanban },
  { label: "List", icon: List },
  { label: "Calendar", icon: Calendar },
] as const

export function BoardList() {
  const navigate = useNavigate()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [activeView, setActiveView] = useState<string>("Kanban")

  return (
    <div className="flex flex-col h-full bg-[#E2E8F0]">
      <Toolbar title="My Boards" />
      <div className="flex-1 overflow-y-auto p-8">
        <div className="flex items-center justify-between mb-6">
          {/* Left: title + view tabs */}
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

          {/* Right: filters + new card + new board */}
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#CBD5E1] bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors">
              <SlidersHorizontal size={14} />
              Filters
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#CBD5E1] bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors">
              <Plus size={14} />
              New Card
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

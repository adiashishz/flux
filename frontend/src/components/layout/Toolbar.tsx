import { SlidersHorizontal, Plus, PanelLeftOpen } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"

const VIEWS = ["Kanban", "List", "Calendar"] as const

export function Toolbar({ title = "My Board" }: { title?: string }) {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const [activeView, setActiveView] = useState<string>("Kanban")

  return (
    <header className="flex items-center h-16 px-6 bg-white border-b border-[#E2E8F0] shrink-0 gap-4">
      {/* Sidebar toggle */}
      <button
        onClick={toggleSidebar}
        className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
      >
        <PanelLeftOpen size={18} />
      </button>

      {/* Board title */}
      <h1 className="text-base font-semibold text-[#0F172A] mr-2 truncate">{title}</h1>

      {/* View tabs */}
      <div className="flex items-center gap-1 bg-slate-100 rounded-md p-1">
        {VIEWS.map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={cn(
              "px-3 py-1 rounded text-sm font-medium transition-colors",
              activeView === view
                ? "bg-white text-[#0F172A] shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            {view}
          </button>
        ))}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 ml-auto">
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E2E8F0] text-sm text-slate-600 hover:bg-slate-50 transition-colors">
          <SlidersHorizontal size={14} />
          Filters
        </button>
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0D9488] text-white text-sm font-medium hover:bg-[#0F766E] transition-colors">
          <Plus size={14} />
          New Card
        </button>
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-orange-50 border-2 border-orange-200 flex items-center justify-center ml-1">
          <span className="text-xs font-semibold text-orange-600">A</span>
        </div>
      </div>
    </header>
  )
}

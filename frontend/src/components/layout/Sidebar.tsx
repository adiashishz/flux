import { Kanban, ChevronDown, Hash, Search, ChevronRight, ChevronsLeft } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"

const MOCK_BOARDS = ["Content Marketing Pipeline", "Feature Roadmap Q4", "Design System"]
const MOCK_TAGS = ["marketing", "launch", "analysis", "research", "workflows"]

export function Sidebar() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const [workspacesOpen, setWorkspacesOpen] = useState(true)

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-[#0F172A] text-slate-300 shrink-0 transition-all duration-300 overflow-hidden",
        sidebarOpen ? "w-64" : "w-0"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center shrink-0">
          <span className="text-white font-bold text-sm">F</span>
        </div>
        <span className="text-white font-semibold text-base tracking-tight">Flux</span>
        <button
          onClick={toggleSidebar}
          className="ml-auto p-1 rounded-md text-slate-500 hover:text-slate-300 hover:bg-slate-700/50 transition-colors"
          title="Collapse sidebar"
        >
          <ChevronsLeft size={16} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 px-3 py-2">
        <NavItem icon={<Kanban size={16} />} label="My Boards" active />
      </nav>

      {/* Workspaces */}
      <div className="px-3 flex-1 overflow-y-auto">
        <button
          onClick={() => setWorkspacesOpen((o) => !o)}
          className="flex items-center justify-between w-full px-2 py-1.5 mb-1 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-300 transition-colors"
        >
          <span>Workspaces</span>
          {workspacesOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        </button>

        {workspacesOpen && (
          <div className="flex flex-col gap-0.5">
            {MOCK_BOARDS.map((name) => (
              <button
                key={name}
                className="flex items-center gap-2 w-full px-2 py-1.5 rounded-md text-sm text-slate-400 hover:bg-[#334155] hover:text-white transition-colors text-left"
              >
                <div className="w-2 h-2 rounded-sm bg-teal-500 shrink-0" />
                <span className="truncate">{name}</span>
              </button>
            ))}
          </div>
        )}

        {/* Tags */}
        <div className="mt-5">
          <p className="px-2 mb-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">Tags</p>
          <div className="flex flex-col gap-0.5">
            {MOCK_TAGS.map((tag) => (
              <button
                key={tag}
                className="flex items-center gap-2 w-full px-2 py-1.5 rounded-md text-sm text-slate-400 hover:bg-[#334155] hover:text-white transition-colors text-left"
              >
                <Hash size={13} className="shrink-0 text-slate-500" />
                <span>{tag}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Search */}
      <div className="px-3 py-4 border-t border-slate-700">
        <button className="flex items-center gap-2 w-full px-3 py-2 rounded-md bg-slate-700/50 text-slate-400 text-sm hover:bg-slate-700 hover:text-white transition-colors">
          <Search size={14} />
          <span>Quick search…</span>
          <span className="ml-auto text-xs text-slate-600">⌘K</span>
        </button>
      </div>
    </aside>
  )
}

function NavItem({ icon, label, active }: { icon: React.ReactNode; label: string; active?: boolean }) {
  return (
    <button
      className={cn(
        "flex items-center gap-2.5 w-full px-3 py-2 rounded-md text-sm transition-colors text-left",
        active
          ? "bg-teal-600/20 text-teal-400 font-medium"
          : "text-slate-400 hover:bg-[#334155] hover:text-white"
      )}
    >
      {icon}
      {label}
    </button>
  )
}

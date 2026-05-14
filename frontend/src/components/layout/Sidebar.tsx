import { Kanban, ChevronDown, Search, ChevronRight, ChevronsLeft, Plus } from "lucide-react"
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"
import { useWorkspaces } from "@/hooks/queries/useWorkspaces"
import { CreateWorkspaceDialog } from "@/features/workspace/components/CreateWorkspaceDialog"

export function Sidebar() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const [workspacesOpen, setWorkspacesOpen] = useState(true)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const navigate = useNavigate()
  const { data: workspaces } = useWorkspaces()

  return (
    <>
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
          <NavItem
            icon={<Kanban size={16} />}
            label="My Boards"
            onClick={() => navigate("/boards")}
          />
        </nav>

        {/* Workspaces */}
        <div className="px-3 flex-1 overflow-y-auto">
          <div className="flex items-center justify-between w-full px-2 py-1.5 mb-1">
            <button
              onClick={() => setWorkspacesOpen((o) => !o)}
              className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider hover:text-slate-300 transition-colors"
            >
              {workspacesOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
              <span>Workspaces</span>
            </button>
            <button
              onClick={() => setCreateDialogOpen(true)}
              className="p-0.5 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-700/50 transition-colors"
              title="New workspace"
            >
              <Plus size={13} />
            </button>
          </div>

          {workspacesOpen && (
            <div className="flex flex-col gap-0.5">
              {(workspaces ?? []).map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => navigate(`/workspaces/${ws.id}`)}
                  className="flex items-center gap-2 w-full px-2 py-1.5 rounded-md text-sm text-slate-400 hover:bg-[#334155] hover:text-white transition-colors text-left"
                >
                  <div className="w-2 h-2 rounded-sm bg-teal-500 shrink-0" />
                  <span className="truncate">{ws.title}</span>
                </button>
              ))}
            </div>
          )}
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

      <CreateWorkspaceDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
      />
    </>
  )
}

function NavItem({
  icon,
  label,
  onClick,
  active,
}: {
  icon: React.ReactNode
  label: string
  onClick?: () => void
  active?: boolean
}) {
  return (
    <button
      onClick={onClick}
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

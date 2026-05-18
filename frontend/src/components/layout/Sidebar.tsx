import { Kanban, ChevronDown, ChevronRight, ChevronsLeft, Plus, MoreVertical, Pencil, Trash2 } from "lucide-react"
import { useState, useRef } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"
import { useWorkspaces, useUpdateWorkspace, useDeleteWorkspace } from "@/hooks/queries/useWorkspaces"
import { CreateWorkspaceDialog } from "@/features/workspace/components/CreateWorkspaceDialog"

export function Sidebar() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)
  const [workspacesOpen, setWorkspacesOpen] = useState(true)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState("")
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const renameInputRef = useRef<HTMLInputElement>(null)
  const committingRef = useRef(false)
  const savedRenameValue = useRef("")
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { data: workspaces } = useWorkspaces()
  const { mutate: updateWorkspace } = useUpdateWorkspace()
  const { mutate: deleteWorkspace } = useDeleteWorkspace()

  function startRename(id: string, currentTitle: string) {
    committingRef.current = false
    savedRenameValue.current = currentTitle
    setRenamingId(id)
    setRenameValue(currentTitle)
    setTimeout(() => renameInputRef.current?.select(), 0)
  }

  function commitRename() {
    if (committingRef.current) return
    committingRef.current = true
    const trimmed = renameValue.trim()
    if (trimmed && renamingId && trimmed !== savedRenameValue.current) {
      updateWorkspace({ id: renamingId, data: { title: trimmed } })
    }
    setRenamingId(null)
  }

  function handleRenameKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") commitRename()
    if (e.key === "Escape") { committingRef.current = true; setRenamingId(null) }
  }

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
          <img src="/Flux_transparent.png" alt="Flux" className="w-8 h-8 rounded-lg shrink-0" />
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
            active={pathname === "/boards" || pathname.startsWith("/boards/")}
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
                <div key={ws.id}>
                  <div
                    className={cn(
                      "group flex items-center gap-2 w-full px-2 py-1.5 rounded-md text-sm transition-colors",
                      pathname.startsWith(`/workspaces/${ws.id}`)
                        ? "bg-teal-600/20 text-teal-400 font-medium"
                        : "text-slate-400 hover:bg-[#334155] hover:text-white"
                    )}
                  >
                    <div className="w-2 h-2 rounded-sm bg-teal-500 shrink-0" />
                    {renamingId === ws.id ? (
                      <input
                        ref={renameInputRef}
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onBlur={commitRename}
                        onKeyDown={handleRenameKeyDown}
                        className="flex-1 min-w-0 bg-slate-700 text-white text-sm rounded px-1 outline-none"
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span
                        className="flex-1 truncate cursor-pointer"
                        onClick={() => navigate(`/workspaces/${ws.id}`)}
                      >
                        {ws.title}
                      </span>
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); setOpenMenuId(openMenuId === ws.id ? null : ws.id) }}
                      className="shrink-0 p-0.5 rounded text-slate-600 hover:text-slate-300 hover:bg-slate-600/50 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <MoreVertical size={13} />
                    </button>
                  </div>
                  {openMenuId === ws.id && (
                    <div className="ml-4 mt-0.5 mb-1 rounded-md overflow-hidden border border-slate-700">
                      <button
                        onClick={() => { setOpenMenuId(null); startRename(ws.id, ws.title) }}
                        className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 transition-colors"
                      >
                        <Pencil size={11} />
                        Rename
                      </button>
                      <button
                        onClick={() => {
                          setOpenMenuId(null)
                          deleteWorkspace(ws.id, {
                            onSuccess: () => {
                              if (pathname.startsWith(`/workspaces/${ws.id}`)) navigate("/boards")
                            },
                          })
                        }}
                        className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-red-400 hover:bg-slate-700 transition-colors"
                      >
                        <Trash2 size={11} />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
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

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Plus, FolderOpen, SlidersHorizontal } from "lucide-react"
import { CreateWorkspaceDialog } from "./components/CreateWorkspaceDialog"
import { useWorkspaces } from "@/hooks/queries/useWorkspaces"
import relativeTime from "@/utils/relativeTime"
import { usePageTitle } from "@/hooks/usePageTitle"

export function WorkspaceList() {
  const navigate = useNavigate()
  const [dialogOpen, setDialogOpen] = useState(false)
  const { data: workspaces, isLoading } = useWorkspaces()
  usePageTitle("Workspaces")

  return (
    <div className="flex flex-col h-full bg-[#E2E8F0]">
      <div className="flex-1 overflow-y-auto p-8">
        <h1 className="text-xl font-bold text-[#0F172A] mb-5">Workspaces</h1>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-[#0F172A]">All Workspaces</h2>
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
              New Workspace
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
          <div className="grid grid-cols-3 gap-4">
            {(workspaces ?? []).map((ws) => (
              <button
                key={ws.id}
                onClick={() => navigate(`/workspaces/${ws.id}`)}
                className="flex flex-col items-start gap-3 p-5 bg-white rounded-xl border border-[#E2E8F0] shadow-sm hover:shadow-md hover:border-[#0D9488]/30 transition-all text-left"
              >
                <div className="w-10 h-10 rounded-lg bg-teal-50 flex items-center justify-center">
                  <FolderOpen size={20} className="text-[#0D9488]" />
                </div>
                <div>
                  <p className="font-semibold text-[#0F172A] text-sm mb-1">{ws.title}</p>
                  <p className="text-xs text-[#94A3B8]">
                    {ws.board_count} boards · Updated {relativeTime(ws.updated_at)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <CreateWorkspaceDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  )
}

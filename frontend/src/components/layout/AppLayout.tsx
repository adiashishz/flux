import { Outlet } from "react-router-dom"
import { ChevronsRight } from "lucide-react"
import { Sidebar } from "./Sidebar"
import { EditorPanel } from "@/features/editor/EditorPanel"
import { SearchDialog } from "@/features/search/SearchDialog"
import { useUIStore } from "@/store/ui"

export function AppLayout() {
  const editorOpen = useUIStore((s) => s.editorPanelOpen)
  const closeEditor = useUIStore((s) => s.closeEditor)
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)

  return (
    <div className="flex h-screen overflow-hidden bg-[#F8FAFC]">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 relative">
        {!sidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="absolute top-4 left-4 z-10 p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title="Expand sidebar"
          >
            <ChevronsRight size={16} />
          </button>
        )}
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
      {editorOpen && (
        <div className="fixed inset-0 z-10" onClick={closeEditor} />
      )}
      <EditorPanel />
      <SearchDialog />
    </div>
  )
}

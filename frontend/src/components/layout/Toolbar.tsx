import { ChevronsRight } from "lucide-react"
import { useUIStore } from "@/store/ui"

export function Toolbar({ title = "My Board" }: { title?: string }) {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen)
  const toggleSidebar = useUIStore((s) => s.toggleSidebar)

  return (
    <header className="flex items-center h-14 px-6 bg-white border-b border-[#E2E8F0] shrink-0 gap-3">
      {/* Expand button — only visible when sidebar is collapsed */}
      {!sidebarOpen && (
        <button
          onClick={toggleSidebar}
          className="p-1 rounded-md text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          title="Expand sidebar"
        >
          <ChevronsRight size={16} />
        </button>
      )}

      <h1 className="text-base font-semibold text-[#0F172A] truncate">{title}</h1>

      {/* Avatar */}
      <div className="ml-auto w-8 h-8 rounded-full bg-orange-50 border-2 border-orange-200 flex items-center justify-center">
        <span className="text-xs font-semibold text-orange-600">A</span>
      </div>
    </header>
  )
}

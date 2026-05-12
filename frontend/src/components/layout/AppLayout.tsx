import { Outlet } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { EditorPanel } from "@/features/editor/EditorPanel"

export function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-[#F8FAFC]">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
      <EditorPanel />
    </div>
  )
}

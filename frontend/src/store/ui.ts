import { create } from "zustand"

interface UIState {
  selectedCardId: string | null
  editorPanelOpen: boolean
  sidebarOpen: boolean
  setSelectedCard: (id: string | null) => void
  openEditor: () => void
  closeEditor: () => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  selectedCardId: null,
  editorPanelOpen: false,
  sidebarOpen: true,
  setSelectedCard: (id) => set({ selectedCardId: id }),
  openEditor: () => set({ editorPanelOpen: true }),
  closeEditor: () => set({ editorPanelOpen: false, selectedCardId: null }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))

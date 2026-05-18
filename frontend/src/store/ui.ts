import { create } from "zustand"

interface UIState {
  selectedCardId: string | null
  editorPanelOpen: boolean
  editorExpanded: boolean
  sidebarOpen: boolean
  setSelectedCard: (id: string | null) => void
  openEditor: () => void
  closeEditor: () => void
  toggleEditorExpanded: () => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  selectedCardId: null,
  editorPanelOpen: false,
  editorExpanded: false,
  sidebarOpen: true,
  setSelectedCard: (id) => set({ selectedCardId: id }),
  openEditor: () => set({ editorPanelOpen: true }),
  closeEditor: () => set({ editorPanelOpen: false, selectedCardId: null, editorExpanded: false }),
  toggleEditorExpanded: () => set((s) => ({ editorExpanded: !s.editorExpanded })),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))

import { create } from "zustand"

interface UIState {
  selectedCardId: string | null
  editorPanelOpen: boolean
  editorExpanded: boolean
  sidebarOpen: boolean
  searchOpen: boolean
  aiPanelOpen: boolean
  isDragging: boolean
  setSelectedCard: (id: string | null) => void
  openEditor: () => void
  closeEditor: () => void
  toggleEditorExpanded: () => void
  toggleSidebar: () => void
  setSearchOpen: (open: boolean) => void
  setAiPanelOpen: (open: boolean) => void
  setDragging: (dragging: boolean) => void
}

export const useUIStore = create<UIState>((set) => ({
  selectedCardId: null,
  editorPanelOpen: false,
  editorExpanded: false,
  sidebarOpen: true,
  searchOpen: false,
  aiPanelOpen: false,
  isDragging: false,
  setSelectedCard: (id) => set({ selectedCardId: id }),
  openEditor: () => set({ editorPanelOpen: true, aiPanelOpen: false }),
  closeEditor: () => set({ editorPanelOpen: false, selectedCardId: null, editorExpanded: false }),
  toggleEditorExpanded: () => set((s) => ({ editorExpanded: !s.editorExpanded })),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSearchOpen: (open) => set({ searchOpen: open }),
  setAiPanelOpen: (open) => set(open ? { aiPanelOpen: true, editorPanelOpen: false, editorExpanded: false } : { aiPanelOpen: false }),
  setDragging: (dragging) => set({ isDragging: dragging }),
}))

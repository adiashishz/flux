export interface Workspace {
  id: string
  title: string
  created_at: string
  updated_at: string
  board_count: number
}

export interface WorkspaceDetail extends Workspace {
  boards: Board[]
}

export interface Board {
  id: string
  title: string
  description?: string
  workspace_id: string | null
  created_at: string
  updated_at: string
  column_count: number
}

export interface Card {
  id: string
  column_id: string
  title: string
  description?: string
  content_preview: string
  position: number
  created_at: string
  updated_at: string
}

export interface CardDetail extends Card {
  content_markdown: string
  column_title: string
}

export interface Column {
  id: string
  board_id: string
  title: string
  position: number
  card_count: number
  cards: Card[]
}

export interface BoardDetail extends Board {
  columns: Column[]
}

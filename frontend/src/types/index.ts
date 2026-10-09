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
  position: number
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

export interface SearchResult {
  id: string
  title: string
  content_preview: string
  column_id: string
  column_title: string
  board_id: string
  board_title: string
  score: number
}

export interface ChatTurn {
  role: "user" | "assistant"
  content: string
}

export type ChatEvent =
  | { type: "text"; text: string }
  | { type: "tool_call"; id: string; name: string; input: Record<string, unknown> }
  | { type: "tool_result"; id: string; name: string; ok: boolean; result: Record<string, unknown> }
  | { type: "confirmation_required"; action: "delete_card"; card_id: string; title: string; board_id: string }
  | { type: "done"; stop_reason: string | null; iterations: number; usage: { input_tokens: number; output_tokens: number } }
  | { type: "error"; message: string }

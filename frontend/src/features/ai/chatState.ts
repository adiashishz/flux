import type { ChatEvent, ChatTurn } from "@/types"

export interface ToolActivity {
  id: string
  name: string
  input: Record<string, unknown>
  status: "running" | "ok" | "error"
  result?: Record<string, unknown>
}

export interface PendingDelete {
  cardId: string
  title: string
  boardId: string
  state: "pending" | "deleting" | "deleted" | "cancelled" | "failed"
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  tools: ToolActivity[]
  confirmations: PendingDelete[]
  error?: string
}

const MAX_TURNS = 20

export function newMessage(role: ChatMessage["role"], content = ""): ChatMessage {
  return { id: crypto.randomUUID(), role, content, tools: [], confirmations: [] }
}

export function applyEvent(message: ChatMessage, event: ChatEvent): ChatMessage {
  switch (event.type) {
    case "text":
      return { ...message, content: message.content + event.text }
    case "tool_call":
      return { ...message, tools: [...message.tools, { id: event.id, name: event.name, input: event.input, status: "running" }] }
    case "tool_result":
      return {
        ...message,
        tools: message.tools.map((tool) =>
          tool.id === event.id ? { ...tool, status: event.ok ? "ok" : "error", result: event.result } : tool
        ),
      }
    case "confirmation_required":
      return {
        ...message,
        confirmations: [
          ...message.confirmations,
          { cardId: event.card_id, title: event.title, boardId: event.board_id, state: "pending" },
        ],
      }
    case "error":
      return { ...message, error: event.message }
    default:
      return message
  }
}

export function setConfirmationState(
  message: ChatMessage,
  cardId: string,
  state: PendingDelete["state"]
): ChatMessage {
  return {
    ...message,
    confirmations: message.confirmations.map((item) => (item.cardId === cardId ? { ...item, state } : item)),
  }
}

/** The server is stateless: send the text turns only, newest 20, starting on a user turn. */
export function toTurns(messages: ChatMessage[]): ChatTurn[] {
  const turns = messages
    .filter((message) => message.content.trim())
    .map((message) => ({ role: message.role, content: message.content }))
    .slice(-MAX_TURNS)
  while (turns.length && turns[0].role !== "user") turns.shift()
  return turns
}

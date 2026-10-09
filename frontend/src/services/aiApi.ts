import { api } from "./api"
import type { ChatEvent, ChatTurn, SearchResult } from "@/types"
import { createSSEParser } from "@/utils/sse"

export const semanticSearch = (q: string) =>
  api.get<SearchResult[]>(`/ai/search/`, { params: { q } }).then(r => r.data)

export async function streamChat({
  messages,
  boardId,
  signal,
  onEvent,
}: {
  messages: ChatTurn[]
  boardId?: string
  signal: AbortSignal
  onEvent: (event: ChatEvent) => void
}) {
  const response = await fetch(`${api.defaults.baseURL}ai/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, board_id: boardId }),
    signal,
  })

  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `The assistant request failed (${response.status}).`)
  }

  const feed = createSSEParser((message) => onEvent(JSON.parse(message.data) as ChatEvent))
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    feed(decoder.decode(value, { stream: true }))
  }
}

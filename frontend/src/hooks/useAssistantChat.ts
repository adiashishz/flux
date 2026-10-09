import { useCallback, useRef, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import * as aiApi from "@/services/aiApi"
import * as cardsApi from "@/services/cardsApi"
import { boardKeys } from "@/hooks/queries/useBoards"
import { cardKeys } from "@/hooks/queries/useCards"
import { useUIStore } from "@/store/ui"
import {
  applyEvent,
  newMessage,
  setConfirmationState,
  toTurns,
  type ChatMessage,
  type PendingDelete,
} from "@/features/ai/chatState"
import type { ChatEvent } from "@/types"

const MUTATING_TOOLS = new Set(["create_card", "update_card", "move_card"])
const INVALIDATION_RETRY_MS = 300
const INVALIDATION_MAX_TRIES = 20

export function useAssistantChat(boardId?: string) {
  const qc = useQueryClient()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const messagesRef = useRef<ChatMessage[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const update = useCallback((updater: (current: ChatMessage[]) => ChatMessage[]) => {
    messagesRef.current = updater(messagesRef.current)
    setMessages(messagesRef.current)
  }, [])

  // The board view mutates its own cache while a card is dragged, so wait for the drop first.
  const refreshAfterTool = useCallback(
    (event: Extract<ChatEvent, { type: "tool_result" }>, tries = 0) => {
      if (!event.ok || !MUTATING_TOOLS.has(event.name)) return
      if (useUIStore.getState().isDragging && tries < INVALIDATION_MAX_TRIES) {
        setTimeout(() => refreshAfterTool(event, tries + 1), INVALIDATION_RETRY_MS)
        return
      }
      const result = event.result as { board_id?: string; card_id?: string }
      if (result.board_id) qc.invalidateQueries({ queryKey: boardKeys.detail(result.board_id) })
      if (result.card_id) qc.invalidateQueries({ queryKey: cardKeys.detail(result.card_id) })
    },
    [qc]
  )

  const send = useCallback(
    async (text: string) => {
      const content = text.trim()
      if (!content || abortRef.current) return

      const userMessage = newMessage("user", content)
      const assistantMessage = newMessage("assistant")
      const turns = toTurns([...messagesRef.current, userMessage])
      update((current) => [...current, userMessage, assistantMessage])

      const controller = new AbortController()
      abortRef.current = controller
      setStreaming(true)

      const patch = (change: (message: ChatMessage) => ChatMessage) =>
        update((current) => current.map((m) => (m.id === assistantMessage.id ? change(m) : m)))

      try {
        await aiApi.streamChat({
          messages: turns,
          boardId,
          signal: controller.signal,
          onEvent: (event) => {
            patch((message) => applyEvent(message, event))
            if (event.type === "tool_result") refreshAfterTool(event)
          },
        })
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          patch((message) => ({ ...message, error: (error as Error).message }))
        }
      } finally {
        abortRef.current = null
        setStreaming(false)
      }
    },
    [boardId, refreshAfterTool, update]
  )

  const stop = useCallback(() => abortRef.current?.abort(), [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    update(() => [])
  }, [update])

  const setConfirmation = useCallback(
    (messageId: string, cardId: string, state: PendingDelete["state"]) =>
      update((current) => current.map((m) => (m.id === messageId ? setConfirmationState(m, cardId, state) : m))),
    [update]
  )

  const confirmDelete = useCallback(
    async (messageId: string, confirmation: PendingDelete) => {
      setConfirmation(messageId, confirmation.cardId, "deleting")
      try {
        await cardsApi.deleteCard(confirmation.cardId)
        qc.invalidateQueries({ queryKey: boardKeys.detail(confirmation.boardId) })
        qc.removeQueries({ queryKey: cardKeys.detail(confirmation.cardId) })
        setConfirmation(messageId, confirmation.cardId, "deleted")
      } catch {
        setConfirmation(messageId, confirmation.cardId, "failed")
      }
    },
    [qc, setConfirmation]
  )

  const cancelDelete = useCallback(
    (messageId: string, confirmation: PendingDelete) => setConfirmation(messageId, confirmation.cardId, "cancelled"),
    [setConfirmation]
  )

  return { messages, streaming, send, stop, reset, confirmDelete, cancelDelete }
}

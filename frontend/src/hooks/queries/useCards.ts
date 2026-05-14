import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import * as cardsApi from "@/services/cardsApi"
import { boardKeys } from "./useBoards"
import type { CardDetail, BoardDetail } from "@/types"

export const cardKeys = {
  detail: (id: string) => ["cards", id] as const,
}

export function useCard(id: string | null) {
  return useQuery({
    queryKey: cardKeys.detail(id ?? ""),
    queryFn: () => cardsApi.getCard(id!),
    enabled: !!id,
  })
}

export function useCreateCard(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ columnId, title }: { columnId: string; title: string }) =>
      cardsApi.createCard(columnId, title),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) }),
  })
}

export function useUpdateCard(boardId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Pick<CardDetail, "title" | "description" | "content_markdown" | "content_preview">> }) =>
      cardsApi.updateCard(id, data),
    onSuccess: (updatedCard, { id }) => {
      qc.setQueryData(cardKeys.detail(id), updatedCard)
      if (boardId) {
        qc.setQueryData<BoardDetail>(boardKeys.detail(boardId), (old) => {
          if (!old) return old
          return {
            ...old,
            columns: old.columns.map(col => ({
              ...col,
              cards: col.cards.map(c =>
                c.id === id ? { ...c, ...updatedCard } : c
              ),
            })),
          }
        })
      }
    },
  })
}

export function useDeleteCard(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => cardsApi.deleteCard(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) }),
  })
}

export function useMoveCard(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { source_column_id: string; destination_column_id: string; destination_index: number } }) =>
      cardsApi.moveCard(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) }),
  })
}

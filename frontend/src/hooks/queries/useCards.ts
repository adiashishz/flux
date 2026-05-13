import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import * as cardsApi from "@/services/cardsApi"
import { boardKeys } from "./useBoards"
import type { CardDetail } from "@/types"

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

export function useUpdateCard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Pick<CardDetail, "title" | "content_markdown" | "content_preview">> }) =>
      cardsApi.updateCard(id, data),
    onSuccess: (_, { id }) => qc.invalidateQueries({ queryKey: cardKeys.detail(id) }),
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

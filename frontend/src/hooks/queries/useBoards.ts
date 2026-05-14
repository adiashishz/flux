import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import * as boardsApi from "@/services/boardsApi"
import { workspaceKeys } from "./useWorkspaces"

export const boardKeys = {
  all: ["boards"] as const,
  detail: (id: string) => ["boards", id, "detail"] as const,
}

export function useBoards() {
  return useQuery({ queryKey: boardKeys.all, queryFn: boardsApi.getBoards })
}

export function useBoard(id: string) {
  return useQuery({
    queryKey: boardKeys.detail(id),
    queryFn: () => boardsApi.getBoardDetail(id),
    enabled: !!id,
  })
}

export function useCreatePersonalBoard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { title: string; description?: string }) => boardsApi.createBoard(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.all }),
  })
}

export function useUpdateBoard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string; description?: string } }) =>
      boardsApi.updateBoard(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.all }),
  })
}

export function useDeleteBoard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => boardsApi.deleteBoard(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.all }),
  })
}

export function useCreateColumn(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (title: string) => boardsApi.createColumn(boardId, title),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) }),
  })
}

export function useUpdateColumn(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string } }) =>
      boardsApi.updateColumn(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) })
      qc.invalidateQueries({ queryKey: ["cards"] })
    },
  })
}

export function useDeleteColumn(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => boardsApi.deleteColumn(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) }),
  })
}

export function useMoveColumn(boardId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { board_id: string; destination_index: number } }) =>
      boardsApi.moveColumn(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: boardKeys.detail(boardId) }),
  })
}

export function useMoveBoard(workspaceId?: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { destination_index: number } }) =>
      boardsApi.moveBoard(id, payload),
    onSuccess: () => {
      if (workspaceId) {
        qc.invalidateQueries({ queryKey: workspaceKeys.detail(workspaceId) })
      } else {
        qc.invalidateQueries({ queryKey: boardKeys.all })
      }
    },
  })
}

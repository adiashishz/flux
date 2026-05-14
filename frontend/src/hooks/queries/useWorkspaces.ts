import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import * as workspacesApi from "@/services/workspacesApi"
import { boardKeys } from "./useBoards"

export const workspaceKeys = {
  all: ["workspaces"] as const,
  detail: (id: string) => ["workspaces", id, "detail"] as const,
}

export function useWorkspaces() {
  return useQuery({ queryKey: workspaceKeys.all, queryFn: workspacesApi.getWorkspaces })
}

export function useWorkspace(id: string | undefined) {
  return useQuery({
    queryKey: workspaceKeys.detail(id ?? ""),
    queryFn: () => workspacesApi.getWorkspaceDetail(id!),
    enabled: !!id,
  })
}

export function useCreateWorkspace() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (title: string) => workspacesApi.createWorkspace(title),
    onSuccess: () => qc.invalidateQueries({ queryKey: workspaceKeys.all }),
  })
}

export function useUpdateWorkspace() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { title?: string } }) =>
      workspacesApi.updateWorkspace(id, data),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: workspaceKeys.all })
      qc.invalidateQueries({ queryKey: workspaceKeys.detail(id) })
    },
  })
}

export function useDeleteWorkspace() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => workspacesApi.deleteWorkspace(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: workspaceKeys.all }),
  })
}

export function useCreateBoard(workspaceId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (title: string) => workspacesApi.createBoard(workspaceId, title),
    onSuccess: () => qc.invalidateQueries({ queryKey: workspaceKeys.detail(workspaceId) }),
  })
}

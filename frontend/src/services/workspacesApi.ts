import { api } from "./api"
import type { Workspace, WorkspaceDetail, Board } from "@/types"

export const getWorkspaces = () =>
  api.get<Workspace[]>("/workspaces/").then(r => r.data)

export const createWorkspace = (title: string) =>
  api.post<Workspace>("/workspaces/", { title }).then(r => r.data)

export const updateWorkspace = (id: string, data: Partial<Pick<Workspace, "title">>) =>
  api.patch<Workspace>(`/workspaces/${id}/`, data).then(r => r.data)

export const deleteWorkspace = (id: string) =>
  api.delete(`/workspaces/${id}/`).then(r => r.data)

export const getWorkspaceDetail = (id: string) =>
  api.get<WorkspaceDetail>(`/workspaces/${id}/`).then(r => r.data)

export const createBoard = (workspaceId: string, data: { title: string; description?: string }) =>
  api.post<Board>(`/workspaces/${workspaceId}/boards/`, data).then(r => r.data)

import { api } from "./api"
import type { Board, BoardDetail } from "@/types"

export const getBoards = () =>
  api.get<Board[]>("/boards/").then(r => r.data)

export const createBoard = (title: string) =>
  api.post<Board>("/boards/", { title }).then(r => r.data)

export const updateBoard = (id: string, data: Partial<Pick<Board, "title">>) =>
  api.patch<Board>(`/boards/${id}/`, data).then(r => r.data)

export const deleteBoard = (id: string) =>
  api.delete(`/boards/${id}/`).then(r => r.data)

export const getBoardDetail = (id: string) =>
  api.get<BoardDetail>(`/boards/${id}/detail/`).then(r => r.data)

export const createColumn = (boardId: string, title: string) =>
  api.post(`/boards/${boardId}/columns/`, { title }).then(r => r.data)

export const updateColumn = (id: string, data: { title?: string; position?: number }) =>
  api.patch(`/columns/${id}/`, data).then(r => r.data)

export const deleteColumn = (id: string) =>
  api.delete(`/columns/${id}/`).then(r => r.data)

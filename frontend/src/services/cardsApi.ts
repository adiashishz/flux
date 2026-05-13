import { api } from "./api"
import type { Card, CardDetail } from "@/types"

export const getCard = (id: string) =>
  api.get<CardDetail>(`/cards/${id}/`).then(r => r.data)

export const createCard = (columnId: string, title: string) =>
  api.post<Card>(`/columns/${columnId}/cards/`, { title }).then(r => r.data)

export const updateCard = (id: string, data: Partial<Pick<CardDetail, "title" | "content_markdown" | "content_preview">>) =>
  api.patch<CardDetail>(`/cards/${id}/`, data).then(r => r.data)

export const deleteCard = (id: string) =>
  api.delete(`/cards/${id}/`).then(r => r.data)

export const moveCard = (id: string, payload: { source_column_id: string; destination_column_id: string; destination_index: number }) =>
  api.post<Card>(`/cards/${id}/move/`, payload).then(r => r.data)

export const search = (q: string) =>
  api.get(`/search/`, { params: { q } }).then(r => r.data)

import { api } from "./api"
import type { SearchResult } from "@/types"

export const semanticSearch = (q: string) =>
  api.get<SearchResult[]>(`/ai/search/`, { params: { q } }).then(r => r.data)

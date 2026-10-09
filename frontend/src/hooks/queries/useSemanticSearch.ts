import { useQuery } from "@tanstack/react-query"
import * as aiApi from "@/services/aiApi"

export const aiKeys = {
  search: (q: string) => ["ai", "search", q] as const,
}

export function useSemanticSearch(q: string) {
  return useQuery({
    queryKey: aiKeys.search(q),
    queryFn: () => aiApi.semanticSearch(q),
    enabled: q.length >= 2,
    staleTime: 60_000,
  })
}

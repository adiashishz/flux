import { useQuery } from "@tanstack/react-query"
import * as aiApi from "@/services/aiApi"

export const aiStatusKey = ["ai", "status"] as const

export function useAiStatus(enabled: boolean) {
  return useQuery({
    queryKey: aiStatusKey,
    queryFn: aiApi.getStatus,
    enabled,
    staleTime: 30_000,
  })
}

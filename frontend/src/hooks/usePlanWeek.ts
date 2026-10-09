import { useEffect, useRef, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import axios from "axios"
import * as aiApi from "@/services/aiApi"
import { boardKeys } from "@/hooks/queries/useBoards"
import { isActive } from "@/features/ai/planState"

const POLL_MS = 2000

export const runKeys = {
  detail: (id: string) => ["ai", "runs", id] as const,
}

export function usePlanWeek(boardId?: string) {
  const qc = useQueryClient()
  const [runId, setRunId] = useState<string | null>(null)
  const refreshedRun = useRef<string | null>(null)

  const start = useMutation({
    mutationFn: (focus: string) => aiApi.startPlan(boardId!, focus),
    onSuccess: (run) => {
      qc.setQueryData(runKeys.detail(run.id), run)
      setRunId(run.id)
    },
  })

  const { data: run } = useQuery({
    queryKey: runKeys.detail(runId ?? ""),
    queryFn: () => aiApi.getRun(runId!),
    enabled: !!runId,
    staleTime: 0,
    refetchInterval: (query) => (isActive(query.state.data) ? POLL_MS : false),
  })

  // The new column and plan card only show up after the board is refetched, once per run.
  useEffect(() => {
    if (run?.status === "succeeded" && run.result && refreshedRun.current !== run.id) {
      refreshedRun.current = run.id
      qc.invalidateQueries({ queryKey: boardKeys.detail(run.result.board_id) })
    }
  }, [run, qc])

  const startError = start.error
    ? axios.isAxiosError(start.error)
      ? (start.error.response?.data?.detail ?? "Could not start the plan.")
      : "Could not start the plan."
    : null

  return {
    run,
    starting: start.isPending,
    error: startError as string | null,
    start: (focus = "") => boardId && start.mutate(focus),
    dismiss: () => {
      setRunId(null)
      start.reset()
    },
  }
}

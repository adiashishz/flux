import type { AiStatus } from "@/types"

/** Until the status arrives we assume it works, so the panel does not flash a warning. */
export function isReady(status: AiStatus | undefined): boolean {
  return status ? status.enabled && status.configured : true
}

export function statusProblem(status: AiStatus | undefined): string | null {
  if (!status || isReady(status)) return null
  if (!status.configured) return status.problem ?? "No model provider is configured."
  return "The assistant is switched off. Set AI_ENABLED=true on the server."
}

export function modelLabel(status: AiStatus | undefined): string | null {
  if (!status || !status.configured) return null
  return `${status.provider} / ${status.model}`
}

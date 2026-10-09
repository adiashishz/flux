import type { PlanItem, PlanRun } from "@/types"

export const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

const STEP_LABELS: Record<string, string> = {
  gather: "Reading open cards",
  plan: "Choosing the week",
  validate: "Checking the plan",
  repair: "Fixing problems",
  write: "Saving the plan card",
}

export function stepLabel(name: string): string {
  return STEP_LABELS[name] ?? name
}

export function groupByDay(items: PlanItem[]): { day: string; items: PlanItem[] }[] {
  return DAYS.map((day) => ({ day, items: items.filter((item) => item.day === day) })).filter((group) => group.items.length > 0)
}

export function isActive(run: PlanRun | undefined): boolean {
  return run?.status === "queued" || run?.status === "running"
}

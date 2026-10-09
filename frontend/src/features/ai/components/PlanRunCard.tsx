import { AlertTriangle, Check, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { PlanRun } from "@/types"
import { groupByDay, isActive, stepLabel } from "../planState"

interface PlanRunCardProps {
  run: PlanRun | undefined
  starting: boolean
  error: string | null
  onOpenCard: (cardId: string) => void
  onRetry: () => void
  onDismiss: () => void
}

export function PlanRunCard({ run, starting, error, onOpenCard, onRetry, onDismiss }: PlanRunCardProps) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        <p>{error}</p>
        <Button size="sm" variant="outline" className="mt-2" onClick={onDismiss}>
          Dismiss
        </Button>
      </div>
    )
  }

  if (starting && !run) {
    return (
      <p className="flex items-center gap-2 text-sm text-slate-500">
        <Loader2 size={14} className="animate-spin" /> Starting...
      </p>
    )
  }
  if (!run) return null

  const result = run.result
  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-slate-50 p-3 text-sm">
      <ul className="flex flex-col gap-1">
        {run.steps.map((step) => (
          <li key={step.name} className="flex items-center gap-2 text-slate-600">
            {step.status === "running" && <Loader2 size={12} className="animate-spin" />}
            {step.status === "done" && <Check size={12} className="text-teal-600" />}
            {step.status === "failed" && <AlertTriangle size={12} className="text-red-600" />}
            <span>{stepLabel(step.name)}</span>
            {step.detail && step.detail !== "ok" && <span className="text-xs text-slate-400">({step.detail})</span>}
          </li>
        ))}
        {isActive(run) && run.steps.length === 0 && (
          <li className="flex items-center gap-2 text-slate-500">
            <Loader2 size={12} className="animate-spin" /> Waiting for a worker...
          </li>
        )}
      </ul>

      {run.status === "failed" && (
        <div className="mt-2">
          <p className="text-red-700">{run.error_message || "The plan failed."}</p>
          <div className="mt-2 flex gap-2">
            <Button size="sm" onClick={onRetry}>
              Try again
            </Button>
            <Button size="sm" variant="outline" onClick={onDismiss}>
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {run.status === "succeeded" && result && (
        <div className="mt-3">
          <p className="text-slate-700">{result.summary}</p>
          <div className="mt-2 flex flex-col gap-1.5">
            {groupByDay(result.items).map((group) => (
              <div key={group.day}>
                <p className="text-xs font-semibold text-slate-500">{group.day}</p>
                {group.items.map((item) => (
                  <p key={item.card_id} className="text-slate-700">
                    {item.title}
                  </p>
                ))}
              </div>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <Button size="sm" onClick={() => onOpenCard(result.card_id)}>
              Open plan card
            </Button>
            <Button size="sm" variant="outline" onClick={onDismiss}>
              Dismiss
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

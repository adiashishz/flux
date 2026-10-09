import { Button } from "@/components/ui/button"
import type { PendingDelete } from "../chatState"

interface DeleteConfirmationProps {
  confirmation: PendingDelete
  onConfirm: () => void
  onCancel: () => void
}

export function DeleteConfirmation({ confirmation, onConfirm, onCancel }: DeleteConfirmationProps) {
  const { state, title } = confirmation

  if (state === "deleted") return <p className="text-xs text-slate-500">Deleted "{title}".</p>
  if (state === "cancelled") return <p className="text-xs text-slate-500">Kept "{title}".</p>

  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm">
      <p className="text-red-800">Delete "{title}"? This cannot be undone.</p>
      {state === "failed" && <p className="mt-1 text-xs text-red-700">Deleting failed. Try again.</p>}
      <div className="mt-2 flex gap-2">
        <Button size="sm" variant="destructive" disabled={state === "deleting"} onClick={onConfirm}>
          {state === "deleting" ? "Deleting..." : "Delete"}
        </Button>
        <Button size="sm" variant="outline" disabled={state === "deleting"} onClick={onCancel}>
          Keep
        </Button>
      </div>
    </div>
  )
}

import { AlertTriangle, Check, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ToolActivity } from "../chatState"

function describe(tool: ToolActivity): string {
  const title = (tool.result?.title ?? tool.input.title) as string | undefined
  switch (tool.name) {
    case "list_boards":
      return "Looked up your boards"
    case "get_board":
      return "Read a board"
    case "search_cards":
      return `Searched for "${String(tool.input.query ?? "")}"`
    case "create_card":
      return `Created "${title ?? "card"}"`
    case "update_card":
      return `Updated "${title ?? "card"}"`
    case "move_card":
      return `Moved "${title ?? "card"}"`
    case "delete_card":
      return "Asked you to confirm a deletion"
    default:
      return tool.name
  }
}

export function ToolChip({ tool }: { tool: ToolActivity }) {
  const failure = tool.status === "error" ? String(tool.result?.error ?? "Failed") : undefined
  return (
    <span
      title={failure}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs",
        tool.status === "error" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-600"
      )}
    >
      {tool.status === "running" && <Loader2 size={12} className="animate-spin" />}
      {tool.status === "ok" && <Check size={12} className="text-teal-600" />}
      {tool.status === "error" && <AlertTriangle size={12} />}
      {describe(tool)}
    </span>
  )
}

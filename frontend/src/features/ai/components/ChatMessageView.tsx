import { MarkdownPreview } from "@/features/editor/components/MarkdownPreview"
import type { ChatMessage, PendingDelete } from "../chatState"
import { DeleteConfirmation } from "./DeleteConfirmation"
import { ToolChip } from "./ToolChip"

interface ChatMessageViewProps {
  message: ChatMessage
  onConfirmDelete: (confirmation: PendingDelete) => void
  onCancelDelete: (confirmation: PendingDelete) => void
}

export function ChatMessageView({ message, onConfirmDelete, onCancelDelete }: ChatMessageViewProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-[#0F172A] px-3 py-2 text-sm text-white">
          {message.content}
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {message.tools.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {message.tools.map((tool) => (
            <ToolChip key={tool.id} tool={tool} />
          ))}
        </div>
      )}
      {message.content && <MarkdownPreview content={message.content} />}
      {message.confirmations.map((confirmation) => (
        <DeleteConfirmation
          key={confirmation.cardId}
          confirmation={confirmation}
          onConfirm={() => onConfirmDelete(confirmation)}
          onCancel={() => onCancelDelete(confirmation)}
        />
      ))}
      {message.error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{message.error}</p>}
    </div>
  )
}

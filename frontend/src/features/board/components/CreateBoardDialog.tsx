import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useCreatePersonalBoard } from "@/hooks/queries/useBoards"
import { useCreateBoard } from "@/hooks/queries/useWorkspaces"

interface CreateBoardDialogProps {
  open: boolean
  onClose: () => void
  workspaceId?: string
}

export function CreateBoardDialog({ open, onClose, workspaceId }: CreateBoardDialogProps) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const { mutate: createPersonalBoard, isPending: personalPending } = useCreatePersonalBoard()
  const { mutate: createWorkspaceBoard, isPending: workspacePending } = useCreateBoard(workspaceId ?? "")
  const isPending = personalPending || workspacePending

  function handleCreate() {
    if (!title.trim()) return
    const mutate = workspaceId ? createWorkspaceBoard : createPersonalBoard
    mutate({ title: title.trim(), description: description.trim() || undefined }, {
      onSuccess: () => {
        setTitle("")
        setDescription("")
        onClose()
      },
    })
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Board</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Board title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          autoFocus
        />
        <textarea
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none outline-none focus:ring-1 focus:ring-ring placeholder:text-muted-foreground"
        />
        <DialogFooter>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md text-sm text-[#475569] hover:bg-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={isPending || !title.trim()}
            className="px-4 py-2 rounded-md text-sm bg-[#0D9488] text-white font-medium hover:bg-[#0F766E] disabled:opacity-50 transition-colors"
          >
            {isPending ? "Creating…" : "Create"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

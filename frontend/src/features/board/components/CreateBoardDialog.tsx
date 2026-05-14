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
  const { mutate: createPersonalBoard, isPending: personalPending } = useCreatePersonalBoard()
  const { mutate: createWorkspaceBoard, isPending: workspacePending } = useCreateBoard(workspaceId ?? "")
  const isPending = personalPending || workspacePending

  function handleCreate() {
    if (!title.trim()) return
    const mutate = workspaceId ? createWorkspaceBoard : createPersonalBoard
    mutate(title.trim(), {
      onSuccess: () => {
        setTitle("")
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

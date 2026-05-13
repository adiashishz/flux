import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useCreateWorkspace } from "@/hooks/queries/useWorkspaces"

interface CreateWorkspaceDialogProps {
  open: boolean
  onClose: () => void
}

export function CreateWorkspaceDialog({ open, onClose }: CreateWorkspaceDialogProps) {
  const [title, setTitle] = useState("")
  const { mutate: createWorkspace, isPending } = useCreateWorkspace()

  function handleCreate() {
    if (!title.trim()) return
    createWorkspace(title.trim(), {
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
          <DialogTitle>New Workspace</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Workspace name"
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

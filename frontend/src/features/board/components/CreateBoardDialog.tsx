import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"

interface CreateBoardDialogProps {
  open: boolean
  onClose: () => void
}

export function CreateBoardDialog({ open, onClose }: CreateBoardDialogProps) {
  const [title, setTitle] = useState("")

  function handleCreate() {
    if (!title.trim()) return
    setTitle("")
    onClose()
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
            className="px-4 py-2 rounded-md text-sm bg-[#0D9488] text-white font-medium hover:bg-[#0F766E] transition-colors"
          >
            Create
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

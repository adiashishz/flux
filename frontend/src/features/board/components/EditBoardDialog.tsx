import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useUpdateBoard } from "@/hooks/queries/useBoards"
import type { Board } from "@/types"

interface EditBoardDialogProps {
  board: Board | null
  onClose: () => void
}

export function EditBoardDialog({ board, onClose }: EditBoardDialogProps) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const { mutate: updateBoard, isPending } = useUpdateBoard()

  useEffect(() => {
    if (board) {
      setTitle(board.title)
      setDescription(board.description ?? "")
    }
  }, [board])

  function handleSave() {
    if (!board || !title.trim()) return
    updateBoard(
      { id: board.id, data: { title: title.trim(), description: description.trim() } },
      { onSuccess: onClose }
    )
  }

  return (
    <Dialog open={!!board} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Board</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Board title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSave()}
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
            onClick={handleSave}
            disabled={isPending || !title.trim()}
            className="px-4 py-2 rounded-md text-sm bg-[#0D9488] text-white font-medium hover:bg-[#0F766E] disabled:opacity-50 transition-colors"
          >
            {isPending ? "Saving…" : "Save"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

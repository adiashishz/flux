import { useState, useEffect, useRef } from "react"
import { X, Pin, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"
import { useCard, useUpdateCard, useDeleteCard } from "@/hooks/queries/useCards"
import { useUpdateColumn } from "@/hooks/queries/useBoards"
import { useDebounce } from "@/hooks/useDebounce"
import { TipTapEditor } from "./components/TipTapEditor"
import { useParams } from "react-router-dom"

export function EditorPanel() {
  const open = useUIStore((s) => s.editorPanelOpen)
  const closeEditor = useUIStore((s) => s.closeEditor)
  const selectedCardId = useUIStore((s) => s.selectedCardId)
  const { id: boardId = "" } = useParams<{ id?: string }>()

  const { data: card } = useCard(selectedCardId)
  const { mutate: updateCard } = useUpdateCard(boardId)
  const { mutate: deleteCard } = useDeleteCard(boardId)
  const { mutate: updateColumn } = useUpdateColumn(boardId)

  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [content, setContent] = useState("")
  const [editingColumn, setEditingColumn] = useState(false)
  const [editingColumnValue, setEditingColumnValue] = useState("")
  const columnInputRef = useRef<HTMLInputElement>(null)
  const initialized = useRef(false)
  const savedTitle = useRef("")
  const savedDescription = useRef("")
  const savedContent = useRef("")

  useEffect(() => {
    if (card) {
      initialized.current = false
      setTitle(card.title)
      setDescription(card.description ?? "")
      setContent(card.content_markdown)
      savedTitle.current = card.title
      savedDescription.current = card.description ?? ""
      savedContent.current = card.content_markdown
      setEditingColumn(false)
      const t = setTimeout(() => { initialized.current = true }, 0)
      return () => clearTimeout(t)
    }
  }, [card?.id])

  useEffect(() => {
    if (editingColumn) columnInputRef.current?.select()
  }, [editingColumn])

  const debouncedContent = useDebounce(content, 1500)

  useEffect(() => {
    if (!initialized.current || !card) return
    if (debouncedContent === savedContent.current) return
    savedContent.current = debouncedContent
    updateCard({ id: card.id, data: { content_markdown: debouncedContent, content_preview: debouncedContent.slice(0, 200) } })
  }, [debouncedContent])

  function commitDescription() {
    if (!card) return
    const trimmed = description.trim()
    if (trimmed === savedDescription.current) return
    savedDescription.current = trimmed
    updateCard({ id: card.id, data: { description: trimmed } })
  }

  function handleDescriptionKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") { commitDescription(); (e.target as HTMLInputElement).blur() }
    if (e.key === "Escape") { setDescription(savedDescription.current); (e.target as HTMLInputElement).blur() }
  }

  function commitTitle() {
    if (!card) return
    const trimmed = title.trim()
    if (!trimmed || trimmed === savedTitle.current) return
    savedTitle.current = trimmed
    updateCard({ id: card.id, data: { title: trimmed } })
  }

  function handleTitleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      commitTitle();
      (e.target as HTMLInputElement).blur()
    }
    if (e.key === "Escape") {
      setTitle(savedTitle.current);
      (e.target as HTMLInputElement).blur()
    }
  }

  function startEditingColumn() {
    setEditingColumnValue(card?.column_title ?? "")
    setEditingColumn(true)
  }

  function commitColumnTitle() {
    const trimmed = editingColumnValue.trim()
    if (trimmed && card && trimmed !== card.column_title) {
      updateColumn({ id: card.column_id, data: { title: trimmed } })
    }
    setEditingColumn(false)
  }

  function handleColumnKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") commitColumnTitle()
    if (e.key === "Escape") setEditingColumn(false)
  }

  function handleDelete() {
    if (!card) return
    deleteCard(card.id, { onSuccess: closeEditor })
  }

  return (
    <aside
      className={cn(
        "h-screen bg-white border-l border-[#E2E8F0] shadow-2xl flex flex-col shrink-0 transition-all duration-300 overflow-hidden relative z-20",
        open ? "w-[450px]" : "w-0"
      )}
    >
      {/* Top bar */}
      <div className="flex items-center gap-1 px-5 py-3 border-b border-[#E2E8F0] shrink-0">
        <div className="flex-1">
          {card && (
            editingColumn ? (
              <input
                ref={columnInputRef}
                value={editingColumnValue}
                onChange={(e) => setEditingColumnValue(e.target.value)}
                onBlur={commitColumnTitle}
                onKeyDown={handleColumnKeyDown}
                className="text-xs font-medium text-[#0F172A] bg-orange-100 rounded-full px-2.5 py-0.5 outline-none w-fit"
              />
            ) : (
              <span
                className="inline-flex items-center text-xs font-medium text-[#0F172A] bg-orange-200 rounded-full px-2.5 py-0.5 cursor-pointer w-fit"
                onClick={startEditingColumn}
                title="Click to rename column"
              >
                {card.column_title}
              </span>
            )
          )}
        </div>
        <div className="flex items-center gap-1">
          <button className="p-1.5 rounded-md text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors" title="Pin">
            <Pin size={15} />
          </button>
          <button
            onClick={handleDelete}
            className="p-1.5 rounded-md text-[#94A3B8] hover:bg-red-50 hover:text-red-500 transition-colors"
            title="Delete card"
          >
            <Trash2 size={15} />
          </button>
          <button
            onClick={closeEditor}
            className="p-1.5 rounded-md text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors"
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-4">
        {card ? (
          <>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={handleTitleKeyDown}
              className="text-3xl font-bold text-[#0F172A] outline-none w-full bg-transparent placeholder:text-slate-300"
              placeholder="Card title"
            />

            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={commitDescription}
              onKeyDown={handleDescriptionKeyDown}
              className="text-sm text-[#475569] outline-none w-full bg-transparent placeholder:text-slate-300 -mt-2"
              placeholder="Add a short description…"
            />

            <TipTapEditor key={card.id} value={content} onChange={setContent} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-sm text-[#94A3B8]">
            Select a card to view
          </div>
        )}
      </div>

    </aside>
  )
}

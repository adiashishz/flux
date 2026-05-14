import { useEditor, EditorContent, Extension } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import TaskList from "@tiptap/extension-task-list"
import TaskItem from "@tiptap/extension-task-item"
import { Markdown } from "tiptap-markdown"

const ListShortcuts = Extension.create({
  name: "listShortcuts",
  addKeyboardShortcuts() {
    return {
      Tab: ({ editor }) => {
        if (editor.isActive("listItem") || editor.isActive("taskItem")) {
          editor.chain().focus().sinkListItem(editor.isActive("taskItem") ? "taskItem" : "listItem").run()
          return true
        }
        return false
      },
      "Shift-Tab": ({ editor }) => {
        if (editor.isActive("listItem") || editor.isActive("taskItem")) {
          editor.chain().focus().liftListItem(editor.isActive("taskItem") ? "taskItem" : "listItem").run()
          return true
        }
        return false
      },
      "Mod-Shift-7": ({ editor }) => editor.chain().focus().toggleOrderedList().run(),
      "Mod-Shift-8": ({ editor }) => editor.chain().focus().toggleBulletList().run(),
      "Mod-Shift-9": ({ editor }) => editor.chain().focus().toggleTaskList().run(),
    }
  },
})
import { Bold, Italic, Underline as UnderlineIcon, Strikethrough, List, ListOrdered, CheckSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"

interface TipTapEditorProps {
  value: string
  onChange: (markdown: string) => void
}

const TOOLBAR = [
  { icon: Bold, label: "Bold (Ctrl+B)", action: (e: any) => e.chain().focus().toggleBold().run(), isActive: (e: any) => e.isActive("bold") },
  { icon: Italic, label: "Italic (Ctrl+I)", action: (e: any) => e.chain().focus().toggleItalic().run(), isActive: (e: any) => e.isActive("italic") },
  { icon: UnderlineIcon, label: "Underline (Ctrl+U)", action: (e: any) => e.chain().focus().toggleUnderline().run(), isActive: (e: any) => e.isActive("underline") },
  { icon: Strikethrough, label: "Strikethrough (Ctrl+Shift+S)", action: (e: any) => e.chain().focus().toggleStrike().run(), isActive: (e: any) => e.isActive("strike") },
  { icon: List, label: "Bullet list (Ctrl+Shift+8)", action: (e: any) => e.chain().focus().toggleBulletList().run(), isActive: (e: any) => e.isActive("bulletList") },
  { icon: ListOrdered, label: "Ordered list (Ctrl+Shift+7)", action: (e: any) => e.chain().focus().toggleOrderedList().run(), isActive: (e: any) => e.isActive("orderedList") },
  { icon: CheckSquare, label: "Checklist (Ctrl+Shift+9)", action: (e: any) => e.chain().focus().toggleTaskList().run(), isActive: (e: any) => e.isActive("taskList") },
]

export function TipTapEditor({ value, onChange }: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TaskList,
      TaskItem.configure({ nested: true }),
      Markdown.configure({ html: false, tightLists: true }),
      ListShortcuts,
    ],
    content: value,
    onUpdate({ editor }) {
      onChange(editor.storage.markdown.getMarkdown())
    },
    editorProps: {
      attributes: {
        class: "outline-none min-h-[200px] text-sm text-[#0F172A] leading-relaxed tiptap-content",
      },
    },
  })

  if (!editor) return null

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-1 py-1 border-b border-[#E2E8F0]">
        {TOOLBAR.map(({ icon: Icon, label, action, isActive }) => (
          <Tooltip key={label}>
            <TooltipTrigger>
              <button
                onMouseDown={(e) => { e.preventDefault(); action(editor) }}
                className={cn(
                  "p-1.5 rounded text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors",
                  isActive(editor) && "bg-slate-100 text-[#475569]"
                )}
              >
                <Icon size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="bg-[#1E293B] text-white text-xs px-2 py-1 rounded shadow-md">{label}</TooltipContent>
          </Tooltip>
        ))}
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}

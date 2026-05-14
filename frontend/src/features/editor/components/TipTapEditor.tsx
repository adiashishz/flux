import { useEditor, EditorContent } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import TaskList from "@tiptap/extension-task-list"
import TaskItem from "@tiptap/extension-task-item"
import { Markdown } from "tiptap-markdown"
import { Bold, Italic, Underline as UnderlineIcon, List, CheckSquare } from "lucide-react"
import { cn } from "@/lib/utils"

interface TipTapEditorProps {
  value: string
  onChange: (markdown: string) => void
}

const TOOLBAR = [
  { icon: Bold, label: "Bold", action: (e: any) => e.chain().focus().toggleBold().run(), isActive: (e: any) => e.isActive("bold") },
  { icon: Italic, label: "Italic", action: (e: any) => e.chain().focus().toggleItalic().run(), isActive: (e: any) => e.isActive("italic") },
  { icon: UnderlineIcon, label: "Underline", action: (e: any) => e.chain().focus().toggleUnderline().run(), isActive: (e: any) => e.isActive("underline") },
  { icon: List, label: "Bullet list", action: (e: any) => e.chain().focus().toggleBulletList().run(), isActive: (e: any) => e.isActive("bulletList") },
  { icon: CheckSquare, label: "Checklist", action: (e: any) => e.chain().focus().toggleTaskList().run(), isActive: (e: any) => e.isActive("taskList") },
]

export function TipTapEditor({ value, onChange }: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TaskList,
      TaskItem.configure({ nested: false }),
      Markdown.configure({ html: false, tightLists: true }),
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
          <button
            key={label}
            title={label}
            onMouseDown={(e) => { e.preventDefault(); action(editor) }}
            className={cn(
              "p-1.5 rounded text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors",
              isActive(editor) && "bg-slate-100 text-[#475569]"
            )}
          >
            <Icon size={14} />
          </button>
        ))}
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}

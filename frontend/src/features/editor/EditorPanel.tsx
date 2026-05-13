import { useState } from "react"
import { X, Pin, Archive, Bold, Italic, Underline, List, CheckSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"
import { MarkdownEditor } from "./components/MarkdownEditor"
import { MarkdownPreview } from "./components/MarkdownPreview"

const MOCK_CONTENT = `## Overview

This quarter we're focused on shipping the core feature set.

- [x] Define scope and requirements
- [x] Design mockups approved
- [ ] Backend API implementation
- [ ] Frontend integration
- [ ] QA and testing

### Notes

Make sure to coordinate with the design team before finalising the component library. Reference the mockup in \`context/mockup.png\` for exact spacing.`

const COLUMNS = ["Ideas", "Researching", "Drafting", "Approved", "Published"]

export function EditorPanel() {
  const open = useUIStore((s) => s.editorPanelOpen)
  const closeEditor = useUIStore((s) => s.closeEditor)
  const [isEditing, setIsEditing] = useState(false)
  const [content, setContent] = useState(MOCK_CONTENT)
  const [title, setTitle] = useState("Feature Roadmap Q4")
  const [selectedColumn, setSelectedColumn] = useState("Drafting")

  return (
    <aside
      className={cn(
        "h-screen bg-white border-l border-[#E2E8F0] shadow-2xl flex flex-col shrink-0 transition-all duration-300 overflow-hidden",
        open ? "w-[450px]" : "w-0"
      )}
    >
      {/* Top bar */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-[#E2E8F0] shrink-0">
        <select
          value={selectedColumn}
          onChange={(e) => setSelectedColumn(e.target.value)}
          className="text-xs text-[#475569] border border-[#E2E8F0] rounded-md px-2 py-1 bg-white outline-none cursor-pointer hover:border-[#0D9488] transition-colors"
        >
          {COLUMNS.map((col) => (
            <option key={col} value={col}>{col}</option>
          ))}
        </select>

        <div className="flex items-center gap-1 ml-auto">
          <button className="p-1.5 rounded-md text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors">
            <Pin size={15} />
          </button>
          <button className="p-1.5 rounded-md text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors">
            <Archive size={15} />
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
        {/* Status */}
        <p className="text-[10px] font-semibold uppercase tracking-widest text-orange-600">
          {selectedColumn}
        </p>

        {/* Title */}
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="text-3xl font-bold text-[#0F172A] outline-none w-full bg-transparent placeholder:text-slate-300"
          placeholder="Card title"
        />

        {/* Formatting toolbar */}
        <div className="flex items-center gap-1 py-1 border-b border-[#E2E8F0]">
          {[
            { icon: <Bold size={14} />, label: "Bold" },
            { icon: <Italic size={14} />, label: "Italic" },
            { icon: <Underline size={14} />, label: "Underline" },
            { icon: <List size={14} />, label: "List" },
            { icon: <CheckSquare size={14} />, label: "Checklist" },
          ].map(({ icon, label }) => (
            <button
              key={label}
              title={label}
              className="p-1.5 rounded text-[#94A3B8] hover:bg-slate-100 hover:text-[#475569] transition-colors"
            >
              {icon}
            </button>
          ))}
          <button
            onClick={() => setIsEditing((e) => !e)}
            className={cn(
              "ml-auto px-2.5 py-1 rounded text-xs font-medium transition-colors",
              isEditing
                ? "bg-[#0D9488] text-white"
                : "text-[#475569] hover:bg-slate-100"
            )}
          >
            {isEditing ? "Preview" : "Edit"}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 min-h-[200px]">
          {isEditing ? (
            <MarkdownEditor value={content} onChange={setContent} />
          ) : (
            <MarkdownPreview content={content} />
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-[#E2E8F0] flex items-center justify-between shrink-0">
        <span className="text-xs text-[#94A3B8]">Last edited · 2 min ago</span>
        <span className="text-xs text-[#94A3B8]">
          {content.split(/\s+/).filter(Boolean).length} words
        </span>
      </div>
    </aside>
  )
}

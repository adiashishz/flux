import { forwardRef } from "react"

interface MarkdownEditorProps {
  value: string
  onChange: (value: string) => void
}

export const MarkdownEditor = forwardRef<HTMLTextAreaElement, MarkdownEditorProps>(
  ({ value, onChange }, ref) => (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full h-full resize-none outline-none text-sm text-[#0F172A] leading-relaxed"
      placeholder="Start writing…"
    />
  )
)

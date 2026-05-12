interface MarkdownEditorProps {
  value: string
  onChange: (value: string) => void
}

export function MarkdownEditor({ value, onChange }: MarkdownEditorProps) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full h-full resize-none outline-none text-sm text-[#0F172A] leading-relaxed font-mono"
      placeholder="Start writing…"
    />
  )
}

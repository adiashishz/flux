import ReactMarkdown from "react-markdown"

interface MarkdownPreviewProps {
  content: string
}

export function MarkdownPreview({ content }: MarkdownPreviewProps) {
  return (
    <div className="prose prose-slate prose-sm max-w-none">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  )
}

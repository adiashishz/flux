import { useState } from "react"
import { Send, Square } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

interface ChatInputProps {
  streaming: boolean
  onSend: (text: string) => void
  onStop: () => void
}

export function ChatInput({ streaming, onSend, onStop }: ChatInputProps) {
  const [value, setValue] = useState("")

  function submit() {
    if (!value.trim() || streaming) return
    onSend(value)
    setValue("")
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex items-end gap-2 border-t border-[#E2E8F0] p-3">
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask me to find, create, or move cards..."
        className="max-h-32 min-h-10 resize-none"
      />
      {streaming ? (
        <Button size="icon" variant="outline" onClick={onStop} title="Stop">
          <Square size={14} />
        </Button>
      ) : (
        <Button size="icon" onClick={submit} disabled={!value.trim()} title="Send">
          <Send size={14} />
        </Button>
      )}
    </div>
  )
}

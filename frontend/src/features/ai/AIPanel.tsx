import { useEffect, useRef } from "react"
import { useMatch } from "react-router-dom"
import { RotateCcw, Sparkles, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"
import { useAssistantChat } from "@/hooks/useAssistantChat"
import { ChatInput } from "./components/ChatInput"
import { ChatMessageView } from "./components/ChatMessageView"

const SUGGESTIONS = [
  "What is on this board?",
  "Find cards about invoices",
  "Create a card called Review PRs in the first column",
]

export function AIPanel() {
  const open = useUIStore((s) => s.aiPanelOpen)
  const setOpen = useUIStore((s) => s.setAiPanelOpen)
  const personalBoard = useMatch("/boards/:id")
  const workspaceBoard = useMatch("/workspaces/:workspaceId/boards/:id")
  const boardId = (personalBoard ?? workspaceBoard)?.params.id
  const { messages, streaming, send, stop, reset, confirmDelete, cancelDelete } = useAssistantChat(boardId)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" })
  }, [messages])

  return (
    <aside
      className={cn(
        "h-screen bg-white border-l border-[#E2E8F0] shadow-2xl flex flex-col shrink-0 transition-all duration-300 overflow-hidden relative z-20",
        open ? "w-[420px]" : "w-0"
      )}
    >
      <div className="flex h-full w-[420px] flex-col">
        <div className="flex items-center gap-2 border-b border-[#E2E8F0] px-4 py-3 shrink-0">
          <Sparkles size={16} className="text-teal-600" />
          <h2 className="text-sm font-semibold text-[#0F172A]">Ask AI</h2>
          <button
            onClick={reset}
            disabled={messages.length === 0}
            className="ml-auto p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 disabled:opacity-40"
            title="New conversation"
          >
            <RotateCcw size={14} />
          </button>
          <button
            onClick={() => setOpen(false)}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
            title="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 ? (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-slate-500">Ask about your boards, or have me change them.</p>
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => send(suggestion)}
                  className="rounded-lg border border-[#E2E8F0] px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-50"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {messages.map((message) => (
                <ChatMessageView
                  key={message.id}
                  message={message}
                  onConfirmDelete={(confirmation) => confirmDelete(message.id, confirmation)}
                  onCancelDelete={(confirmation) => cancelDelete(message.id, confirmation)}
                />
              ))}
            </div>
          )}
          <div ref={endRef} />
        </div>

        <ChatInput streaming={streaming} onSend={send} onStop={stop} />
      </div>
    </aside>
  )
}

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Search } from "lucide-react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useUIStore } from "@/store/ui"
import { useSemanticSearch } from "@/hooks/queries/useSemanticSearch"
import type { SearchResult } from "@/types"

const DEBOUNCE_MS = 300

export function SearchDialog() {
  const open = useUIStore((s) => s.searchOpen)
  const setSearchOpen = useUIStore((s) => s.setSearchOpen)
  const setSelectedCard = useUIStore((s) => s.setSelectedCard)
  const openEditor = useUIStore((s) => s.openEditor)
  const navigate = useNavigate()
  const [input, setInput] = useState("")
  const [query, setQuery] = useState("")
  const { data: results, isFetching, isError } = useSemanticSearch(query)

  useEffect(() => {
    const timer = setTimeout(() => setQuery(input.trim()), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [input])

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setSearchOpen(!useUIStore.getState().searchOpen)
      }
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [setSearchOpen])

  function handleOpenChange(next: boolean) {
    setSearchOpen(next)
    if (!next) {
      setInput("")
      setQuery("")
    }
  }

  function openResult(result: SearchResult) {
    navigate(`/boards/${result.board_id}`)
    setSelectedCard(result.id)
    openEditor()
    handleOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-xl" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle>Search by meaning</DialogTitle>
        </DialogHeader>
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            autoFocus
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe what you are looking for..."
            className="pl-8"
          />
        </div>
        <ScrollArea className="max-h-80">
          <ul className="flex flex-col gap-1">
            {isError && <li className="px-2 py-3 text-sm text-red-600">Search failed. Try again.</li>}
            {!isError && query.length >= 2 && !isFetching && results?.length === 0 && (
              <li className="px-2 py-3 text-sm text-slate-500">No matching cards.</li>
            )}
            {results?.map((result) => (
              <li key={result.id}>
                <button
                  onClick={() => openResult(result)}
                  className="w-full text-left px-2 py-2 rounded-md hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-900 truncate">{result.title}</span>
                    <span className="ml-auto text-xs text-slate-400 shrink-0">{Math.round(result.score * 100)}%</span>
                  </div>
                  <div className="text-xs text-slate-500 truncate">
                    {result.board_title} / {result.column_title}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}

import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui"
import relativeTime from "@/utils/relativeTime"
import type { Card as CardType } from "@/types"

const TAG_COLORS: Record<string, string> = {
  marketing: "bg-teal-50 text-teal-700",
  launch: "bg-purple-50 text-purple-700",
  analysis: "bg-orange-50 text-orange-600",
  research: "bg-blue-50 text-blue-700",
  workflows: "bg-green-50 text-green-700",
}

interface CardProps {
  card: CardType & { tags?: string[]; avatar?: string; date?: string }
}

export function Card({ card }: CardProps) {
  const setSelectedCard = useUIStore((s) => s.setSelectedCard)
  const openEditor = useUIStore((s) => s.openEditor)

  function handleClick() {
    setSelectedCard(card.id)
    openEditor()
  }

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow"
    >
      <p className="font-semibold text-[#0F172A] text-sm mb-1 leading-snug">{card.title}</p>
      {card.description && (
        <p className="text-xs text-[#475569] line-clamp-2 mb-3">
          {card.description}
        </p>
      )}

      {/* Tags */}
      {card.tags && card.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {card.tags.map((tag) => (
            <span
              key={tag}
              className={cn(
                "text-[10px] px-2 py-0.5 rounded-md font-medium",
                TAG_COLORS[tag] ?? "bg-slate-100 text-slate-600"
              )}
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Date + avatar */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-[#94A3B8]">{relativeTime(card.updated_at)}</span>
        {card.avatar && (
          <div className="w-6 h-6 rounded-full bg-orange-50 border border-orange-200 flex items-center justify-center">
            <span className="text-[10px] font-semibold text-orange-600">{card.avatar}</span>
          </div>
        )}
      </div>
    </div>
  )
}

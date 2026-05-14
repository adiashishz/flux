import type { Card as CardType } from "@/types"

interface DragOverlayCardProps {
  card: CardType & { tags?: string[]; avatar?: string; date?: string }
}

export function DragOverlayCard({ card }: DragOverlayCardProps) {
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-xl p-4 opacity-95 rotate-1 cursor-grabbing w-80">
      <p className="font-semibold text-[#0F172A] text-sm mb-1 leading-snug">{card.title}</p>
      {card.description && (
        <p className="text-xs text-[#475569] line-clamp-2">{card.description}</p>
      )}
    </div>
  )
}

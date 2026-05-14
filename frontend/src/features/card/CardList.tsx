import { Card } from "./components/Card"
import type { Card as CardType } from "@/types"

type MockCard = CardType & { tags?: string[]; avatar?: string; date?: string }

interface CardListProps {
  cards: MockCard[]
  activeCardId?: string
}

export function CardList({ cards, activeCardId }: CardListProps) {
  return (
    <div className="flex flex-col gap-2">
      {cards.map((card) => (
        <Card key={card.id} card={card} isBeingDragged={card.id === activeCardId} />
      ))}
    </div>
  )
}

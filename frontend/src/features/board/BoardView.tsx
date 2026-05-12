import { Toolbar } from "@/components/layout/Toolbar"
import { Column } from "@/features/column/Column"
import { AddColumnButton } from "@/features/column/components/AddColumnButton"

const MOCK_BOARD = {
  id: "1",
  title: "Content Marketing Pipeline",
  columns: [
    {
      id: "col-1", board_id: "1", title: "Ideas", position: 1000, card_count: 3,
      cards: [
        { id: "c1", column_id: "col-1", title: "SEO article: Top 10 productivity tools", content_preview: "Research and write a comprehensive guide covering the best productivity tools for remote teams.", tags: ["marketing", "research"], avatar: "A", date: "May 8", position: 1000, created_at: "", updated_at: "" },
        { id: "c2", column_id: "col-1", title: "Social media campaign for Q3 launch", content_preview: "Plan and execute a multi-platform campaign across Twitter, LinkedIn and Instagram.", tags: ["launch", "marketing"], avatar: "B", date: "May 9", position: 2000, created_at: "", updated_at: "" },
        { id: "c3", column_id: "col-1", title: "Competitor analysis report", content_preview: "Deep dive into competitor content strategies and identify gaps we can exploit.", tags: ["analysis"], avatar: "A", date: "May 10", position: 3000, created_at: "", updated_at: "" },
      ],
    },
    {
      id: "col-2", board_id: "1", title: "Researching", position: 2000, card_count: 2,
      cards: [
        { id: "c4", column_id: "col-2", title: "Email newsletter redesign", content_preview: "Redesign the monthly newsletter template to improve open and click-through rates.", tags: ["marketing"], avatar: "C", date: "May 7", position: 1000, created_at: "", updated_at: "" },
        { id: "c5", column_id: "col-2", title: "Content workflow automation", content_preview: "Explore tools and integrations to automate the content review and publishing workflow.", tags: ["workflows", "research"], avatar: "A", date: "May 6", position: 2000, created_at: "", updated_at: "" },
      ],
    },
    {
      id: "col-3", board_id: "1", title: "Drafting", position: 3000, card_count: 3,
      cards: [
        { id: "c6", column_id: "col-3", title: "Feature Roadmap Q4", content_preview: "Detailed breakdown of Q4 features, timelines and owner assignments.", tags: ["launch"], avatar: "B", date: "May 5", position: 1000, created_at: "", updated_at: "" },
        { id: "c7", column_id: "col-3", title: "Case study: Enterprise onboarding", content_preview: "Document the successful onboarding of Acme Corp and turn it into a public case study.", tags: ["marketing", "analysis"], avatar: "A", date: "May 4", position: 2000, created_at: "", updated_at: "" },
        { id: "c8", column_id: "col-3", title: "Video script: product walkthrough", content_preview: "Write a 5-minute script for the product walkthrough video targeting new signups.", tags: ["marketing"], avatar: "C", date: "May 3", position: 3000, created_at: "", updated_at: "" },
      ],
    },
    {
      id: "col-4", board_id: "1", title: "Approved", position: 4000, card_count: 2,
      cards: [
        { id: "c9", column_id: "col-4", title: "Landing page copy update", content_preview: "Refresh the homepage headline and subheadline to align with new positioning.", tags: ["launch", "marketing"], avatar: "B", date: "May 2", position: 1000, created_at: "", updated_at: "" },
        { id: "c10", column_id: "col-4", title: "Partner spotlight blog post", content_preview: "Feature our integration partner in a co-authored blog post.", tags: ["marketing"], avatar: "A", date: "May 1", position: 2000, created_at: "", updated_at: "" },
      ],
    },
    {
      id: "col-5", board_id: "1", title: "Published", position: 5000, card_count: 1,
      cards: [
        { id: "c11", column_id: "col-5", title: "April monthly roundup", content_preview: "Recap of all content published in April, performance metrics and learnings.", tags: ["analysis", "marketing"], avatar: "C", date: "Apr 30", position: 1000, created_at: "", updated_at: "" },
      ],
    },
  ],
}

export function BoardView() {
  return (
    <div className="flex flex-col h-full">
      <Toolbar title={MOCK_BOARD.title} />
      <div className="flex flex-row gap-6 overflow-x-auto h-full p-6 items-start">
        {MOCK_BOARD.columns.map((column) => (
          <Column key={column.id} column={column} />
        ))}
        <AddColumnButton />
      </div>
    </div>
  )
}

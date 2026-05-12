import { Plus } from "lucide-react"

export function AddColumnButton() {
  return (
    <button className="w-80 shrink-0 flex items-center justify-center gap-2 h-12 rounded-xl border-2 border-dashed border-[#E2E8F0] text-[#94A3B8] text-sm hover:border-[#0D9488] hover:text-[#0D9488] transition-colors">
      <Plus size={16} />
      Add column
    </button>
  )
}

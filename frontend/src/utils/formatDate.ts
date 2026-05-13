export default function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  try {
    return new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
  } catch {
    return "—"
  }
}

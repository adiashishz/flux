const THRESHOLDS: [number, Intl.RelativeTimeFormatUnit][] = [
  [60, "seconds"],
  [3600, "minutes"],
  [86400, "hours"],
  [604800, "days"],
  [2592000, "weeks"],
  [31536000, "months"],
]

export default function relativeTime(value: string | null | undefined): string {
  if (!value) return "—"
  try {
    const diff = (new Date(value).getTime() - Date.now()) / 1000
    const abs = Math.abs(diff)
    for (let i = 0; i < THRESHOLDS.length; i++) {
      const [threshold, unit] = THRESHOLDS[i]
      const divisor = i === 0 ? 1 : THRESHOLDS[i - 1][0]
      if (abs < threshold) {
        const val = Math.round(diff / divisor)
        return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(val, unit)
      }
    }
    return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
      Math.round(diff / 2592000), "months"
    )
  } catch {
    return "—"
  }
}

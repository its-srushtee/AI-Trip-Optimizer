
export function daysBetween(start, end) {
  if (!start || !end) return 0
  const s = new Date(start)
  const e = new Date(end)
  if (isNaN(s) || isNaN(e)) return 0
  const diff = Math.round((e - s) / 86400000) + 1
  return diff > 0 ? diff : 0
}

export function formatRange(start, end) {
  if (!start || !end) return 'Dates not set'
  const s = new Date(start)
  const e = new Date(end)
  if (isNaN(s) || isNaN(e)) return `${start} – ${end}`
  const a = s.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const b = e.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return `${a} – ${b}`
}


export function recommend(destinations, prefs) {
  const list = destinations || []
  const hasPrefs = prefs && (prefs.interests?.length > 0 || prefs.style || prefs.pace)

  if (!hasPrefs) {
    return {
      personalized: false,
      picks: list.slice(0, 4).map((d) => ({ ...d, match: null })),
    }
  }

  const ints = prefs.interests || []
  const scored = list.map((d) => {
    let s = 0
    ;(d.tags || []).forEach((t) => {
      if (ints.includes(t)) s += 3
    })
    if ((d.styles || []).includes(prefs.style)) s += 3
    if ((d.paces || []).includes(prefs.pace)) s += 2
    return { ...d, s }
  })

  const sorted = [...scored].sort((a, b) => b.s - a.s)
  const max = sorted[0]?.s || 1
  const picks = sorted.slice(0, 4).map((d) => ({
    ...d,
    match: Math.min(98, Math.round(50 + (d.s / max) * 48)),
  }))

  return { personalized: ints.length > 0, picks }
}

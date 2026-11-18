// Recommendation scoring — pure function. Destinations now come from the
// backend (`GET /destinations`), so this file no longer ships a static list.
//
// Expected destination shape (matches the API response):
//   { id, name, country, image_url, tags: [], styles: [], paces: [], price, blurb }

export function recommend(destinations, prefs) {
  const list = destinations || []
  const hasPrefs = prefs && (prefs.interests?.length > 0 || prefs.style || prefs.pace)

  // If already scored by backend recommendation engine, respect backend's multi-factor order
  const hasBackendScores = list.some((d) => typeof d.match_score === 'number' || Array.isArray(d.match_reasons))
  if (hasBackendScores) {
    return {
      personalized: Boolean(hasPrefs),
      picks: list.map((d) => ({
        ...d,
        match: d.match_score ?? (hasPrefs ? 88 : null),
      })),
    }
  }

  if (!hasPrefs) {
    return {
      personalized: false,
      picks: list.slice(0, 8).map((d) => ({ ...d, match: null })),
    }
  }

  const ints = (prefs.interests || []).map((x) => String(x).toLowerCase())
  const scored = list.map((d) => {
    let s = 10
    const tags = (d.tags || []).map((t) => String(t).toLowerCase())
    const text = (d.blurb || '').toLowerCase() + ' ' + (d.name || '').toLowerCase()

    ints.forEach((interest) => {
      if (tags.includes(interest)) s += 15
      if (text.includes(interest)) s += 8
    })

    // Nature + Adventure -> mountains, trekking, forests, outdoors
    if (ints.includes('nature') && ints.includes('adventure')) {
      if (/mountain|trekking|hiking|forest|alpine|outdoor|alps|rocky/i.test(text + ' ' + tags.join(' '))) {
        s += 25
      }
    }
    // Culture + History -> heritage, museums, temples, historic
    if (ints.includes('culture') || ints.includes('history')) {
      if (/temple|museum|historic|heritage|colosseum|ancient|castle/i.test(text + ' ' + tags.join(' '))) {
        s += 20
      }
    }
    // Food -> culinary experiences
    if (ints.includes('food')) {
      if (/food|culinary|dining|sushi|street food|tapas|trattoria/i.test(text + ' ' + tags.join(' '))) {
        s += 20
      }
    }
    // Relaxation -> beaches, retreats, spas, scenic stays
    if (ints.includes('relaxation') || ints.includes('beaches')) {
      if (/beach|villa|lagoon|spa|retreat|peaceful|hot spring|sunset/i.test(text + ' ' + tags.join(' '))) {
        s += 20
      }
    }

    // Food + Photography
    if (ints.includes('food') && ints.includes('photography')) {
      if (/food|sushi|ramen|culinary|market|neon|skyline|crossing|photogenic/i.test(text + ' ' + tags.join(' '))) {
        s += 35
      }
    }

    const styleStr = (prefs.style || '').toLowerCase()
    const dStyles = (d.styles || []).map((x) => String(x).toLowerCase())
    if (dStyles.includes(styleStr)) s += 12
    else if (styleStr === 'backpacker' && dStyles.includes('budget')) s += 12

    const paceStr = (prefs.pace || '').toLowerCase()
    const dPaces = (d.paces || []).map((x) => String(x).toLowerCase())
    if (dPaces.includes(paceStr)) s += 10
    else if ((paceStr === 'moderate' && dPaces.includes('balanced')) || (paceStr === 'fast-paced' && dPaces.includes('packed'))) s += 10

    return { ...d, s }
  })

  const sorted = [...scored].sort((a, b) => b.s - a.s)
  const max = sorted[0]?.s || 1
  const picks = sorted.map((d) => ({
    ...d,
    match: Math.min(99, Math.round(55 + (d.s / max) * 44)),
  }))

  return { personalized: ints.length > 0, picks }
}

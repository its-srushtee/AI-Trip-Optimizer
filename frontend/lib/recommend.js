// Recommendation scoring — pure function. Destinations now come from the
// backend (`GET /destinations`), so this file no longer ships a static list.
//
// Expected destination shape (matches the API response):
//   { id, name, country, image_url, tags: [], styles: [], paces: [], price, blurb }

export function recommend(destinations, prefs) {
  const list = destinations || []
  const hasPrefs = prefs && (prefs.interests?.length > 0 || prefs.style || prefs.pace)

  if (!hasPrefs) {
    return {
      personalized: false,
      picks: list.slice(0, 4).map((d) => ({ ...d, match: null })),
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

    if ((d.styles || []).includes(prefs.style)) s += 10
    if ((d.paces || []).includes(prefs.pace)) s += 8
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

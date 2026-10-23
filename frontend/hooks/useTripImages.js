import { useEffect, useState } from 'react'
import { api, resolveImageUrl } from '../services/api.js'

/**
 * Resolve a photo for every trip destination.
 *
 * The backend decides where the photo comes from (local catalogue file, cached
 * provider URL, or a fresh provider lookup) — the frontend just asks by name.
 * Results are keyed by the destination string and resolved in parallel.
 *
 * Returns { byName, get } where get(name) -> { url, credit, credit_url, license }
 */
export function useTripImages(names) {
  const [byName, setByName] = useState({})

  // Stable key so the effect doesn't refire on every render.
  const key = JSON.stringify([...new Set(names.filter(Boolean))].sort())

  useEffect(() => {
    const list = JSON.parse(key)
    if (!list.length) return
    let cancelled = false

    Promise.all(
      list.map(async (name) => {
        try {
          const r = await api.destinationImage(name)
          return [name, { ...r, url: resolveImageUrl(r.url) }]
        } catch {
          return [name, { url: resolveImageUrl('/images/hero.jpg') }]
        }
      }),
    ).then((pairs) => {
      if (!cancelled) setByName(Object.fromEntries(pairs))
    })

    return () => {
      cancelled = true
    }
  }, [key])

  const get = (name) => byName[name] || null
  return { byName, get }
}

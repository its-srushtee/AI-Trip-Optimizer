import { useEffect, useState } from 'react'
import { api, resolveImageUrl } from '../services/api.js'

export function useTripImages(names) {
  const [byName, setByName] = useState({})

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

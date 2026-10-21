import { useEffect, useState } from 'react'
import { api } from '../../services/api.js'

/**
 * Site-level photo credit.
 *
 * Required by provider terms, not decoration:
 *   - Pexels:   "show a prominent link to Pexels" wherever their API is used.
 *   - Unsplash: the app must attribute Unsplash itself, with utm parameters.
 *
 * Per-image credits on the cards satisfy the *photographer* half; this
 * satisfies the *platform* half. Only providers that have actually served an
 * image are listed, so a deployment with no key shows nothing.
 */
export default function ProviderCredit({ className = '' }) {
  const [providers, setProviders] = useState([])

  useEffect(() => {
    let cancelled = false
    api
      .imageProviders()
      .then((list) => {
        if (!cancelled && Array.isArray(list)) setProviders(list)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  if (!providers.length) return null

  return (
    <p className={`text-xs text-faint ${className}`}>
      Destination photos provided by{' '}
      {providers.map((p, i) => (
        <span key={p.name}>
          {i > 0 && (i === providers.length - 1 ? ' and ' : ', ')}
          <a
            href={p.url}
            target="_blank"
            rel="noreferrer nofollow"
            className="text-brand hover:underline"
          >
            {p.name}
          </a>
        </span>
      ))}
      .
    </p>
  )
}

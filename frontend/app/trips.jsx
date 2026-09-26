import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import PageHeader from '../components/common/PageHeader.jsx'
import Button from '../components/common/Button.jsx'
import TripCard from '../components/trip/TripCard.jsx'
import { api, getToken, clearToken, resolveImageUrl } from '../services/api.js'
import { useTripImages } from '../hooks/useTripImages.js'
import ProviderCredit from '../components/common/ProviderCredit.jsx'
import { clearUser } from '../lib/userStore.js'

export default function Trips() {
  const navigate = useNavigate()
  const [trips, setTrips] = useState([])
  const [dests, setDests] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) {
      navigate('/login')
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const [tripList, destList] = await Promise.all([api.listTrips(token), api.destinations()])
        if (cancelled) return
        setTrips(tripList)
        setDests(destList)
      } catch (err) {
        if (cancelled) return
        if (err.status === 401) {
          clearUser()
          clearToken()
          navigate('/login')
        } else {
          setLoadError(err.message)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [navigate])

  const tripImages = useTripImages(trips.map((t) => t.destination))
  const imageFor = (name) =>
    tripImages.get(name)?.url || resolveImageUrl('/images/hero.jpg')
  const creditFor = (name) => {
    const r = tripImages.get(name)
    return r?.credit
      ? {
          credit: r.credit,
          url: r.credit_url,
          license: r.license,
          license_url: r.license_url,
          source_name: r.source_name,
          source_url: r.source_url,
        }
      : null
  }

  const handleRemove = async (id) => {
    try {
      await api.deleteTrip(id, getToken())
      setTrips((prev) => prev.filter((t) => t.id !== id))
    } catch (err) {
      setLoadError(err.message)
    }
  }

  return (
    <div className="min-h-screen w-full">
      <PageHeader>
        <Link
          to="/create-trip"
          className="inline-flex h-9 items-center rounded-md px-4 text-[13px] font-medium text-white transition-colors"
          style={{ backgroundColor: 'var(--accent)' }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--accent-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'var(--accent)')}
        >
          Create Trip
        </Link>
      </PageHeader>

      <main className="mx-auto max-w-5xl px-5 py-8">
        <div className="flex items-baseline justify-between gap-3">
          <h1 className="text-xl font-semibold tracking-tight text-main">Your trips</h1>
          {trips.length > 0 && (
            <span className="text-[13px] tabular-nums text-faint">
              {trips.length} saved
            </span>
          )}
        </div>

        {loadError && (
          <div className="alert alert-warn mt-5 flex items-center justify-between gap-3">
            <span>Couldn&apos;t load your trips: {loadError}</span>
            <button
              onClick={() => window.location.reload()}
              className="inline-flex shrink-0 items-center gap-1.5 font-medium underline underline-offset-2"
            >
              <RefreshCw size={13} /> Retry
            </button>
          </div>
        )}

        {loading ? (
          <p className="mt-5 text-[13px] text-mut">Loading…</p>
        ) : trips.length === 0 ? (
          <div className="mt-5 rounded-md border border-dashed border-subtle px-6 py-12 text-center">
            <p className="text-[13px] font-medium text-soft">No trips saved yet</p>
            <p className="mx-auto mt-1 max-w-xs text-[13px] text-mut">
              Create your first trip and it will appear here.
            </p>
            <Button variant="secondary" size="sm" className="mt-4" onClick={() => navigate('/create-trip')}>
              Create Trip
            </Button>
          </div>
        ) : (
          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={trip}
                image={imageFor(trip.destination)}
                credit={creditFor(trip.destination)}
                onRemove={handleRemove}
              />
            ))}
          </div>
        )}

        <footer className="mt-10 border-t border-subtle py-5">
          <ProviderCredit />
        </footer>
      </main>
    </div>
  )
}

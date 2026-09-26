import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LayoutGrid, Map, Settings, LogOut, RefreshCw } from 'lucide-react'
import Logo from '../components/common/Logo.jsx'
import Button from '../components/common/Button.jsx'
import ThemeToggle from '../components/common/ThemeToggle.jsx'
import SettingsModal from '../components/common/SettingsModal.jsx'
import PlanForm from '../components/trip/PlanForm.jsx'
import TripCard from '../components/trip/TripCard.jsx'
import ProfilePrompt from '../components/common/ProfilePrompt.jsx'
import { interests } from '../lib/constants.js'
import { recommend } from '../lib/recommend.js'
import { getUser, clearUser, saveUser } from '../lib/userStore.js'
import { api, getToken, clearToken, resolveImageUrl } from '../services/api.js'
import { useTripImages } from '../hooks/useTripImages.js'
import ProviderCredit from '../components/common/ProviderCredit.jsx'
import {
  userProfileComplete,
  isPromptDismissed,
  dismissPrompt,
  clearDismissed,
} from '../lib/profile.js'

const NAV = [
  { icon: LayoutGrid, label: 'Overview', target: 'top' },
  { icon: Map, label: 'Trips', target: 'trips' },
  { icon: Settings, label: 'Settings', target: null },
]

export default function Dashboard() {
  const navigate = useNavigate()

  const [user, setUser] = useState(() => getUser())
  const [trips, setTrips] = useState([])
  const [dests, setDests] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [reload, setReload] = useState(0)
  const [promptDismissed, setPromptDismissed] = useState(false)
  const [savedPlaces, setSavedPlaces] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('tripopt_places')) || []
    } catch {
      return []
    }
  })

  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there'
  const prefs = user?.preferences

  const [form, setForm] = useState({
    destination: '',
    start: '',
    end: '',
    budget: 1000,
    travelers: 1,
    selected: [],
  })
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [justAdded, setJustAdded] = useState(false)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      navigate('/login')
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const [me, tripList, destList] = await Promise.all([
          api.me(token),
          api.listTrips(token),
          api.destinations(),
        ])
        if (cancelled) return
        saveUser(me)
        setUser(me)
        setTrips(tripList)
        setDests(destList)
        if (me.preferences?.interests) {
          setForm((f) => ({ ...f, selected: me.preferences.interests }))
        }
        if (userProfileComplete(me)) {
          clearDismissed(me.id)
          setPromptDismissed(false)
        } else {
          setPromptDismissed(isPromptDismissed(me.id))
        }
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
  }, [navigate, reload])

  const set = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }))
    if (formError) setFormError('')
  }
  const toggleInterest = (id) =>
    setForm((f) => ({
      ...f,
      selected: f.selected.includes(id)
        ? f.selected.filter((x) => x !== id)
        : [...f.selected, id],
    }))

  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  const handlePlan = async (e) => {
    e.preventDefault()
    if (!form.destination.trim()) {
      setFormError('Enter a destination.')
      return
    }
    if (!form.start || !form.end) {
      setFormError('Choose start and end dates.')
      return
    }
    if (new Date(form.end) < new Date(form.start)) {
      setFormError('The end date must be after the start date.')
      return
    }
    setFormError('')
    setSubmitting(true)
    try {
      const created = await api.createTrip(
        {
          destination: form.destination.trim(),
          start_date: form.start,
          end_date: form.end,
          budget: form.budget,
          travelers: form.travelers,
          interests: form.selected,
        },
        getToken(),
      )
      setTrips((prev) => [created, ...prev])
      setForm((f) => ({ ...f, destination: '', start: '', end: '' }))
      setJustAdded(true)
      setTimeout(() => {
        setJustAdded(false)
        scrollTo('trips')
      }, 400)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleRemove = async (id) => {
    try {
      await api.deleteTrip(id, getToken())
      setTrips((prev) => prev.filter((t) => t.id !== id))
    } catch (err) {
      setLoadError(err.message)
    }
  }

  const signOut = () => {
    clearUser()
    clearToken()
    navigate('/login')
  }

  const [settingsOpen, setSettingsOpen] = useState(false)

  const handleNav = (item) => {
    if (item.label === 'Settings') setSettingsOpen(true)
    else if (item.target) scrollTo(item.target)
  }

  const saveProfile = async ({ name, email }) => {
    try {
      const updated = await api.updateMe({ name, email }, getToken())
      saveUser(updated)
      setUser(updated)
    } catch (err) {
      window.alert(err.message)
    }
  }

  const savePreferences = async (preferences) => {
    try {
      const updated = await api.updateMe({ preferences }, getToken())
      saveUser(updated)
      setUser(updated)
      if (userProfileComplete(updated)) clearDismissed(updated.id)
    } catch (err) {
      window.alert(err.message)
    }
  }

  const clearData = async () => {
    try {
      await Promise.all(trips.map((t) => api.deleteTrip(t.id, getToken())))
    } catch {
      
    }
    localStorage.removeItem('tripopt_places')
    setTrips([])
    setSavedPlaces([])
  }

  const showProfilePrompt = !loading && !userProfileComplete(user) && !promptDismissed

  const handleDismissPrompt = () => {
    if (user?.id) dismissPrompt(user.id)
    setPromptDismissed(true)
  }

  const { picks, personalized } = recommend(dests, prefs)

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

  const hasPrefs = prefs && Object.keys(prefs).length > 0 && prefs.style

  return (
    <div className="min-h-screen w-full">
      
      <header
        className="sticky top-0 z-30 flex items-center justify-between border-b border-subtle px-4 py-2.5 lg:hidden"
        style={{ backgroundColor: 'var(--panel)' }}
      >
        <Logo size={26} />
        <div className="flex items-center gap-1.5">
          <ThemeToggle />
          <button
            onClick={signOut}
            className="grid h-11 w-11 place-items-center rounded-full border border-subtle bg-panel text-mut transition-colors hv"
            aria-label="Sign out"
          >
            <LogOut size={15} />
          </button>
        </div>
      </header>

      <aside
        className="fixed inset-y-0 left-0 z-30 hidden w-56 flex-col border-r border-subtle lg:flex"
        style={{ backgroundColor: 'var(--panel)' }}
      >
        <div className="px-4 py-4">
          <Logo size={26} />
        </div>

        <nav className="flex-1 space-y-0.5 px-2.5">
          {NAV.map((item) => {
            const Icon = item.icon
            const active = item.label === 'Overview'
            return (
              <button
                key={item.label}
                onClick={() => handleNav(item)}
                className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-[14px] transition-colors ${
                  active ? 'font-medium text-main' : 'text-mut hv hover:text-soft'
                }`}
                style={active ? { backgroundColor: 'var(--fill)' } : undefined}
              >
                <Icon size={16} />
                {item.label}
                {item.label === 'Trips' && trips.length > 0 && (
                  <span className="ml-auto text-xs tabular-nums text-faint">{trips.length}</span>
                )}
              </button>
            )
          })}
        </nav>

        <div className="border-t border-subtle p-3">
          <div className="flex items-center gap-2.5 px-1 pb-2.5">
            <span
              className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-bold"
              style={{ backgroundColor: 'var(--accent)', color: 'var(--accent-ink)' }}
            >
              {firstName.slice(0, 2).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-medium text-main">{user?.name || 'Traveler'}</p>
              <p className="truncate text-xs text-faint">{user?.email || ''}</p>
            </div>
          </div>
          <div className="flex gap-1.5">
            <Button variant="secondary" size="sm" className="flex-1" onClick={signOut}>
              <LogOut size={14} /> Sign out
            </Button>
            <ThemeToggle className="h-8 w-8" />
          </div>
        </div>
      </aside>

      <main className="main-pad lg:pl-56">
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8 lg:py-9" id="top">
          
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[15px] text-mut">Good to see you</p>
              <h1 className="display mt-0.5 text-[1.875rem] text-main sm:text-[2.5rem] lg:text-[2.75rem]">
                {user?.name || 'Traveler'}
              </h1>
              <p className="mt-2 text-[15px] text-mut">
                {trips.length > 0
                  ? `${trips.length} saved trip${trips.length > 1 ? 's' : ''} · plan your next one below`
                  : 'Create your first trip to get started.'}
              </p>
            </div>
            <div className="hidden sm:block">
              <ThemeToggle />
            </div>
          </div>

          {showProfilePrompt && (
            <div className="mt-5">
              <ProfilePrompt onDismiss={handleDismissPrompt} />
            </div>
          )}

          {loadError && (
            <div className="alert alert-warn mt-5 flex items-center justify-between gap-3">
              <span>Couldn&apos;t load your data: {loadError}</span>
              <button
                onClick={() => {
                  setLoadError('')
                  setLoading(true)
                  setReload((r) => r + 1)
                }}
                className="inline-flex shrink-0 items-center gap-1.5 font-medium underline underline-offset-2"
              >
                <RefreshCw size={13} /> Retry
              </button>
            </div>
          )}

          <div className="mt-6 grid gap-5 lg:grid-cols-3" id="plan">
            <section className="card p-5 lg:col-span-2">
              <h2 className="section-title">Create a trip</h2>
              <p className="section-sub mb-5">
                Enter your destination, dates and budget. You can generate an itinerary once
                the trip is saved.
              </p>
              <PlanForm
                form={form}
                onFieldChange={set}
                onToggleInterest={toggleInterest}
                onSubmit={handlePlan}
                submitting={submitting}
                justAdded={justAdded}
                error={formError}
              />
            </section>

            <div className="space-y-5">
              
              <section className="card p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <h2 className="section-title">Preferences</h2>
                  <Link
                    to="/complete-profile"
                    className="-mr-2 inline-flex min-h-[44px] items-center px-2 text-[14px] font-semibold text-brand hover:underline lg:min-h-0 lg:py-0"
                  >
                    {hasPrefs ? 'Edit' : 'Add'}
                  </Link>
                </div>

                {hasPrefs ? (
                  <>
                    <dl className="mt-3 space-y-0">
                      <PrefRow label="Style" value={prefs.style} />
                      <PrefRow label="Pace" value={prefs.pace} />
                      <PrefRow label="Stay" value={prefs.accommodation} />
                      <PrefRow label="Food" value={prefs.food} />
                    </dl>
                    {prefs.interests?.length > 0 && (
                      <div className="mt-3 border-t border-subtle pt-3">
                        <p className="eyebrow mb-1.5">Interests</p>
                        <div className="flex flex-wrap gap-1">
                          {prefs.interests.map((id) => {
                            const it = interests.find((x) => x.id === id)
                            return it ? (
                              <span key={id} className="tag">
                                {it.label}
                              </span>
                            ) : null
                          })}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="mt-2 text-[13px] leading-relaxed text-mut">
                    Not set yet. Adding them lets us match destinations to how you travel.
                  </p>
                )}
              </section>

              <section className="card p-4" id="saved">
                <h2 className="section-title">Saved places</h2>
                {savedPlaces.length > 0 ? (
                  <ul className="mt-2.5 space-y-0.5">
                    {savedPlaces.map((p) => (
                      <li
                        key={p.id}
                        className="flex items-center gap-2.5 rounded px-1.5 py-1.5 text-[13px] transition-colors hv"
                      >
                        <span className="flex-1 truncate text-soft">{p.name}</span>
                        <span className="text-xs text-faint">{p.city}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-[13px] text-mut">
                    Places you save while browsing will appear here.
                  </p>
                )}
              </section>
            </div>
          </div>

          <section className="mt-9">
            <div className="flex items-baseline justify-between gap-3">
              <div>
                <h2 className="section-title">
                  {personalized ? 'Recommended for you' : 'Popular destinations'}
                </h2>
                <p className="section-sub">
                  {personalized ? (
                    'Ranked against your saved preferences.'
                  ) : (
                    <>
                      <Link to="/complete-profile" className="font-medium text-brand hover:underline">
                        Complete your profile
                      </Link>{' '}
                      to see destinations matched to you.
                    </>
                  )}
                </p>
              </div>
            </div>

            {loading ? (
              <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="h-[16rem] animate-pulse rounded-2xl bg-soft sm:h-[19rem]" />
                ))}
              </div>
            ) : picks.length === 0 ? (
              <p className="mt-4 rounded-md border border-dashed border-subtle px-4 py-8 text-center text-[13px] text-mut">
                No destinations available.
              </p>
            ) : (
              <div className="rail mt-5 -mx-4 px-4 sm:mx-0 sm:grid sm:grid-cols-2 sm:gap-4 sm:overflow-visible sm:px-0 lg:grid-cols-4">
                {picks.map((d) => (
                  <article key={d.id} className="group flex w-[78vw] max-w-[20rem] flex-col sm:w-auto sm:max-w-none">
                    
                    <button
                      type="button"
                      onClick={() => {
                        set('destination', d.name)
                        scrollTo('plan')
                      }}
                      className="photo-card scrim card-hover block h-[16rem] w-full text-left sm:h-[19rem]"
                    >
                      <img src={resolveImageUrl(d.image_url)} alt="" />

                      {d.match != null && (
                        <span className="tag-float absolute left-3 top-3 z-10">
                          {d.match}% match
                        </span>
                      )}

                      <div className="absolute inset-x-0 bottom-0 z-10 p-4">
                        <h3 className="display-sm text-[1.375rem] text-white">{d.name}</h3>
                        <p className="mt-0.5 text-[13px] text-white/70">{d.country}</p>
                        <p
                          className="mt-2 text-[15px] font-semibold"
                          style={{ color: 'var(--accent)' }}
                        >
                          From {d.price}
                        </p>
                      </div>
                    </button>

                    <p className="mt-3 line-clamp-2 px-0.5 text-[13px] leading-snug text-mut">
                      {d.blurb}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="mt-9" id="trips">
            <div className="flex items-baseline justify-between gap-3">
              <div>
                <h2 className="section-title">Your trips</h2>
                <p className="section-sub">
                  {trips.length > 0
                    ? 'Open a trip to generate or review its itinerary.'
                    : 'Saved trips appear here.'}
                </p>
              </div>
              {trips.length > 0 && (
                <span className="text-[13px] tabular-nums text-faint">{trips.length}</span>
              )}
            </div>

            {loading ? (
              <p className="mt-4 text-[13px] text-mut">Loading…</p>
            ) : trips.length === 0 ? (
              <div className="mt-4 rounded-md border border-dashed border-subtle px-6 py-10 text-center">
                <p className="text-[13px] font-medium text-soft">No trips saved yet</p>
                <p className="mx-auto mt-1 max-w-xs text-[13px] text-mut">
                  Create a trip above and it will show up here.
                </p>
                <Button variant="secondary" size="sm" className="mt-4" onClick={() => scrollTo('plan')}>
                  Create Trip
                </Button>
              </div>
            ) : (
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
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
          </section>

          <footer className="mt-10 border-t border-subtle py-5 text-[13px] text-faint">
            Trip Optimizer — trips and preferences are saved to your account.
            <ProviderCredit className="mt-1.5" />
          </footer>
        </div>
      </main>

      <nav
        className="fixed inset-x-0 bottom-0 z-40 border-t border-subtle lg:hidden"
        style={{
          backgroundColor: 'var(--panel)',
          paddingBottom: 'env(safe-area-inset-bottom)',
        }}
      >
        <div className="mx-auto grid max-w-md grid-cols-3">
          {NAV.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.label}
                onClick={() => handleNav(item)}
                className="flex min-h-[56px] flex-col items-center justify-center gap-1 py-2 text-[11px] text-mut transition-colors active:text-brand"
              >
                <Icon size={18} />
                {item.label}
              </button>
            )
          })}
        </div>
      </nav>

      <SettingsModal
        open={settingsOpen}
        user={user}
        onClose={() => setSettingsOpen(false)}
        onSaveProfile={saveProfile}
        onSavePreferences={savePreferences}
        onSignOut={signOut}
        onClearData={clearData}
        tripsCount={trips.length}
      />
    </div>
  )
}

function PrefRow({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-subtle py-1.5 text-[13px] last:border-0">
      <dt className="text-mut">{label}</dt>
      <dd className="font-medium text-soft">{value}</dd>
    </div>
  )
}

import { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Search,
  Star,
  Calendar,
  User,
  Plus,
  ArrowRight,
  Compass,
  MapPin,
  RefreshCw,
  Sparkles,
  Heart,
  Edit3,
  X,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar.jsx'
import { recommend } from '../lib/recommend.js'
import { getUser, clearUser, saveUser } from '../lib/userStore.js'
import { api, getToken, clearToken, resolveImageUrl } from '../services/api.js'
import { useTripImages } from '../hooks/useTripImages.js'
import { useSidebar } from '../hooks/useSidebar.js'

export default function Dashboard() {
  const navigate = useNavigate()
  const sidebarCollapsed = useSidebar()

  const [user, setUser] = useState(() => getUser())
  const [trips, setTrips] = useState([])
  const [dests, setDests] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [reload, setReload] = useState(0)

  // Search & filter states
  const [searchQuery, setSearchQuery] = useState('')
  const [travelDate, setTravelDate] = useState('')
  const [selectedTag, setSelectedTag] = useState('All')
  const [favorites, setFavorites] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('trip_favorites') || '[]')
    } catch {
      return []
    }
  })

  // Edit trip modal state
  const [editingTrip, setEditingTrip] = useState(null)
  const [editForm, setEditForm] = useState({
    destination: '',
    start_date: '',
    end_date: '',
    budget: 1000,
    travelers: 1,
  })
  const [savingEdit, setSavingEdit] = useState(false)
  const [editError, setEditError] = useState('')

  const openEditModal = (trip) => {
    setEditingTrip(trip)
    setEditForm({
      destination: trip.destination || '',
      start_date: trip.start_date || '',
      end_date: trip.end_date || '',
      budget: trip.budget || 1000,
      travelers: trip.travelers || 1,
    })
    setEditError('')
  }

  const handleSaveEdit = async (e) => {
    e.preventDefault()
    setSavingEdit(true)
    setEditError('')
    try {
      const updated = await api.updateTrip(editingTrip.id, editForm, getToken())
      setTrips((prev) => prev.map((t) => (t.id === updated.id ? updated : t)))
      setEditingTrip(null)
    } catch (err) {
      setEditError(err.message || 'Failed to update trip.')
    } finally {
      setSavingEdit(false)
    }
  }

  const firstName = user?.name?.trim().split(/\s+/)[0] || 'Traveler'

  const prefs = user?.preferences

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

  const toggleFavorite = (e, destId) => {
    e.stopPropagation()
    setFavorites((prev) => {
      const next = prev.includes(destId)
        ? prev.filter((id) => id !== destId)
        : [...prev, destId]
      try {
        localStorage.setItem('trip_favorites', JSON.stringify(next))
      } catch {}
      return next
    })
  }

  const { picks, personalized } = useMemo(() => {
    return recommend(dests, prefs)
  }, [dests, prefs])

  // Extract all unique category tags from destinations
  const tagsList = useMemo(() => {
    const set = new Set(['All'])
    dests.forEach((d) => (d.tags || []).forEach((t) => set.add(t)))
    return Array.from(set).slice(0, 8)
  }, [dests])

  // Filtered destinations based on search query and category tag
  const filteredDests = useMemo(() => {
    return picks.filter((d) => {
      const matchSearch =
        !searchQuery ||
        d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (d.tags || []).some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
      const matchTag =
        selectedTag === 'All' ||
        (d.tags || []).some((t) => t.toLowerCase() === selectedTag.toLowerCase())
      return matchSearch && matchTag
    })
  }, [picks, searchQuery, selectedTag])

  const tripImages = useTripImages(trips.map((t) => t.destination))
  const imageFor = (name) =>
    tripImages.get(name)?.url || resolveImageUrl('/images/hero.jpg')

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/create-trip?destination=${encodeURIComponent(searchQuery)}`)
    } else {
      navigate('/create-trip')
    }
  }

  return (
    <div className="min-h-screen w-full flex bg-[#f8fafc]">
      {/* Reusable Collapsible Sidebar */}
      <Sidebar activeNav="Home" />

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
          sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
        }`}
      >
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {/* Error Banner */}
          {loadError && (
            <div className="mb-6 flex items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-[13px] text-amber-800 shadow-xs">
              <span>Could not load latest travel data: {loadError}</span>
              <button
                onClick={() => {
                  setLoadError('')
                  setLoading(true)
                  setReload((r) => r + 1)
                }}
                className="inline-flex shrink-0 items-center gap-1 font-semibold underline underline-offset-2 hover:text-amber-950"
              >
                <RefreshCw size={13} /> Retry
              </button>
            </div>
          )}

          {/* ============================================================
              1. HERO LANDING SECTION
              - Full destination photography background
              - Dark gradient overlay for clear contrast
              - "Your Next Adventure Starts Here" headline
              - "Plan a New Trip" CTA button
              - Compact search bar for destination & dates
              ============================================================ */}
          <section className="relative mb-8 overflow-hidden rounded-3xl shadow-lg">
            {/* Background Image */}
            <img
              src={resolveImageUrl('/images/hero.jpg')}
              alt="Travel Adventure"
              className="absolute inset-0 h-full w-full object-cover object-center"
            />

            {/* Dark Gradient Overlay for Maximum Readability */}
            <div
              className="absolute inset-0"
              style={{
                background:
                  'linear-gradient(135deg, rgba(15, 23, 42, 0.90) 0%, rgba(15, 23, 42, 0.65) 55%, rgba(30, 27, 75, 0.50) 100%)',
              }}
            />

            {/* Content Container */}
            <div className="relative z-10 flex min-h-[380px] sm:min-h-[420px] flex-col justify-between p-6 sm:p-10 lg:p-12">
              <div className="flex items-start justify-between gap-4">
                <div className="max-w-xl">
                  {/* Eyebrow badge */}
                  <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3.5 py-1 text-[11px] font-semibold tracking-wider uppercase text-white/90 backdrop-blur-md mb-4">
                    <Compass size={13} className="text-violet-300" />
                    <span>EXPLORE · PLAN · TRAVEL</span>
                  </div>

                  {/* Prominent Headline */}
                  <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-[1.1]">
                    Your Next Adventure Starts Here
                  </h1>

                  {/* Supporting text */}
                  <p className="mt-3.5 text-sm sm:text-base leading-relaxed text-slate-200/90 max-w-md">
                    Personalized trip recommendations, intelligent budget allocations, and day-by-day itineraries tailored to your style.
                  </p>

                  {/* Primary CTA */}
                  <div className="mt-6 flex flex-wrap items-center gap-3">
                    <Link
                      to="/create-trip"
                      className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold text-white shadow-md transition-all duration-150 hover:opacity-95 hover:shadow-lg active:scale-[0.98]"
                      style={{
                        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                      }}
                    >
                      <Plus size={16} />
                      Plan a New Trip
                      <ArrowRight size={15} />
                    </Link>

                    <Link
                      to="/trips"
                      className="inline-flex items-center gap-2 rounded-xl border border-white/30 bg-white/10 px-4 py-3 text-sm font-medium text-white backdrop-blur-md transition-colors hover:bg-white/20"
                    >
                      View My Trips ({trips.length})
                    </Link>
                  </div>
                </div>

                {/* Profile Pill badge */}
                <div className="hidden sm:flex items-center gap-3 rounded-2xl border border-white/15 bg-white/10 px-4 py-2.5 backdrop-blur-md">
                  <div
                    className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-sm font-bold text-white shadow-xs"
                    style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
                  >
                    {firstName.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="text-left text-white">
                    <p className="text-xs font-semibold leading-tight">{user?.name || 'Traveler'}</p>
                    <p className="text-[11px] text-white/70">
                      {personalized ? 'Profile Personalized' : 'Member'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Compact Search Bar */}
              <form onSubmit={handleSearchSubmit} className="mt-8 max-w-xl">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 rounded-2xl sm:rounded-full bg-white/95 p-2 shadow-2xl backdrop-blur-xl border border-white/40">
                  {/* Destination Input */}
                  <div className="flex flex-1 items-center gap-2.5 px-3 py-1.5">
                    <MapPin size={17} className="text-violet-600 shrink-0" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Where do you want to go?"
                      className="w-full bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none"
                    />
                  </div>

                  <div className="hidden sm:block h-6 w-px bg-slate-200" />

                  {/* Dates selector input */}
                  <div className="flex items-center gap-2 px-3 py-1.5 sm:w-44">
                    <Calendar size={16} className="text-slate-400 shrink-0" />
                    <input
                      type="text"
                      value={travelDate}
                      onChange={(e) => setTravelDate(e.target.value)}
                      placeholder="Travel dates?"
                      className="w-full bg-transparent text-xs text-slate-700 placeholder-slate-400 outline-none"
                    />
                  </div>

                  {/* Search submit button */}
                  <button
                    type="submit"
                    className="flex items-center justify-center gap-2 rounded-xl sm:rounded-full px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition-transform active:scale-95"
                    style={{
                      background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                    }}
                  >
                    <Search size={14} />
                    <span>Search</span>
                  </button>
                </div>
              </form>
            </div>
          </section>

          {/* ============================================================
              2. UPCOMING / RECENT TRIPS SECTION (Application Data)
              ============================================================ */}
          {trips.length > 0 && (
            <section className="mb-10">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                    Your Planned Trips
                  </h2>
                  <p className="text-xs text-slate-500">
                    Upcoming and active itineraries saved to your account.
                  </p>
                </div>
                <Link
                  to="/trips"
                  className="text-xs font-semibold text-violet-600 hover:text-violet-700 hover:underline flex items-center gap-1"
                >
                  View all ({trips.length}) <ArrowRight size={13} />
                </Link>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {trips.slice(0, 3).map((trip) => {
                  const img = imageFor(trip.destination)
                  const nights =
                    trip.start_date && trip.end_date
                      ? Math.max(
                          0,
                          Math.round(
                            (new Date(trip.end_date) - new Date(trip.start_date)) / 86400000
                          )
                        )
                      : 0
                  return (
                    <article
                      key={trip.id}
                      onClick={() => navigate(`/trips/${trip.id}`)}
                      className="group cursor-pointer overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
                    >
                      <div className="relative h-40 w-full overflow-hidden bg-slate-100">
                        <img
                          src={img}
                          alt={trip.destination}
                          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-black/20" />
                        <span className="absolute top-3 right-3 rounded-full bg-white/95 px-2.5 py-1 text-[10px] font-bold tracking-wide uppercase text-violet-700 shadow-xs backdrop-blur-md">
                          {trip.status || 'Planned'}
                        </span>
                        <div className="absolute inset-x-3 bottom-3 text-white">
                          <h3 className="text-base font-bold truncate drop-shadow-xs">
                            {trip.destination}
                          </h3>
                        </div>
                      </div>

                      <div className="p-4">
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                          <Calendar size={13} className="text-slate-400" />
                          <span>
                            {trip.start_date
                              ? new Date(trip.start_date).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                })
                              : 'TBD'}{' '}
                            –{' '}
                            {trip.end_date
                              ? new Date(trip.end_date).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                })
                              : 'TBD'}
                          </span>
                        </div>

                        <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                          <span className="flex items-center gap-1.5 text-slate-600">
                            <User size={13} className="text-slate-400" />
                            {trip.travelers} traveler{trip.travelers > 1 ? 's' : ''}
                          </span>
                          {nights > 0 && (
                            <span className="font-medium text-slate-500">
                              {nights} night{nights > 1 ? 's' : ''}
                            </span>
                          )}
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                openEditModal(trip)
                              }}
                              className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-violet-600 transition-colors"
                              title="Edit trip"
                            >
                              <Edit3 size={11} />
                              Edit
                            </button>
                            <span className="font-semibold text-violet-600 group-hover:underline">
                              Details →
                            </span>
                          </div>
                        </div>
                      </div>
                    </article>
                  )
                })}
              </div>
            </section>
          )}

          {/* ============================================================
              3. DESTINATIONS & RECOMMENDATIONS SECTION
              - Category filter pills
              - Grid of high-res destination cards
              - Star ratings & blurbs
              - Direct "Plan Trip" button
              ============================================================ */}
          <section className="mb-12">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                    {personalized ? 'Recommended for You' : 'Popular Destinations'}
                  </h2>
                  {personalized && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-violet-100 px-2.5 py-0.5 text-[11px] font-semibold text-violet-700">
                      <Sparkles size={11} /> Matched
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {personalized
                    ? 'Hand-picked based on your travel style, pace, and interests.'
                    : 'Explore top-rated travel destinations worldwide.'}
                </p>
              </div>

              {/* Category Filter Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                {tagsList.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => setSelectedTag(tag)}
                    className={`rounded-full px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                      selectedTag === tag
                        ? 'bg-violet-600 text-white shadow-xs'
                        : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {tag.charAt(0).toUpperCase() + tag.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-72 animate-pulse rounded-2xl bg-slate-200/70"
                  />
                ))}
              </div>
            ) : filteredDests.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center">
                <Compass size={28} className="mx-auto text-slate-400 mb-2" />
                <p className="text-sm font-semibold text-slate-700">No destinations match your criteria</p>
                <p className="text-xs text-slate-500 mt-1">Try clearing your search query or selecting a different tag.</p>
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('')
                    setSelectedTag('All')
                  }}
                  className="mt-3 text-xs font-semibold text-violet-600 underline"
                >
                  Reset filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                {filteredDests.map((d, idx) => {
                  const rating = (4.5 + (idx % 5) * 0.1).toFixed(1)
                  const isFav = favorites.includes(d.id)
                  return (
                    <div
                      key={d.id}
                      onClick={() =>
                        navigate(`/create-trip?destination=${encodeURIComponent(d.name)}`)
                      }
                      className="group cursor-pointer flex flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
                    >
                      {/* Destination Image */}
                      <div className="relative h-48 w-full overflow-hidden bg-slate-100">
                        <img
                          src={resolveImageUrl(d.image_url)}
                          alt={d.name}
                          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-108"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-black/20" />

                        {/* Favorite button */}
                        <button
                          type="button"
                          onClick={(e) => toggleFavorite(e, d.id)}
                          className={`absolute top-3 right-3 grid h-8 w-8 place-items-center rounded-full backdrop-blur-md transition-colors ${
                            isFav
                              ? 'bg-rose-500 text-white'
                              : 'bg-white/80 text-slate-700 hover:bg-white'
                          }`}
                        >
                          <Heart size={14} fill={isFav ? 'currentColor' : 'none'} />
                        </button>

                        {/* Rating pill */}
                        <span className="absolute bottom-3 left-3 flex items-center gap-1 rounded-full bg-white/95 px-2.5 py-1 text-xs font-bold text-slate-800 shadow-xs backdrop-blur-md">
                          <Star size={11} className="text-amber-500 fill-amber-500" />
                          {rating}
                        </span>
                      </div>

                      {/* Destination Body */}
                      <div className="flex flex-1 flex-col justify-between p-4">
                        <div>
                          <div className="flex items-baseline justify-between gap-2">
                            <h3 className="font-bold text-slate-900 group-hover:text-violet-600 transition-colors">
                              {d.name}
                            </h3>
                            <span className="text-[11px] font-medium text-slate-400">
                              {d.country}
                            </span>
                          </div>

                          <p className="mt-1 text-xs text-slate-500 line-clamp-2 leading-relaxed">
                            {d.blurb || 'Discover historic sights, local flavors, and memorable experiences.'}
                          </p>

                          {/* Tags */}
                          {d.tags && d.tags.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-1">
                              {d.tags.slice(0, 3).map((tag) => (
                                <span
                                  key={tag}
                                  className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Card action */}
                        <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                          <span className="text-xs font-semibold text-slate-700">
                            {d.price || 'From $850'}
                          </span>
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-violet-600 group-hover:translate-x-0.5 transition-transform">
                            Plan trip <ArrowRight size={12} />
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </section>
        </div>

        {/* Dashboard Edit Trip Modal */}
        {editingTrip && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-xs animate-fade-in">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                    <Edit3 size={15} />
                  </div>
                  <h3 className="text-sm font-bold text-slate-900">Edit Trip</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setEditingTrip(null)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X size={16} />
                </button>
              </div>

              <form onSubmit={handleSaveEdit} className="space-y-3.5">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Destination
                  </label>
                  <input
                    type="text"
                    required
                    value={editForm.destination}
                    onChange={(e) =>
                      setEditForm((prev) => ({ ...prev, destination: e.target.value }))
                    }
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      required
                      value={editForm.start_date}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, start_date: e.target.value }))
                      }
                      className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      required
                      value={editForm.end_date}
                      onChange={(e) =>
                        setEditForm((prev) => ({ ...prev, end_date: e.target.value }))
                      }
                      className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Travelers
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={editForm.travelers}
                      onChange={(e) =>
                        setEditForm((prev) => ({
                          ...prev,
                          travelers: Math.max(1, parseInt(e.target.value) || 1),
                        }))
                      }
                      className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Budget ($ USD)
                    </label>
                    <input
                      type="number"
                      min={0}
                      step={50}
                      value={editForm.budget}
                      onChange={(e) =>
                        setEditForm((prev) => ({
                          ...prev,
                          budget: Math.max(0, parseInt(e.target.value) || 0),
                        }))
                      }
                      className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                </div>

                {editError && (
                  <p className="text-xs text-rose-600 font-medium">{editError}</p>
                )}

                <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setEditingTrip(null)}
                    className="rounded-xl border border-slate-200 px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingEdit}
                    className="rounded-xl bg-violet-600 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-violet-700 disabled:opacity-50"
                  >
                    {savingEdit ? 'Saving…' : 'Save Changes'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}


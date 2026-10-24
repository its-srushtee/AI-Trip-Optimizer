import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Calendar,
  Users,
  DollarSign,
  MapPin,
  Clock,
  Sparkles,
  Edit3,
  Trash2,
  Share2,
  Check,
  Compass,
  Plane,
  Hotel,
  Utensils,
  Activity,
  Layers,
  Info,
  Shield,
  Heart,
  Camera,
  RefreshCw,
  Sun,
  Moon,
  Coffee,
  Sunset,
  Sunrise,
  Map as MapIcon,
  List,
  Star,
  Luggage,
  AlertCircle,
  X,
  ExternalLink,
} from 'lucide-react'
import Sidebar from '../components/common/Sidebar.jsx'
import { useSidebar } from '../hooks/useSidebar.js'
import { api, getToken, clearToken, resolveImageUrl } from '../services/api.js'
import { clearUser } from '../lib/userStore.js'
import { INTERESTS } from '../lib/constants.js'

const TABS = [
  { id: 'overview', label: 'Overview', icon: Compass },
  { id: 'itinerary', label: 'Itinerary', icon: Calendar },
  { id: 'places', label: 'Places to Visit', icon: MapPin },
  { id: 'map', label: 'Map', icon: MapIcon },
  { id: 'flights_stay', label: 'Flights & Stay', icon: Plane },
  { id: 'budget', label: 'Budget', icon: DollarSign },
]

export default function TripDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const sidebarCollapsed = useSidebar()

  const [trip, setTrip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  // Destination image & catalogue
  const [heroImage, setHeroImage] = useState(resolveImageUrl('/images/hero.jpg'))

  // AI-generated itinerary and multi-agent plan
  const [itinerary, setItinerary] = useState(null)
  const [optimizing, setOptimizing] = useState(false)
  const [optimizeError, setOptimizeError] = useState('')

  // Edit trip modal state
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({
    destination: '',
    start_date: '',
    end_date: '',
    budget: 1000,
    travelers: 1,
    interests: [],
  })
  const [savingEdit, setSavingEdit] = useState(false)
  const [editError, setEditError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Places filter
  const [placeCategory, setPlaceCategory] = useState('All')
  const [selectedDayIndex, setSelectedDayIndex] = useState(null) // null = all days

  // Fetch trip details from backend
  const fetchTrip = async () => {
    const token = getToken()
    if (!token) {
      navigate('/login')
      return
    }
    setLoading(true)
    setLoadError('')
    try {
      const data = await api.getTrip(id, token)
      setTrip(data)
      setEditForm({
        destination: data.destination || '',
        start_date: data.start_date || '',
        end_date: data.end_date || '',
        budget: data.budget || 1000,
        travelers: data.travelers || 1,
        interests: Array.isArray(data.interests) ? data.interests : [],
      })

      // Fetch hero photo
      try {
        const imgRes = await api.destinationImage(data.destination)
        if (imgRes && imgRes.url) {
          setHeroImage(resolveImageUrl(imgRes.url))
        }
      } catch (e) {
        // Fallback hero
      }

      // Generate or fetch itinerary
      generatePlan(data, token)
    } catch (err) {
      if (err.status === 401) {
        clearUser()
        clearToken()
        navigate('/login')
      } else {
        setLoadError(err.message || 'Unable to load trip details.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Optimize itinerary via multi-agent workflow
  const generatePlan = async (tripData, tokenOverride) => {
    const token = tokenOverride || getToken()
    if (!tripData || !token) return
    setOptimizing(true)
    setOptimizeError('')
    try {
      const res = await api.optimize(
        {
          destination: tripData.destination,
          start_date: tripData.start_date || '2026-11-01',
          end_date: tripData.end_date || '2026-11-07',
          budget: tripData.budget || 1500,
          travelers: tripData.travelers || 1,
          interests: Array.isArray(tripData.interests) ? tripData.interests : [],
        },
        token
      )
      if (res && res.itinerary) {
        setItinerary(res.itinerary)
      }
    } catch (err) {
      setOptimizeError(err.message || 'Could not generate AI itinerary plan.')
    } finally {
      setOptimizing(false)
    }
  }

  useEffect(() => {
    fetchTrip()
  }, [id])

  // Duration in days and nights
  const duration = useMemo(() => {
    if (!trip?.start_date || !trip?.end_date) return { days: 1, nights: 0 }
    const start = new Date(trip.start_date)
    const end = new Date(trip.end_date)
    const nights = Math.max(0, Math.round((end - start) / 86400000))
    return { days: nights + 1, nights }
  }, [trip])

  // Save edited trip
  const handleSaveEdit = async (e) => {
    e.preventDefault()
    setSavingEdit(true)
    setEditError('')
    try {
      const token = getToken()
      const updated = await api.updateTrip(id, editForm, token)
      setTrip(updated)
      setSaveSuccess(true)
      setTimeout(() => {
        setSaveSuccess(false)
        setIsEditing(false)
      }, 1000)

      // Re-fetch destination image if destination changed
      if (updated.destination !== trip.destination) {
        try {
          const imgRes = await api.destinationImage(updated.destination)
          if (imgRes?.url) setHeroImage(resolveImageUrl(imgRes.url))
        } catch {}
      }

      // Re-run itinerary optimization with updated values
      generatePlan(updated, token)
    } catch (err) {
      setEditError(err.message || 'Failed to update trip.')
    } finally {
      setSavingEdit(false)
    }
  }

  // Toggle interest pill in edit form
  const toggleInterest = (interestName) => {
    const norm = interestName.toLowerCase()
    setEditForm((prev) => {
      const current = prev.interests || []
      const exists = current.some((i) => i.toLowerCase() === norm)
      return {
        ...prev,
        interests: exists
          ? current.filter((i) => i.toLowerCase() !== norm)
          : [...current, interestName],
      }
    })
  }

  // Curated places list from itinerary
  const places = useMemo(() => {
    return itinerary?.places_to_visit || []
  }, [itinerary])

  // Filtered places
  const filteredPlaces = useMemo(() => {
    if (placeCategory === 'All') return places
    return places.filter(
      (p) =>
        p.category?.toLowerCase().includes(placeCategory.toLowerCase()) ||
        p.tags?.some((t) => t.toLowerCase().includes(placeCategory.toLowerCase()))
    )
  }, [places, placeCategory])

  // Available place categories
  const categoriesList = useMemo(() => {
    const set = new Set(['All'])
    places.forEach((p) => {
      if (p.category) {
        const clean = p.category.split('&')[0].trim()
        set.add(clean)
      }
    })
    return Array.from(set)
  }, [places])

  // Map destination coordinates lookup (fallback coordinates for visual map)
  const mapCoords = useMemo(() => {
    const dest = (trip?.destination || '').toLowerCase()
    if (dest.includes('bali')) return { lat: -8.4095, lng: 115.1889, zoom: 10 }
    if (dest.includes('paris')) return { lat: 48.8566, lng: 2.3522, zoom: 12 }
    if (dest.includes('tokyo')) return { lat: 35.6762, lng: 139.6503, zoom: 11 }
    if (dest.includes('alps') || dest.includes('swiss')) return { lat: 46.5584, lng: 7.9864, zoom: 10 }
    if (dest.includes('maldives')) return { lat: 3.2028, lng: 73.2207, zoom: 10 }
    if (dest.includes('goa')) return { lat: 15.2993, lng: 74.124, zoom: 10 }
    if (dest.includes('thailand') || dest.includes('bangkok')) return { lat: 13.7563, lng: 100.5018, zoom: 11 }
    if (dest.includes('rome')) return { lat: 41.9028, lng: 12.4964, zoom: 12 }
    if (dest.includes('kyoto')) return { lat: 35.0116, lng: 135.7681, zoom: 12 }
    return { lat: 48.8566, lng: 2.3522, zoom: 11 }
  }, [trip?.destination])

  if (loading) {
    return (
      <div className="min-h-screen w-full flex bg-slate-50">
        <Sidebar activeNav="My Trips" />
        <main
          className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
            sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
          }`}
        >
          <div className="flex flex-col items-center justify-center min-h-[70vh] p-6 text-center">
            <div className="h-14 w-14 rounded-2xl bg-violet-100 flex items-center justify-center animate-pulse mb-4 text-violet-600">
              <Compass size={28} className="animate-spin" />
            </div>
            <h2 className="text-xl font-bold text-slate-800">Loading trip details…</h2>
            <p className="text-sm text-slate-500 mt-1 max-w-sm">
              Retrieving your itinerary, attractions, and destination intelligence.
            </p>
          </div>
        </main>
      </div>
    )
  }

  if (loadError || !trip) {
    return (
      <div className="min-h-screen w-full flex bg-slate-50">
        <Sidebar activeNav="My Trips" />
        <main
          className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
            sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
          }`}
        >
          <div className="mx-auto max-w-2xl px-4 py-16 text-center">
            <div className="mx-auto h-16 w-16 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center mb-4">
              <AlertCircle size={32} />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Trip Not Found</h1>
            <p className="text-sm text-slate-500 mt-2 mb-6">
              {loadError || 'The requested trip could not be found or was deleted.'}
            </p>
            <Link
              to="/trips"
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 transition-colors shadow-sm"
            >
              <ArrowLeft size={16} /> Back to My Trips
            </Link>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full flex bg-slate-50">
      {/* Collapsible Sidebar */}
      <Sidebar activeNav="My Trips" />

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
          sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
        }`}
      >
        {/* ============================================================
            1. LARGE DESTINATION HERO SECTION
            ============================================================ */}
        <section className="relative w-full overflow-hidden min-h-[380px] sm:min-h-[440px] lg:min-h-[480px] flex flex-col justify-between bg-slate-900 text-white">
          {/* Scenic Full-Width Destination Photograph */}
          <img
            src={heroImage}
            alt={trip.destination}
            className="absolute inset-0 h-full w-full object-cover object-center transition-transform duration-700 ease-out"
          />

          {/* Dark Gradient Overlay for Maximum Readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/65 to-black/35 backdrop-blur-[0.5px]" />

          {/* Top Hero Bar (Back Button + Actions) */}
          <div className="relative z-10 mx-auto w-full max-w-7xl px-4 pt-6 sm:px-6 lg:px-8 flex items-center justify-between">
            <Link
              to="/trips"
              className="inline-flex items-center gap-2 rounded-full bg-white/20 px-3.5 py-1.5 text-xs font-semibold text-white backdrop-blur-md transition-all hover:bg-white/30 active:scale-95 border border-white/20"
            >
              <ArrowLeft size={14} />
              <span>Back to Trips</span>
            </Link>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => generatePlan(trip)}
                disabled={optimizing}
                className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-white/20 px-3.5 py-1.5 text-xs font-semibold text-white backdrop-blur-md transition-all hover:bg-white/30 border border-white/20 active:scale-95 disabled:opacity-50"
                title="Regenerate with AI"
              >
                <Sparkles size={14} className={optimizing ? 'animate-spin' : ''} />
                <span>{optimizing ? 'Generating…' : 'Refresh AI Plan'}</span>
              </button>

              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="inline-flex items-center gap-1.5 rounded-full bg-violet-600 hover:bg-violet-700 px-4 py-1.5 text-xs font-semibold text-white shadow-md transition-all active:scale-95 border border-violet-400/40"
              >
                <Edit3 size={14} />
                <span>Edit Trip</span>
              </button>
            </div>
          </div>

          {/* Bottom Hero Content: Title, Dates, Travelers, Badges */}
          <div className="relative z-10 mx-auto w-full max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
            <div className="max-w-3xl">
              {/* Trip Status Badge */}
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-0.5 text-[11px] font-bold uppercase tracking-wider backdrop-blur-md">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {trip.status || 'Active Journey'}
                </span>
                <span className="inline-flex items-center gap-1 text-[12px] font-medium text-slate-300">
                  <Clock size={13} className="text-violet-400" />
                  {duration.days} Days / {duration.nights} Nights
                </span>
              </div>

              {/* Destination Name */}
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight drop-shadow-md">
                {trip.destination}
              </h1>

              {/* Supporting Subtitle / AI Note */}
              <p className="mt-2 text-sm sm:text-base text-slate-200 line-clamp-2 max-w-2xl font-normal drop-shadow-xs">
                {itinerary?.summary ||
                  `Personalized travel plan for ${trip.travelers} traveler${trip.travelers > 1 ? 's' : ''} with a focus on ${trip.interests?.join(', ') || 'sights & local culture'}.`}
              </p>

              {/* Meta Pills (Dates, Travelers, Budget) */}
              <div className="mt-5 flex flex-wrap items-center gap-2.5">
                <div className="flex items-center gap-2 rounded-xl bg-white/15 px-3.5 py-1.5 text-xs font-medium text-white backdrop-blur-md border border-white/15">
                  <Calendar size={14} className="text-violet-300" />
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

                <div className="flex items-center gap-2 rounded-xl bg-white/15 px-3.5 py-1.5 text-xs font-medium text-white backdrop-blur-md border border-white/15">
                  <Users size={14} className="text-blue-300" />
                  <span>
                    {trip.travelers} Traveler{trip.travelers > 1 ? 's' : ''}
                  </span>
                </div>

                <div className="flex items-center gap-2 rounded-xl bg-white/15 px-3.5 py-1.5 text-xs font-medium text-white backdrop-blur-md border border-white/15">
                  <DollarSign size={14} className="text-emerald-300" />
                  <span>${trip.budget?.toLocaleString()} Budget</span>
                </div>

                {trip.interests && trip.interests.length > 0 && (
                  <div className="hidden sm:flex items-center gap-1.5">
                    {trip.interests.slice(0, 3).map((int) => (
                      <span
                        key={int}
                        className="rounded-lg bg-violet-500/25 px-2.5 py-1 text-[11px] font-semibold text-violet-200 border border-violet-400/30 backdrop-blur-sm capitalize"
                      >
                        {int}
                      </span>
                    ))}
                    {trip.interests.length > 3 && (
                      <span className="text-[11px] text-slate-300">
                        +{trip.interests.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* ============================================================
            2. NAVIGATION TABS BAR
            ============================================================ */}
        <div className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto py-2 scrollbar-none" aria-label="Trip Tabs">
              {TABS.map((tab) => {
                const Icon = tab.icon
                const active = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3.5 py-2 text-xs font-semibold transition-all duration-150 ${
                      active
                        ? 'bg-violet-600 text-white shadow-xs'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`}
                  >
                    <Icon size={15} />
                    <span>{tab.label}</span>
                    {tab.id === 'itinerary' && itinerary?.days?.length > 0 && (
                      <span
                        className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                          active ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'
                        }`}
                      >
                        {itinerary.days.length}d
                      </span>
                    )}
                    {tab.id === 'places' && places.length > 0 && (
                      <span
                        className={`ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                          active ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-700'
                        }`}
                      >
                        {places.length}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>
        </div>

        {/* ============================================================
            MAIN TAB PANELS CONTAINER
            ============================================================ */}
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-8 animate-fade-in">
              {/* Stat Cards Grid */}
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Duration
                    </span>
                    <Clock size={18} className="text-violet-600" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 tracking-tight">
                    {duration.days} Days
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {duration.nights} night{duration.nights > 1 ? 's' : ''} stay
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Travelers
                    </span>
                    <Users size={18} className="text-blue-600" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 tracking-tight">
                    {trip.travelers} Guest{trip.travelers > 1 ? 's' : ''}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {trip.travelers === 1 ? 'Solo Trip' : trip.travelers === 2 ? 'Couple / Duo' : 'Group Adventure'}
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Est. Budget
                    </span>
                    <DollarSign size={18} className="text-emerald-600" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 tracking-tight">
                    ${trip.budget?.toLocaleString()}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    ~${Math.round(trip.budget / Math.max(1, duration.days))}/day
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Pace & Style
                    </span>
                    <Compass size={18} className="text-amber-600" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900 tracking-tight">
                    Balanced
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Comfort & Discovery
                  </p>
                </div>
              </div>

              {/* Two Column Section: Destination Blurb + Travel Preferences */}
              <div className="grid gap-6 lg:grid-cols-3">
                {/* Destination Spotlight (2 cols) */}
                <div className="lg:col-span-2 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                        <MapPin size={17} />
                      </div>
                      <h2 className="text-base font-bold text-slate-900">
                        About {trip.destination}
                      </h2>
                    </div>
                    <span className="text-xs text-slate-500">Travel Guide</span>
                  </div>

                  <p className="text-sm text-slate-600 leading-relaxed">
                    {itinerary?.summary ||
                      `${trip.destination} offers stunning scenery, vibrant local culture, and memorable activities tailored to your itinerary. Whether exploring historical landmarks or enjoying regional gastronomy, your trip is set up for an unforgettable journey.`}
                  </p>

                  {/* Highlights Bullet List from Agent */}
                  <div className="mt-5 grid sm:grid-cols-2 gap-3">
                    <div className="flex items-start gap-2.5 rounded-xl bg-slate-50 p-3">
                      <Check size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <h3 className="text-xs font-semibold text-slate-800">
                          Handpicked Experiences
                        </h3>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Activities organized by morning, afternoon, and evening to maximize time.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2.5 rounded-xl bg-slate-50 p-3">
                      <Check size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <h3 className="text-xs font-semibold text-slate-800">
                          Budget Tracking
                        </h3>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Calculated cost distribution across stay, flights, dining, and activities.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Quick CTAs */}
                  <div className="mt-6 flex flex-wrap gap-3">
                    <button
                      onClick={() => setActiveTab('itinerary')}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-violet-700 transition-colors"
                    >
                      <Calendar size={14} /> View Day-by-Day Plan
                    </button>
                    <button
                      onClick={() => setActiveTab('places')}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors"
                    >
                      <MapPin size={14} /> Recommended Attractions ({places.length})
                    </button>
                  </div>
                </div>

                {/* Selected Travel Preferences (1 col) */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-2 border-b border-slate-100 pb-4 mb-4">
                      <div className="h-8 w-8 rounded-lg bg-pink-50 text-pink-600 flex items-center justify-center">
                        <Heart size={17} />
                      </div>
                      <h2 className="text-base font-bold text-slate-900">
                        Trip Preferences
                      </h2>
                    </div>

                    <p className="text-xs text-slate-500 mb-4">
                      Your travel interests shape the activities and attractions suggested for this journey.
                    </p>

                    <div className="flex flex-wrap gap-2">
                      {trip.interests && trip.interests.length > 0 ? (
                        trip.interests.map((int) => (
                          <span
                            key={int}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700 border border-violet-100 capitalize"
                          >
                            <Sparkles size={12} className="text-violet-500" />
                            {int}
                          </span>
                        ))
                      ) : (
                        <p className="text-xs text-slate-400 italic">
                          No specific interests chosen. Sights & culture default selected.
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-100">
                    <button
                      onClick={() => setIsEditing(true)}
                      className="w-full flex items-center justify-center gap-2 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                    >
                      <Edit3 size={13} /> Edit Preferences & Details
                    </button>
                  </div>
                </div>
              </div>

              {/* Transport & Local Tips Card */}
              {itinerary?.transport?.guidelines && (
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                  <div className="flex items-center gap-2 mb-3">
                    <Luggage size={17} className="text-blue-600" />
                    <h3 className="text-sm font-bold text-slate-900">
                      Local Transport & Travel Guidelines
                    </h3>
                  </div>
                  <div className="grid sm:grid-cols-3 gap-3">
                    {itinerary.transport.guidelines.map((guide, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-slate-100 bg-slate-50/70 p-3 text-xs text-slate-600"
                      >
                        <span className="font-semibold text-slate-800">Tip #{i + 1}:</span>{' '}
                        {guide}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DATE-WISE ITINERARY */}
          {activeTab === 'itinerary' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                    Date-Wise Itinerary Plan
                  </h2>
                  <p className="text-xs text-slate-500">
                    Day-by-day morning, afternoon, and evening activities tailored to your preferences.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => generatePlan(trip)}
                    disabled={optimizing}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-violet-50 text-violet-700 px-3 py-1.5 text-xs font-semibold hover:bg-violet-100 transition-colors border border-violet-100"
                  >
                    <RefreshCw size={13} className={optimizing ? 'animate-spin' : ''} />
                    <span>{optimizing ? 'Optimizing…' : 'Regenerate Itinerary'}</span>
                  </button>
                </div>
              </div>

              {/* Day filter pills */}
              {itinerary?.days && itinerary.days.length > 1 && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                  <button
                    onClick={() => setSelectedDayIndex(null)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                      selectedDayIndex === null
                        ? 'bg-slate-900 text-white'
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    All Days ({itinerary.days.length})
                  </button>
                  {itinerary.days.map((d, idx) => (
                    <button
                      key={d.day}
                      onClick={() => setSelectedDayIndex(idx)}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                        selectedDayIndex === idx
                          ? 'bg-violet-600 text-white shadow-xs'
                          : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      Day {d.day}
                    </button>
                  ))}
                </div>
              )}

              {/* Loading State */}
              {optimizing && !itinerary && (
                <div className="space-y-4">
                  {[1, 2, 3].map((n) => (
                    <div
                      key={n}
                      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs animate-pulse"
                    >
                      <div className="h-5 w-40 bg-slate-200 rounded mb-4" />
                      <div className="space-y-2">
                        <div className="h-4 w-full bg-slate-100 rounded" />
                        <div className="h-4 w-3/4 bg-slate-100 rounded" />
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Error State */}
              {optimizeError && (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700 flex items-center justify-between">
                  <span>{optimizeError}</span>
                  <button
                    onClick={() => generatePlan(trip)}
                    className="font-bold underline ml-2"
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* Days List / Timeline */}
              {itinerary?.days && itinerary.days.length > 0 ? (
                <div className="space-y-6">
                  {itinerary.days
                    .filter((_, idx) => selectedDayIndex === null || selectedDayIndex === idx)
                    .map((day) => (
                      <article
                        key={day.day}
                        className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-shadow hover:shadow-md"
                      >
                        {/* Day Card Header */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 bg-slate-50/70 px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-600 text-xs font-bold text-white shadow-xs">
                              {day.day}
                            </span>
                            <div>
                              <h3 className="text-sm font-bold text-slate-900">
                                Day {day.day}: {day.theme || 'Exploration & Sights'}
                              </h3>
                              <p className="text-[11px] text-slate-500">
                                {day.date
                                  ? new Date(day.date).toLocaleDateString('en-US', {
                                      weekday: 'long',
                                      month: 'short',
                                      day: 'numeric',
                                    })
                                  : `Day ${day.day}`}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 text-xs">
                            <span className="rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 font-medium">
                              Est. ${day.estimate_usd || Math.round(trip.budget / duration.days)}
                            </span>
                            <span className="text-slate-400">·</span>
                            <span className="text-slate-500 truncate max-w-[180px]">
                              {day.stay || `Stay in ${trip.destination}`}
                            </span>
                          </div>
                        </div>

                        {/* Day Content Body */}
                        <div className="p-5 sm:p-6 space-y-5">
                          {/* Day summary/description if present */}
                          {day.description && (
                            <p className="text-xs text-slate-600 italic border-l-2 border-violet-400 pl-3">
                              {day.description}
                            </p>
                          )}

                          {/* 3 Activities Blocks: Morning, Afternoon, Evening */}
                          <div className="grid gap-3.5 sm:grid-cols-3">
                            {/* Morning Block */}
                            <div className="rounded-xl border border-amber-100 bg-amber-50/40 p-4">
                              <div className="flex items-center gap-2 text-amber-700 mb-2">
                                <Sunrise size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">
                                  Morning
                                </span>
                              </div>
                              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                                {day.morning}
                              </p>
                            </div>

                            {/* Afternoon Block */}
                            <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-4">
                              <div className="flex items-center gap-2 text-blue-700 mb-2">
                                <Sun size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">
                                  Afternoon
                                </span>
                              </div>
                              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                                {day.afternoon}
                              </p>
                            </div>

                            {/* Evening Block */}
                            <div className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4">
                              <div className="flex items-center gap-2 text-indigo-700 mb-2">
                                <Sunset size={16} />
                                <span className="text-xs font-bold uppercase tracking-wider">
                                  Evening
                                </span>
                              </div>
                              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                                {day.evening}
                              </p>
                            </div>
                          </div>

                          {/* Suggested Places to Visit for this Day */}
                          {day.suggested_places && day.suggested_places.length > 0 && (
                            <div className="pt-2 border-t border-slate-100">
                              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                                Featured Places for Day {day.day}
                              </span>
                              <div className="flex flex-wrap gap-2">
                                {day.suggested_places.map((placeName, pi) => (
                                  <span
                                    key={pi}
                                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-3 py-1 text-xs font-medium text-slate-800 hover:bg-slate-200 transition-colors"
                                  >
                                    <MapPin size={12} className="text-violet-600" />
                                    {placeName}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </article>
                    ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
                  <Compass size={32} className="mx-auto text-slate-300 mb-2" />
                  <p className="text-sm font-semibold text-slate-700">No itinerary generated yet.</p>
                  <p className="text-xs text-slate-400 mt-1 mb-4">
                    Click the button below to generate a tailored date-wise plan.
                  </p>
                  <button
                    onClick={() => generatePlan(trip)}
                    className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-xs"
                  >
                    <Sparkles size={14} /> Generate Itinerary Now
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: PLACES TO VISIT */}
          {activeTab === 'places' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                    Recommended Places & Attractions
                  </h2>
                  <p className="text-xs text-slate-500">
                    Curated points of interest in {trip.destination}, prioritized by your selected travel preferences.
                  </p>
                </div>
              </div>

              {/* Category Filter Pills */}
              {categoriesList.length > 1 && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                  {categoriesList.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setPlaceCategory(cat)}
                      className={`rounded-full px-3.5 py-1.5 text-xs font-semibold whitespace-nowrap transition-colors ${
                        placeCategory === cat
                          ? 'bg-violet-600 text-white shadow-xs'
                          : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              )}

              {/* Places Grid */}
              {filteredPlaces.length > 0 ? (
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {filteredPlaces.map((place, idx) => {
                    const placeImg = resolveImageUrl(place.image_url || heroImage)
                    // Check if place matches any user interest
                    const matchesPreference = (trip.interests || []).some(
                      (int) =>
                        place.tags?.includes(int.toLowerCase()) ||
                        place.category?.toLowerCase().includes(int.toLowerCase())
                    )

                    return (
                      <article
                        key={idx}
                        className="group overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg flex flex-col justify-between"
                      >
                        <div>
                          {/* Image Thumbnail with Overlay */}
                          <div className="relative h-48 w-full overflow-hidden bg-slate-100">
                            <img
                              src={placeImg}
                              alt={place.name}
                              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-black/20" />

                            {/* Category Badge */}
                            <span className="absolute top-3 left-3 rounded-full bg-white/90 px-2.5 py-1 text-[10px] font-bold text-slate-800 shadow-xs backdrop-blur-md">
                              {place.category || 'Attraction'}
                            </span>

                            {/* Preference Match Badge */}
                            {matchesPreference && (
                              <span className="absolute top-3 right-3 rounded-full bg-violet-600/90 text-white px-2 py-0.5 text-[10px] font-bold shadow-xs backdrop-blur-md flex items-center gap-1">
                                <Sparkles size={10} /> Top Match
                              </span>
                            )}

                            {/* Rating on image */}
                            <div className="absolute bottom-3 right-3 flex items-center gap-1 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-bold text-amber-300 backdrop-blur-md">
                              <Star size={12} fill="currentColor" />
                              <span>{place.rating || 4.8}</span>
                            </div>

                            <div className="absolute bottom-3 left-3 text-white pr-16">
                              <h3 className="text-base font-bold drop-shadow-xs line-clamp-1">
                                {place.name}
                              </h3>
                            </div>
                          </div>

                          {/* Card Details */}
                          <div className="p-4 space-y-2.5">
                            <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                              {place.description}
                            </p>

                            <div className="flex items-center gap-1.5 text-xs text-slate-500 pt-1">
                              <MapPin size={13} className="text-violet-500 shrink-0" />
                              <span className="truncate">{place.location || trip.destination}</span>
                            </div>

                            {place.visit_info && (
                              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-50 rounded-lg p-2 border border-slate-100">
                                <Info size={12} className="text-blue-500 shrink-0" />
                                <span className="line-clamp-1">{place.visit_info}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Card Footer */}
                        <div className="p-4 pt-0">
                          <button
                            type="button"
                            onClick={() => {
                              window.open(
                                `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                                  place.name + ' ' + trip.destination
                                )}`,
                                '_blank'
                              )
                            }}
                            className="w-full flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                          >
                            <span>Explore on Map</span>
                            <ExternalLink size={12} />
                          </button>
                        </div>
                      </article>
                    )
                  })}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
                  <p className="text-sm text-slate-500">No attractions match the selected filter.</p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: MAP */}
          {activeTab === 'map' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                    Destination & Attractions Map
                  </h2>
                  <p className="text-xs text-slate-500">
                    Interactive geographic overview of {trip.destination} and points of interest.
                  </p>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                {/* Embedded Map Canvas (2 cols) */}
                <div className="lg:col-span-2 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs h-[460px] relative">
                  <iframe
                    title="Destination Map"
                    width="100%"
                    height="100%"
                    frameBorder="0"
                    scrolling="no"
                    marginHeight="0"
                    marginWidth="0"
                    src={`https://www.openstreetmap.org/export/embed.html?bbox=${
                      mapCoords.lng - 0.2
                    }%2C${mapCoords.lat - 0.2}%2C${mapCoords.lng + 0.2}%2C${
                      mapCoords.lat + 0.2
                    }&layer=mapnik&marker=${mapCoords.lat}%2C${mapCoords.lng}`}
                    className="w-full h-full border-0"
                  />
                  <div className="absolute bottom-3 right-3 bg-white/90 backdrop-blur-md rounded-lg px-2.5 py-1 text-[10px] text-slate-600 shadow-xs border border-slate-200">
                    © OpenStreetMap Contributors
                  </div>
                </div>

                {/* Places Pinpoint List (1 col) */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs overflow-y-auto max-h-[460px]">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                    Locations Marked ({places.length})
                  </h3>
                  <div className="space-y-3">
                    {places.map((p, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 rounded-xl border border-slate-100 p-2.5 hover:bg-slate-50 transition-colors"
                      >
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-violet-100 text-[11px] font-bold text-violet-700 shrink-0">
                          {i + 1}
                        </span>
                        <div className="min-w-0 flex-1">
                          <h4 className="text-xs font-bold text-slate-800 truncate">
                            {p.name}
                          </h4>
                          <p className="text-[11px] text-slate-500 truncate">
                            {p.location || trip.destination}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: FLIGHTS & STAY */}
          {activeTab === 'flights_stay' && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Flights & Accommodations
                </h2>
                <p className="text-xs text-slate-500">
                  Curated lodging options and flight guidance for {trip.destination}.
                </p>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                {/* Flights Card */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                  <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-4">
                    <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                      <Plane size={17} />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Flight Guidelines</h3>
                      <p className="text-[11px] text-slate-400">Routes & Departure Planning</p>
                    </div>
                  </div>

                  <div className="space-y-3 text-xs text-slate-600">
                    <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-slate-800">Travel Window:</span>
                        <span className="font-bold text-violet-600">
                          {trip.start_date} – {trip.end_date}
                        </span>
                      </div>
                      <p className="text-slate-500">
                        Aim for Tuesday or Wednesday departures to save an estimated 15–20% on round-trip fares.
                      </p>
                    </div>

                    <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100">
                      <h4 className="font-semibold text-slate-800 mb-1">Baggage & Transfers:</h4>
                      <p className="text-slate-500">
                        Check regional airline baggage allowances before packing. Arrange airport transfers via official kiosks upon arrival.
                      </p>
                    </div>

                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() =>
                          window.open(
                            `https://www.google.com/travel/flights?q=flights+to+${encodeURIComponent(
                              trip.destination
                            )}`,
                            '_blank'
                          )
                        }
                        className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-600 text-white py-2.5 font-semibold hover:bg-blue-700 transition-colors shadow-xs"
                      >
                        <Plane size={14} /> Search Flights on Google
                      </button>
                    </div>
                  </div>
                </div>

                {/* Stays & Accommodations Card */}
                <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                  <div className="flex items-center gap-2.5 border-b border-slate-100 pb-4 mb-4">
                    <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                      <Hotel size={17} />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Recommended Stays</h3>
                      <p className="text-[11px] text-slate-400">Curated lodging in {trip.destination}</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {/* Hotel suggestions */}
                    <div className="rounded-xl border border-slate-100 p-3.5 hover:border-violet-200 transition-colors">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-900">
                          Central Boutique Hotel & Suites
                        </h4>
                        <span className="text-xs font-bold text-emerald-600">
                          ~${Math.round(trip.budget * 0.35 / duration.nights || 120)}/nt
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Conveniently situated near major sights with complimentary breakfast, high-speed Wi-Fi, and terrace views.
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 p-3.5 hover:border-violet-200 transition-colors">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold text-slate-900">
                          Relaxation Resort & Wellness Spa
                        </h4>
                        <span className="text-xs font-bold text-emerald-600">
                          ~${Math.round((trip.budget * 0.35 / duration.nights || 120) * 1.3)}/nt
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">
                        Peaceful retreat featuring botanical gardens, outdoor pool, and restorative wellness therapies.
                      </p>
                    </div>

                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() =>
                          window.open(
                            `https://www.google.com/travel/hotels?q=hotels+in+${encodeURIComponent(
                              trip.destination
                            )}`,
                            '_blank'
                          )
                        }
                        className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-600 text-white py-2.5 font-semibold hover:bg-emerald-700 transition-colors shadow-xs"
                      >
                        <Hotel size={14} /> Search Hotels in {trip.destination}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: BUDGET */}
          {activeTab === 'budget' && (
            <div className="space-y-6 animate-fade-in">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                    Estimated Budget Breakdown
                  </h2>
                  <p className="text-xs text-slate-500">
                    Calculated financial allocation for ${trip.budget?.toLocaleString()} across {duration.days} days.
                  </p>
                </div>
              </div>

              {/* Budget Cards Grid */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500">Flights / Transit</span>
                    <Plane size={16} className="text-blue-500" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    ${Math.round(trip.budget * 0.3).toLocaleString()}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">30% of total budget</p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500">Accommodation</span>
                    <Hotel size={16} className="text-violet-500" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    ${Math.round(trip.budget * 0.35).toLocaleString()}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">35% of total budget</p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500">Food & Dining</span>
                    <Utensils size={16} className="text-amber-500" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    ${Math.round(trip.budget * 0.15).toLocaleString()}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">15% of total budget</p>
                </div>

                <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-500">Activities & Tours</span>
                    <Activity size={16} className="text-emerald-500" />
                  </div>
                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    ${Math.round(trip.budget * 0.2).toLocaleString()}
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">20% of total budget</p>
                </div>
              </div>

              {/* Visual Multi-Segment Bar */}
              <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                  Budget Allocation Bar
                </h3>
                <div className="h-4 w-full overflow-hidden rounded-full flex bg-slate-100">
                  <div style={{ width: '30%' }} className="bg-blue-500" title="Flights 30%" />
                  <div style={{ width: '35%' }} className="bg-violet-500" title="Stay 35%" />
                  <div style={{ width: '15%' }} className="bg-amber-500" title="Food 15%" />
                  <div style={{ width: '20%' }} className="bg-emerald-500" title="Activities 20%" />
                </div>

                <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <div className="h-2.5 w-2.5 rounded-full bg-blue-500" />
                    <span>Flights (30%)</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <div className="h-2.5 w-2.5 rounded-full bg-violet-500" />
                    <span>Stay (35%)</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <div className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                    <span>Food (15%)</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-600">
                    <div className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                    <span>Activities (20%)</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ============================================================
            EDIT TRIP MODAL
            ============================================================ */}
        {isEditing && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-xs animate-fade-in">
            <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                    <Edit3 size={16} />
                  </div>
                  <h3 className="text-base font-bold text-slate-900">Edit Trip Details</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleSaveEdit} className="space-y-4">
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
                    className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-sm text-slate-800 outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                    placeholder="e.g. Bali, Paris, Tokyo"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
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
                      className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
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
                      className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
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
                      className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
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
                      className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                    />
                  </div>
                </div>

                {/* Preferences Selector Chips */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    Travel Interests & Preferences
                  </label>
                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-1 border border-slate-100 rounded-xl bg-slate-50/50">
                    {INTERESTS.map((int) => {
                      const selected = (editForm.interests || []).some(
                        (i) => i.toLowerCase() === int.name.toLowerCase()
                      )
                      return (
                        <button
                          key={int.name}
                          type="button"
                          onClick={() => toggleInterest(int.name)}
                          className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-all ${
                            selected
                              ? 'bg-violet-600 text-white shadow-xs'
                              : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                          }`}
                        >
                          {int.icon} {int.name}
                        </button>
                      )
                    })}
                  </div>
                </div>

                {editError && (
                  <p className="text-xs text-rose-600 font-medium">{editError}</p>
                )}
                {saveSuccess && (
                  <p className="text-xs text-emerald-600 font-medium">✓ Changes saved successfully!</p>
                )}

                <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingEdit}
                    className="rounded-xl bg-violet-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-violet-700 disabled:opacity-50"
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

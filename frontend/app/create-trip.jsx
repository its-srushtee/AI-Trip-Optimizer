import { useState, useEffect, useMemo, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  MapPin,
  Navigation,
  Calendar,
  Users,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Check,
  CheckCircle2,
  DollarSign,
  Heart,
  Star,
  Compass,
  AlertCircle,
  Clock,
  Sliders,
  ShieldCheck,
  Info,
  Loader2,
  Search,
  Plus,
  X,
} from 'lucide-react'
import Sidebar from '../components/common/Sidebar.jsx'
import { useSidebar } from '../hooks/useSidebar.js'
import { api, getToken, resolveImageUrl } from '../services/api.js'
import { getUser } from '../lib/userStore.js'
import {
  interests as ALL_INTERESTS,
  currencyOptions,
  dietaryOptions,
  accessibilityOptions,
  travelStyles,
  tripPaces,
  getTodayDateStr,
  getNextDayDateStr,
} from '../lib/constants.js'

const STEPS = [
  { id: 1, title: 'Preferences', desc: 'Destination & Style' },
  { id: 2, title: 'Budget & Dates', desc: 'Timing & Spending' },
  { id: 3, title: 'Review', desc: 'Recommendations & Confirm' },
]

const CURRENCY_CONFIG = {
  INR: { base: 10000, step: 500, min: 10000, placeholder: 'e.g. 10000', rate: 1 },
  USD: { base: 1200, step: 50, min: 120, placeholder: 'e.g. 1200', rate: 0.012 },
  EUR: { base: 1100, step: 50, min: 110, placeholder: 'e.g. 1100', rate: 0.011 },
  GBP: { base: 950, step: 50, min: 95, placeholder: 'e.g. 950', rate: 0.0095 },
  CAD: { base: 1600, step: 50, min: 160, placeholder: 'e.g. 1600', rate: 0.016 },
  AUD: { base: 1800, step: 50, min: 180, placeholder: 'e.g. 1800', rate: 0.018 },
  JPY: { base: 180000, step: 5000, min: 18000, placeholder: 'e.g. 180000', rate: 1.8 },
}

export default function CreateTrip() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sidebarCollapsed = useSidebar()

  const user = getUser()
  const userPrefs = user?.preferences || {}

  const defaultCurrency = userPrefs.currency || 'INR'
  const defaultBudget = CURRENCY_CONFIG[defaultCurrency]?.base || 10000

  // 3-step state: 0 = Preferences, 1 = Budget & Dates, 2 = Review & Recommendations
  const [step, setStep] = useState(0)

  // Form State — preserves state across all steps
  const [form, setForm] = useState(() => ({
    origin: searchParams.get('origin') || '',
    destination: searchParams.get('destination') || '',
    start: '',
    end: '',
    budget: Math.max(defaultBudget, CURRENCY_CONFIG[defaultCurrency]?.min || 10000),
    currency: defaultCurrency,
    travelers: 2,
    selectedInterests: userPrefs.interests || ['nature', 'adventure'],
    selectedTravelOption: userPrefs.style || 'Comfort',
    travelStyle: userPrefs.style || 'Comfort',
    tripPace: userPrefs.pace || 'Moderate',
    dietary: userPrefs.food || 'No preference',
    accessibility: 'None required',
    specialRequests: '',
  }))

  // Auto-clamp budget if below minimum
  useEffect(() => {
    const minBudget = CURRENCY_CONFIG[form.currency]?.min || 10000
    if (form.budget < minBudget) {
      updateField('budget', minBudget)
    }
  }, [form.currency])

  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [justAdded, setJustAdded] = useState(false)

  // Recommendations state
  const [recommendations, setRecommendations] = useState([])
  const [loadingRecs, setLoadingRecs] = useState(false)
  const [recError, setRecError] = useState('')

  // Calculate nights
  const nights = useMemo(() => {
    if (!form.start || !form.end) return 0
    const diff = Math.round(
      (new Date(form.end) - new Date(form.start)) / (1000 * 60 * 60 * 24)
    )
    return Math.max(0, diff)
  }, [form.start, form.end])

  // Field updater
  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    if (formError) setFormError('')
  }

  // Currency switcher with smart starting budget adjustment
  const handleCurrencyChange = (newCurrency) => {
    const oldCurrency = form.currency
    if (oldCurrency === newCurrency) return

    const oldCfg = CURRENCY_CONFIG[oldCurrency] || { base: 10000, rate: 1 }
    const newCfg = CURRENCY_CONFIG[newCurrency] || { base: 10000, rate: 1 }

    if (form.budget === oldCfg.base) {
      updateField('budget', newCfg.base)
    } else {
      const inrValue = form.budget / oldCfg.rate
      const converted = inrValue * newCfg.rate
      const step = newCfg.step || 50
      const rounded = Math.round(converted / step) * step
      updateField('budget', Math.max(newCfg.min || 50, rounded))
    }
    updateField('currency', newCurrency)
  }

  // Dynamic Destination-Based Preferences state
  const [availablePreferences, setAvailablePreferences] = useState([])
  const [loadingPreferences, setLoadingPreferences] = useState(false)
  const [preferencesMessage, setPreferencesMessage] = useState('')
  const [preferencesError, setPreferencesError] = useState('')
  const preferenceRequestIdRef = useRef(0)

  // Live dynamic destination autocomplete
  const [destSuggestions, setDestSuggestions] = useState([])
  const [loadingDestSuggestions, setLoadingDestSuggestions] = useState(false)
  const [showDestSuggestions, setShowDestSuggestions] = useState(false)

  // Live dynamic origin (departure) autocomplete
  const [originSuggestions, setOriginSuggestions] = useState([])
  const [loadingOriginSuggestions, setLoadingOriginSuggestions] = useState(false)
  const [showOriginSuggestions, setShowOriginSuggestions] = useState(false)

  // Custom user-added travel interest
  const [customInterest, setCustomInterest] = useState('')
  const [showAddCustom, setShowAddCustom] = useState(false)

  // Live Destination autocomplete fetcher
  useEffect(() => {
    const q = (form.destination || '').trim()
    if (q.length < 2) {
      setDestSuggestions([])
      setLoadingDestSuggestions(false)
      setShowDestSuggestions(false)
      return
    }
    const timer = setTimeout(async () => {
      setLoadingDestSuggestions(true)
      try {
        const results = await api.autocompleteDestinations(q)
        if (Array.isArray(results)) {
          setDestSuggestions(results)
        }
      } catch (e) {
        console.debug('Destination autocomplete error:', e)
      } finally {
        setLoadingDestSuggestions(false)
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [form.destination])

  // Live Origin autocomplete fetcher
  useEffect(() => {
    const q = (form.origin || '').trim()
    if (q.length < 2) {
      setOriginSuggestions([])
      setLoadingOriginSuggestions(false)
      setShowOriginSuggestions(false)
      return
    }
    const timer = setTimeout(async () => {
      setLoadingOriginSuggestions(true)
      try {
        const results = await api.autocompleteDestinations(q)
        if (Array.isArray(results)) {
          setOriginSuggestions(results)
        }
      } catch (e) {
        console.debug('Origin autocomplete error:', e)
      } finally {
        setLoadingOriginSuggestions(false)
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [form.origin])

  const handleAddCustomInterest = (e) => {
    e?.preventDefault()
    const clean = customInterest.trim().toLowerCase()
    if (!clean) return
    const id = clean.replace(/[^a-z0-9]+/g, '-')
    const label = clean.charAt(0).toUpperCase() + clean.slice(1)
    if (!availablePreferences.some((p) => p.id === id)) {
      setAvailablePreferences((prev) => [
        ...prev,
        { id, label, emoji: '✨', count: 1 },
      ])
    }
    if (!form.selectedInterests.includes(id)) {
      setForm((prev) => ({
        ...prev,
        selectedInterests: [...prev.selectedInterests, id],
      }))
    }
    setCustomInterest('')
    setShowAddCustom(false)
  }

  // Dynamic destination-based preferences loader with debouncing and race-condition safety
  useEffect(() => {
    const dest = (form.destination || '').trim()

    // 1. Initial State: No destination entered
    if (!dest || dest.length < 2) {
      setAvailablePreferences([])
      setLoadingPreferences(false)
      setPreferencesMessage('Select a destination to discover available experiences.')
      setPreferencesError('')
      return
    }

    // 2. Loading State & Request ID Tracking
    setLoadingPreferences(true)
    setPreferencesMessage('')
    setPreferencesError('')
    const currentRequestId = ++preferenceRequestIdRef.current

    const timer = setTimeout(async () => {
      try {
        const res = await api.getDestinationPreferences(dest)

        // Prevent race condition: ignore if destination changed while waiting
        if (currentRequestId !== preferenceRequestIdRef.current) return

        if (res && res.supported && Array.isArray(res.preferences) && res.preferences.length > 0) {
          setAvailablePreferences(res.preferences)
          setPreferencesMessage('')
          setPreferencesError('')

          // Preserve selections that are still relevant to this destination, remove unsupported ones
          const supportedIdSet = new Set(res.preferences.map((p) => p.id))
          setForm((prev) => {
            const preserved = prev.selectedInterests.filter((id) => supportedIdSet.has(id))
            // If user had no previous selections matching this destination, auto-select top 2 experiences
            const finalInterests = preserved.length > 0
              ? preserved
              : res.preferences.slice(0, 2).map((p) => p.id)
            return {
              ...prev,
              selectedInterests: finalInterests,
            }
          })
        } else {
          // Destination not recognized or no activities found
          setAvailablePreferences([])
          setPreferencesMessage('')
          setPreferencesError(
            res?.message || `No activity data found for "${dest}". Please verify the destination name.`
          )
          // Clear stale selections
          setForm((prev) => ({ ...prev, selectedInterests: [] }))
        }
      } catch (err) {
        if (currentRequestId !== preferenceRequestIdRef.current) return
        setAvailablePreferences([])
        setPreferencesMessage('')
        setPreferencesError(`Could not load activities for "${dest}". Please check destination spelling.`)
      } finally {
        if (currentRequestId === preferenceRequestIdRef.current) {
          setLoadingPreferences(false)
        }
      }
    }, 350)

    return () => clearTimeout(timer)
  }, [form.destination])

  // Toggle interest chip
  const toggleInterest = (id) => {
    setForm((prev) => {
      const exists = prev.selectedInterests.includes(id)
      const next = exists
        ? prev.selectedInterests.filter((x) => x !== id)
        : [...prev.selectedInterests, id]
      return { ...prev, selectedInterests: next }
    })
  }

  // Fetch intelligent backend recommendations when on step 0 or step 2
  useEffect(() => {
    let cancelled = false
    const fetchRecs = async () => {
      setLoadingRecs(true)
      setRecError('')
      try {
        const payload = {
          destination: form.destination.trim() || undefined,
          interests: form.selectedInterests,
          budget: Number(form.budget),
          currency: form.currency,
          travelers: Number(form.travelers),
          start_date: form.start || undefined,
          end_date: form.end || undefined,
          special_requests: form.specialRequests || undefined,
          style: form.travelStyle,
          pace: form.tripPace,
        }
        const data = await api.recommendDestinations(payload)
        if (!cancelled && Array.isArray(data)) {
          setRecommendations(data)
        }
      } catch (err) {
        if (!cancelled) {
          console.warn('Recommendation API notice:', err.message)
          // Fallback gracefully to catalog if needed
          try {
            const catalog = await api.destinations()
            if (!cancelled && Array.isArray(catalog)) {
              setRecommendations(
                catalog.map((c) => ({
                  ...c,
                  match_score: 90,
                  match_reasons: ['Popular destination matching your travel preferences.'],
                }))
              )
            }
          } catch (e) {
            if (!cancelled) setRecError('Unable to load destination recommendations.')
          }
        }
      } finally {
        if (!cancelled) setLoadingRecs(false)
      }
    }

    fetchRecs()
    return () => {
      cancelled = true
    }
  }, [
    form.destination,
    form.selectedInterests,
    form.budget,
    form.currency,
    form.travelers,
    form.travelStyle,
    form.tripPace,
  ])

  // Validation between steps
  const handleNext = () => {
    if (step === 0) {
      if (!form.destination.trim()) {
        setFormError('Please enter a destination or select one from the recommendations below.')
        return
      }
      if (form.selectedInterests.length === 0) {
        setFormError('Please select at least one travel preference.')
        return
      }
    }

    if (step === 1) {
      if (!form.start || !form.end) {
        setFormError('Please select both a start date and an end date.')
        return
      }
      const todayStr = getTodayDateStr()
      if (form.start < todayStr) {
        setFormError('Start date cannot be in the past. Please choose today or an upcoming date.')
        return
      }
      if (form.end <= form.start) {
        setFormError('End date cannot be the same as or earlier than the start date. A trip must be at least 1 night.')
        return
      }
      const minBudget = CURRENCY_CONFIG[form.currency]?.min || 10000
      if (Number(form.budget) < minBudget) {
        setFormError(
          `Minimum allowed budget for ${form.currency} is ${activeCurrencySymbol}${minBudget.toLocaleString()}. Trips under ${activeCurrencySymbol}${minBudget.toLocaleString()} are not allowed.`
        )
        return
      }
    }

    setFormError('')
    setStep((prev) => Math.min(prev + 1, 2))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleBack = () => {
    setFormError('')
    setStep((prev) => Math.max(prev - 1, 0))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Final submission: saves trip to backend database & redirects to trips dashboard
  const handleFinalSubmit = async () => {
    if (submitting) return

    const minBudget = CURRENCY_CONFIG[form.currency]?.min || 10000
    if (Number(form.budget) < minBudget) {
      setFormError(
        `Minimum allowed budget for ${form.currency} is ${activeCurrencySymbol}${minBudget.toLocaleString()}. Trips under ${activeCurrencySymbol}${minBudget.toLocaleString()} cannot be created.`
      )
      setStep(1)
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }

    setSubmitting(true)
    setFormError('')

    try {
      const payload = {
        destination: form.destination.trim(),
        start_date: form.start,
        end_date: form.end,
        budget: Number(form.budget),
        travelers: Number(form.travelers),
        interests: form.selectedInterests,
        currency: form.currency || 'INR',
        preferences: {
          origin: form.origin?.trim() || undefined,
          style: form.travelStyle,
          pace: form.tripPace,
          accommodation: userPrefs.accommodation || 'Hotel',
          food: form.dietary || userPrefs.food || 'No preference',
          currency: form.currency || 'INR',
          accessibility: form.accessibility,
          special_requests: form.specialRequests,
        },
      }

      const created = await api.createTrip(payload, getToken())
      setJustAdded(true)
      setTimeout(() => {
        if (created && created.id) {
          navigate(`/trips/${created.id}`)
        } else {
          navigate('/trips')
        }
      }, 700)
    } catch (err) {
      const msg =
        typeof err?.message === 'string' && err.message !== '[object Object]'
          ? err.message
          : typeof err === 'string'
          ? err
          : 'Could not save your trip. Please check your details and try again.'
      setFormError(msg)
      setSubmitting(false)
    }

  }

  // Pick recommendation directly
  const pickDestination = (dest) => {
    updateField('destination', dest.name)
    if (dest.tags && dest.tags.length > 0) {
      const merged = Array.from(new Set([...form.selectedInterests, ...dest.tags]))
      updateField('selectedInterests', merged)
    }
    // Advance to Step 1 if on step 0
    if (step === 0) {
      setStep(1)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const activeCurrencySymbol =
    currencyOptions.find((c) => c.code === form.currency)?.symbol || '$'

  return (
    <div className="min-h-screen w-full flex bg-[#f8fafc]">
      {/* Unified Sidebar */}
      <Sidebar activeNav="Create Trip" />

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
          sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
        }`}
      >
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <section className="relative mb-8 overflow-hidden rounded-3xl shadow-md">
            <img
              src={resolveImageUrl('/images/hero.jpg')}
              alt="Create Trip"
              className="absolute inset-0 h-full w-full object-cover object-center"
            />
            {/* Dark Gradient Overlay */}
            <div
              className="absolute inset-0"
              style={{
                background:
                  'linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.70) 55%, rgba(46, 16, 101, 0.60) 100%)',
              }}
            />

            <div className="relative z-10 flex flex-col justify-between p-6 sm:p-10 text-white">
              <div className="flex items-center gap-3 mb-3">
                <button
                  type="button"
                  onClick={() => (step > 0 ? handleBack() : navigate('/dashboard'))}
                  className="grid h-8 w-8 place-items-center rounded-xl bg-white/10 text-white backdrop-blur-md transition-colors hover:bg-white/20"
                >
                  <ArrowLeft size={16} />
                </button>
                <span className="text-[11px] font-semibold tracking-wider uppercase text-violet-300">
                  STEP {step + 1} OF 3
                </span>
              </div>

              <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
                Create a New Trip
              </h1>
              <p className="mt-1.5 text-xs sm:text-sm text-slate-200/90 max-w-lg leading-relaxed">
                Tell us your preferences and we’ll help plan your perfect trip.
              </p>

              {/* Progress Indicator */}
              <div className="mt-8 flex items-center justify-between max-w-md">
                {STEPS.map((s, idx) => {
                  const isActive = step === idx
                  const isDone = step > idx
                  return (
                    <div key={s.id} className="flex items-center flex-1 last:flex-none">
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`grid h-8 w-8 place-items-center rounded-full text-xs font-bold transition-all ${
                            isActive
                              ? 'bg-violet-500 text-white shadow-md ring-4 ring-violet-400/30'
                              : isDone
                              ? 'bg-emerald-500 text-white'
                              : 'bg-white/20 text-white/70'
                          }`}
                        >
                          {isDone ? <Check size={14} /> : s.id}
                        </div>
                        <div className="hidden sm:block">
                          <p
                            className={`text-xs font-bold leading-tight ${
                              isActive ? 'text-white' : 'text-slate-300'
                            }`}
                          >
                            {s.title}
                          </p>
                          <p className="text-[10px] text-white/60">{s.desc}</p>
                        </div>
                      </div>

                      {idx < STEPS.length - 1 && (
                        <div
                          className={`h-0.5 flex-1 mx-3 rounded-full transition-colors ${
                            step > idx ? 'bg-emerald-400' : 'bg-white/20'
                          }`}
                        />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </section>

          {/* Form Error Banner */}
          {formError && (
            <div className="mb-6 flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-800 shadow-xs">
              <AlertCircle size={16} className="text-red-600 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          {step === 0 && (
            <div className="space-y-8 animate-fade-up">
              {/* Section A: Origin & Destination */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    A. Where do you want to go?
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Enter your departure location and target destination.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {/* Origin / Departure Input with Live Autocomplete */}
                  <div className="relative">
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">
                      From where you want to go <span className="font-normal text-slate-400">(Departure)</span>
                    </label>
                    <div className="relative">
                      <Navigation
                        size={16}
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-blue-600"
                      />
                      <input
                        type="text"
                        value={form.origin}
                        onChange={(e) => {
                          const val = e.target.value
                          updateField('origin', val)
                          if (val.trim().length >= 2) {
                            setShowOriginSuggestions(true)
                          } else {
                            setShowOriginSuggestions(false)
                            setOriginSuggestions([])
                          }
                        }}
                        onFocus={() => {
                          if ((form.origin || '').trim().length >= 2) {
                            setShowOriginSuggestions(true)
                          }
                        }}
                        onBlur={() => setTimeout(() => setShowOriginSuggestions(false), 200)}
                        placeholder="Starting city (e.g. New York, London, Mumbai)"
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-3 text-sm text-slate-800 outline-none transition-colors focus:border-violet-600 focus:bg-white focus:ring-3 focus:ring-violet-500/10"
                      />
                      {loadingOriginSuggestions && (
                        <Loader2 size={14} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 animate-spin" />
                      )}
                    </div>

                    {/* Origin Suggestions Dropdown - only after start typing */}
                    {showOriginSuggestions && (form.origin || '').trim().length >= 2 && originSuggestions.length > 0 && (
                      <div className="absolute left-0 right-0 top-full mt-1.5 z-30 max-h-56 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl">
                        {originSuggestions.map((item, idx) => (
                          <button
                            key={item.id || idx}
                            type="button"
                            onMouseDown={() => {
                              updateField('origin', item.name || item.city)
                              setShowOriginSuggestions(false)
                              setOriginSuggestions([])
                            }}
                            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left hover:bg-slate-50 transition-colors"
                          >
                            <Navigation size={14} className="text-blue-500 shrink-0" />
                            <div className="min-w-0 flex-1">
                              <p className="text-xs font-semibold text-slate-800 truncate">
                                {item.name || item.city}
                              </p>
                              <p className="text-[10px] text-slate-400 truncate">
                                {item.formatted || item.country}
                              </p>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Destination Input with Live Autocomplete */}
                  <div className="relative">
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">
                      What is your destination <span className="text-violet-600">*</span>
                    </label>
                    <div className="relative">
                      <MapPin
                        size={16}
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-violet-600"
                      />
                      <input
                        type="text"
                        value={form.destination}
                        onChange={(e) => {
                          const val = e.target.value
                          updateField('destination', val)
                          if (val.trim().length >= 2) {
                            setShowDestSuggestions(true)
                          } else {
                            setShowDestSuggestions(false)
                            setDestSuggestions([])
                          }
                        }}
                        onFocus={() => {
                          if ((form.destination || '').trim().length >= 2) {
                            setShowDestSuggestions(true)
                          }
                        }}
                        onBlur={() => setTimeout(() => setShowDestSuggestions(false), 200)}
                        placeholder="Search any city, town, island, or region worldwide..."
                        className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-3 text-sm text-slate-800 outline-none transition-colors focus:border-violet-600 focus:bg-white focus:ring-3 focus:ring-violet-500/10"
                      />
                      {loadingDestSuggestions && (
                        <Loader2 size={14} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-violet-500 animate-spin" />
                      )}
                    </div>

                    {/* Destination Suggestions Dropdown - only after start typing */}
                    {showDestSuggestions && (form.destination || '').trim().length >= 2 && destSuggestions.length > 0 && (
                      <div className="absolute left-0 right-0 top-full mt-1.5 z-30 max-h-64 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl">
                        {destSuggestions.map((item, idx) => (
                          <button
                            key={item.id || idx}
                            type="button"
                            onMouseDown={() => {
                              updateField('destination', item.name || item.city)
                              setShowDestSuggestions(false)
                              setDestSuggestions([])
                            }}
                            className="flex w-full items-center gap-3 rounded-xl p-2 text-left hover:bg-violet-50/60 transition-colors"
                          >
                            {item.image_url ? (
                              <img
                                src={resolveImageUrl(item.image_url)}
                                alt={item.name}
                                referrerPolicy="no-referrer"
                                onError={(e) => {
                                  e.currentTarget.onerror = null
                                  e.currentTarget.src = resolveImageUrl('/images/hero.jpg')
                                }}
                                className="h-9 w-9 rounded-lg object-cover shrink-0"
                              />
                            ) : (
                              <div className="grid h-9 w-9 place-items-center rounded-lg bg-violet-100 text-violet-600 shrink-0">
                                <MapPin size={16} />
                              </div>
                            )}
                            <div className="min-w-0 flex-1">
                              <p className="text-xs font-bold text-slate-800 truncate">
                                {item.name || item.city}
                              </p>
                              <p className="text-[10px] text-slate-500 truncate">
                                {item.formatted || item.country}
                              </p>
                            </div>
                            <span className="text-[9px] font-semibold text-violet-600 bg-violet-50 px-2 py-0.5 rounded-full shrink-0">
                              Select
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Section B: Travel Preferences Chips */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-slate-900">
                      B. Travel Preferences
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {form.destination.trim()
                        ? `Available experiences tailored to ${form.destination.trim()}:`
                        : 'Select all experiences you want prioritized in your itinerary.'}
                    </p>
                  </div>
                  {availablePreferences.length > 0 && (
                    <span className="text-xs font-semibold text-violet-700 bg-violet-50 px-2.5 py-1 rounded-full self-start border border-violet-100">
                      {form.selectedInterests.length} selected
                    </span>
                  )}
                </div>

                {/* State 1: No destination entered yet */}
                {!form.destination.trim() && (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 p-8 text-center">
                    <Compass size={32} className="mx-auto text-violet-400 mb-2.5 opacity-80" />
                    <p className="text-sm font-semibold text-slate-700">
                      Select a destination to discover available experiences.
                    </p>
                    <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                      Different destinations offer different activities — enter your destination above to load real local attractions and experiences.
                    </p>
                  </div>
                )}

                {/* State 2: Loading preferences indicator */}
                {form.destination.trim() && loadingPreferences && (
                  <div className="rounded-2xl border border-violet-100 bg-violet-50/40 p-8 text-center">
                    <Loader2 size={28} className="mx-auto text-violet-600 animate-spin mb-2.5" />
                    <p className="text-xs font-bold text-violet-900">
                      Discovering available activities in {form.destination.trim()}...
                    </p>
                    <p className="text-[11px] text-violet-600/80 mt-1">
                      Analyzing local attractions, sights, and verified experiences.
                    </p>
                  </div>
                )}

                {/* State 3: Destination not found / error */}
                {form.destination.trim() && !loadingPreferences && preferencesError && (
                  <div className="rounded-2xl border border-amber-200 bg-amber-50/60 p-6 text-center">
                    <AlertCircle size={28} className="mx-auto text-amber-600 mb-2" />
                    <p className="text-xs font-bold text-amber-900">{preferencesError}</p>
                    <p className="text-[11px] text-amber-700 mt-1">
                      You can still continue planning your journey to {form.destination.trim()} and add your custom interests below.
                    </p>
                  </div>
                )}

                {/* State 4: Dynamic Preference Cards Display */}
                {form.destination.trim() && !loadingPreferences && (
                  <div className="space-y-4">
                    {availablePreferences.length > 0 && (
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                        {availablePreferences.map((item) => {
                          const selected = form.selectedInterests.includes(item.id)
                          return (
                            <button
                              key={item.id}
                              type="button"
                              onClick={() => toggleInterest(item.id)}
                              className={`flex flex-col items-center justify-center p-3.5 rounded-2xl border text-center transition-all ${
                                selected
                                  ? 'border-violet-600 bg-violet-50/80 text-violet-900 shadow-xs ring-2 ring-violet-500/20'
                                  : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                              }`}
                            >
                              <span className="text-2xl mb-1.5">{item.emoji}</span>
                              <span className="text-xs font-semibold tracking-tight">
                                {item.label}
                              </span>
                              {item.count > 0 && (
                                <span className="text-[10px] text-slate-400 mt-0.5">
                                  {item.count} activit{item.count > 1 ? 'ies' : 'y'}
                                </span>
                              )}
                            </button>
                          )
                        })}
                      </div>
                    )}

                    {/* Custom Interest Adder */}
                    <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-3">
                      {!showAddCustom ? (
                        <button
                          type="button"
                          onClick={() => setShowAddCustom(true)}
                          className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet-600 hover:text-violet-700 bg-violet-50 hover:bg-violet-100 px-3 py-1.5 rounded-xl transition-colors border border-violet-200"
                        >
                          <Plus size={14} />
                          Add Custom Interest
                        </button>
                      ) : (
                        <form
                          onSubmit={handleAddCustomInterest}
                          className="flex items-center gap-2"
                        >
                          <input
                            type="text"
                            value={customInterest}
                            onChange={(e) => setCustomInterest(e.target.value)}
                            placeholder="e.g. Scuba diving, Pottery, Star gazing"
                            autoFocus
                            className="rounded-xl border border-violet-300 bg-white px-3 py-1.5 text-xs text-slate-800 outline-none focus:ring-2 focus:ring-violet-500/20 w-64"
                          />
                          <button
                            type="submit"
                            className="rounded-xl bg-violet-600 text-white px-3 py-1.5 text-xs font-semibold hover:bg-violet-700 transition-colors"
                          >
                            Add
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setShowAddCustom(false)
                              setCustomInterest('')
                            }}
                            className="grid h-7 w-7 place-items-center text-slate-400 hover:text-slate-600"
                          >
                            <X size={14} />
                          </button>
                        </form>
                      )}
                      <span className="text-[11px] text-slate-400">
                        {form.destination.trim()
                          ? `Experiences dynamically tailored to verified sights in ${form.destination.trim()}.`
                          : ''}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Section C: Additional Preferences & Special Requests */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    C. Additional Preferences & Special Requests
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Customize dietary needs, accessibility, or specific trip notes.
                  </p>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  {/* Dietary */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">
                      Dietary Preferences
                    </label>
                    <select
                      value={form.dietary}
                      onChange={(e) => updateField('dietary', e.target.value)}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-3 text-xs text-slate-800 outline-none focus:border-violet-500"
                    >
                      {dietaryOptions.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Accessibility */}
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">
                      Accessibility Requirements
                    </label>
                    <select
                      value={form.accessibility}
                      onChange={(e) => updateField('accessibility', e.target.value)}
                      className="w-full rounded-2xl border border-slate-200 bg-white px-3.5 py-3 text-xs text-slate-800 outline-none focus:border-violet-500"
                    >
                      {accessibilityOptions.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Special Requests */}
                <div className="mt-5">
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    Special Requests <span className="font-normal text-slate-400">(Optional)</span>
                  </label>
                  <textarea
                    rows={3}
                    value={form.specialRequests}
                    onChange={(e) => updateField('specialRequests', e.target.value)}
                    placeholder="e.g. Honeymoon trip, prefer scenic ocean views, avoid steep mountain climbs, local culinary masterclass..."
                    className="w-full rounded-2xl border border-slate-200 bg-white p-3.5 text-xs text-slate-800 outline-none focus:border-violet-500 leading-relaxed"
                  />
                </div>
              </div>

              {/* Navigation Actions */}
              <div className="flex justify-end pt-4">
                <button
                  type="button"
                  onClick={handleNext}
                  className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white shadow-md transition-all hover:opacity-95 hover:shadow-lg active:scale-98"
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  }}
                >
                  Continue to Budget & Dates
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-8 animate-fade-up">
              {/* Section D: Travel Dates & Travelers */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    D. Travel Dates & Travelers
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    When are you planning to travel and with whom?
                  </p>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">
                      Start Date
                    </label>
                    <div className="relative">
                      <Calendar
                        size={16}
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                      />
                      <input
                        type="date"
                        min={getTodayDateStr()}
                        value={form.start}
                        onChange={(e) => {
                          const newStart = e.target.value
                          updateField('start', newStart)
                          if (newStart && (!form.end || form.end <= newStart)) {
                            updateField('end', getNextDayDateStr(newStart))
                          }
                        }}
                        className="w-full rounded-2xl border border-slate-200 pl-10 pr-3.5 py-3 text-xs text-slate-800 outline-none focus:border-violet-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1.5">
                      End Date
                    </label>
                    <div className="relative">
                      <Calendar
                        size={16}
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
                      />
                      <input
                        type="date"
                        min={form.start ? getNextDayDateStr(form.start) : getNextDayDateStr(getTodayDateStr())}
                        value={form.end}
                        onChange={(e) => updateField('end', e.target.value)}
                        className="w-full rounded-2xl border border-slate-200 pl-10 pr-3.5 py-3 text-xs text-slate-800 outline-none focus:border-violet-500"
                      />
                    </div>
                  </div>
                </div>

                {nights > 0 && (
                  <div className="mt-4 flex items-center gap-2 rounded-xl bg-violet-50 p-3 text-xs font-medium text-violet-800">
                    <Clock size={14} className="text-violet-600" />
                    <span>
                      Trip Duration: <strong>{nights} night{nights > 1 ? 's' : ''}</strong> (
                      {nights + 1} days)
                    </span>
                  </div>
                )}

                {/* Travelers counter */}
                <div className="mt-6 border-t border-slate-100 pt-5">
                  <label className="block text-xs font-bold text-slate-700 mb-2">
                    Number of Travelers
                  </label>
                  <div className="flex items-center gap-4">
                    <button
                      type="button"
                      onClick={() =>
                        updateField('travelers', Math.max(1, form.travelers - 1))
                      }
                      disabled={form.travelers <= 1}
                      title={form.travelers <= 1 ? 'Minimum 1 traveler' : 'Decrease travelers'}
                      className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent transition-all"
                    >
                      -
                    </button>
                    <span className="w-12 text-center text-base font-extrabold text-slate-900">
                      {form.travelers}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        updateField('travelers', Math.min(15, form.travelers + 1))
                      }
                      disabled={form.travelers >= 15}
                      title={form.travelers >= 15 ? 'Maximum 15 travelers allowed' : 'Increase travelers'}
                      className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-transparent transition-all"
                    >
                      +
                    </button>
                    <span className="text-xs text-slate-500">
                      {form.travelers === 1
                        ? 'Solo traveler'
                        : form.travelers === 15
                        ? '15 people (maximum limit)'
                        : `${form.travelers} people`}
                    </span>
                  </div>
                </div>
              </div>

              {/* Section E: Budget & Currency */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-slate-900">
                      E. Trip Budget
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Specify your estimated spending limit and preferred currency.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-500 font-medium">Currency:</label>
                    <select
                      value={form.currency}
                      onChange={(e) => handleCurrencyChange(e.target.value)}
                      className="rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-800 outline-none cursor-pointer focus:border-violet-500"
                    >
                      {currencyOptions.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Budget Input Box */}
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="block text-xs font-bold text-slate-700">
                      Enter Budget Amount <span className="text-violet-600">*</span>
                    </label>
                    <span className="text-[11px] font-bold text-violet-700">
                      Minimum required: {activeCurrencySymbol}{(CURRENCY_CONFIG[form.currency]?.min || 10000).toLocaleString()}
                    </span>
                  </div>
                  <div className="relative flex items-center">
                    <span className="absolute left-4 text-lg font-bold text-violet-600 select-none">
                      {activeCurrencySymbol}
                    </span>
                    <input
                      type="number"
                      min={CURRENCY_CONFIG[form.currency]?.min || 10000}
                      step={CURRENCY_CONFIG[form.currency]?.step || 500}
                      value={form.budget === 0 ? '' : form.budget}
                      onChange={(e) => {
                        const val = e.target.value === '' ? 0 : parseInt(e.target.value, 10)
                        updateField('budget', isNaN(val) ? 0 : Math.max(0, val))
                      }}
                      onBlur={() => {
                        const minBudget = CURRENCY_CONFIG[form.currency]?.min || 10000
                        if (form.budget < minBudget) {
                          updateField('budget', minBudget)
                        }
                      }}
                      placeholder={CURRENCY_CONFIG[form.currency]?.placeholder || 'e.g. 10000'}
                      className={`w-full rounded-2xl border bg-slate-50/50 pl-11 pr-24 py-3.5 text-lg font-black text-slate-900 outline-none transition-colors focus:bg-white focus:ring-3 ${
                        form.budget < (CURRENCY_CONFIG[form.currency]?.min || 10000)
                          ? 'border-red-400 focus:border-red-500 focus:ring-red-500/10'
                          : 'border-slate-200 focus:border-violet-600 focus:ring-violet-500/10'
                      }`}
                    />
                    <div className="absolute right-3.5 flex items-center gap-1.5 rounded-xl bg-violet-50 px-3 py-1.5 text-xs font-bold text-violet-700">
                      <span>{form.currency}</span>
                    </div>
                  </div>
                  {form.budget < (CURRENCY_CONFIG[form.currency]?.min || 10000) && (
                    <p className="mt-2 flex items-center gap-1.5 text-xs font-bold text-red-600 animate-fade-in">
                      <AlertCircle size={14} className="shrink-0" />
                      Trips under {activeCurrencySymbol}{(CURRENCY_CONFIG[form.currency]?.min || 10000).toLocaleString()} {form.currency} are not allowed. Minimum required is {activeCurrencySymbol}{(CURRENCY_CONFIG[form.currency]?.min || 10000).toLocaleString()}.
                    </p>
                  )}
                </div>

                {/* Unified Accommodation & Travel Style (Strictly Single Select) */}
                <div className="mt-6 border-t border-slate-100 pt-5">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-bold text-slate-700">
                      Accommodation & Travel Style
                    </label>
                    <span className="text-[11px] text-violet-700 font-semibold bg-violet-50 px-2.5 py-0.5 rounded-full border border-violet-100">
                      Select only 1 option
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-3">
                    Choose your travel preference (only one option can be selected).
                  </p>
                  <div
                    className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2"
                    role="radiogroup"
                    aria-label="Accommodation & Travel Style"
                  >
                    {[
                      { id: 'Backpacker', label: 'Backpacker', style: 'Backpacker', pace: 'Fast-paced' },
                      { id: 'Budget', label: 'Budget', style: 'Budget', pace: 'Moderate' },
                      { id: 'Comfort', label: 'Comfort', style: 'Comfort', pace: 'Moderate' },
                      { id: 'Luxury', label: 'Luxury', style: 'Luxury', pace: 'Relaxed' },
                      { id: 'Fast-paced', label: 'Fast-paced', style: 'Backpacker', pace: 'Fast-paced' },
                      { id: 'Relaxed', label: 'Relaxed', style: 'Comfort', pace: 'Relaxed' },
                    ].map((opt) => {
                      const isSelected =
                        (form.selectedTravelOption || form.travelStyle) === opt.id

                      return (
                        <button
                          key={opt.id}
                          type="button"
                          role="radio"
                          aria-checked={isSelected}
                          onClick={() => {
                            setForm((prev) => ({
                              ...prev,
                              selectedTravelOption: opt.id,
                              travelStyle: opt.style,
                              tripPace: opt.pace,
                            }))
                          }}
                          className={`rounded-xl py-2.5 px-3 text-xs font-semibold border transition-all text-center ${
                            isSelected
                              ? 'border-violet-600 bg-violet-50 text-violet-800 shadow-xs ring-2 ring-violet-500/20'
                              : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'
                          }`}
                        >
                          {opt.label}
                        </button>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* Navigation Actions */}
              <div className="flex items-center justify-between pt-4">
                <button
                  type="button"
                  onClick={handleBack}
                  className="rounded-xl border border-slate-200 px-5 py-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  ← Back to Preferences
                </button>
                <button
                  type="button"
                  onClick={handleNext}
                  disabled={Number(form.budget) < (CURRENCY_CONFIG[form.currency]?.min || 10000)}
                  className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white shadow-md transition-all hover:opacity-95 hover:shadow-lg active:scale-98 disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  }}
                  title={
                    Number(form.budget) < (CURRENCY_CONFIG[form.currency]?.min || 10000)
                      ? `Minimum budget of ${activeCurrencySymbol}${(CURRENCY_CONFIG[form.currency]?.min || 10000).toLocaleString()} required`
                      : 'Continue to Review'
                  }
                >
                  Review & Recommendations
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-10 animate-fade-up">
              {/* Trip Overview Summary Card */}
              <div className="overflow-hidden rounded-3xl border border-slate-200/90 bg-white shadow-md">
                <div className="border-b border-slate-100 bg-slate-50/70 p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-violet-700 bg-violet-100 px-2.5 py-0.5 rounded-full">
                      Trip Overview
                    </span>
                    <h2 className="mt-2 text-2xl font-black text-slate-900">
                      {form.destination || 'Custom Destination'}
                    </h2>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {form.start} – {form.end} · {nights} nights · {form.travelers} traveler(s)
                    </p>
                  </div>

                  <div className="text-left sm:text-right">
                    <p className="text-xs text-slate-400">Total Budget</p>
                    <p className={`text-2xl font-black ${
                      Number(form.budget) < (CURRENCY_CONFIG[form.currency]?.min || 10000)
                        ? 'text-red-600'
                        : 'text-violet-700'
                    }`}>
                      {activeCurrencySymbol}
                      {Number(form.budget).toLocaleString()} {form.currency}
                    </p>
                    {Number(form.budget) < (CURRENCY_CONFIG[form.currency]?.min || 10000) && (
                      <p className="text-[11px] font-bold text-red-600 mt-0.5">
                        Below minimum ({activeCurrencySymbol}{(CURRENCY_CONFIG[form.currency]?.min || 10000).toLocaleString()})
                      </p>
                    )}
                  </div>
                </div>

                <div className="p-6 sm:p-8 space-y-4 text-xs">
                  {/* Selected Preferences Badges */}
                  <div>
                    <span className="font-bold text-slate-700 block mb-2">
                      Selected Travel Preferences:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {form.selectedInterests.map((id) => {
                        const item = ALL_INTERESTS.find((x) => x.id === id)
                        return (
                          <span
                            key={id}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-violet-50 px-3 py-1 font-semibold text-violet-800 border border-violet-100"
                          >
                            <span>{item?.emoji}</span>
                            <span>{item?.label || id}</span>
                          </span>
                        )
                      })}
                    </div>
                  </div>

                  {/* Style, Pace, Dietary */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                    <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Style</span>
                      <span className="font-bold text-slate-700">{form.travelStyle}</span>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Pace</span>
                      <span className="font-bold text-slate-700">{form.tripPace}</span>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Dietary</span>
                      <span className="font-bold text-slate-700">{form.dietary}</span>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-2.5 border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Accessibility</span>
                      <span className="font-bold text-slate-700">{form.accessibility}</span>
                    </div>
                  </div>

                  {form.specialRequests && (
                    <div className="rounded-xl bg-slate-50 p-3 border border-slate-100 text-slate-600">
                      <span className="font-bold text-slate-700 block mb-0.5">Special Requests:</span>
                      {form.specialRequests}
                    </div>
                  )}
                </div>

                {/* Final Submit Button */}
                <div className="border-t border-slate-100 bg-slate-50/50 p-5 sm:p-6 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <button
                    type="button"
                    onClick={handleBack}
                    className="text-xs font-semibold text-slate-600 hover:text-slate-900"
                  >
                    ← Edit Details
                  </button>
                  {Number(form.budget) < (CURRENCY_CONFIG[form.currency]?.min || 10000) && (
                    <div className="flex items-center gap-1.5 text-xs font-bold text-red-600">
                      <AlertCircle size={15} className="shrink-0" />
                      <span>Trips under {activeCurrencySymbol}{(CURRENCY_CONFIG[form.currency]?.min || 10000).toLocaleString()} {form.currency} are not allowed.</span>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={handleFinalSubmit}
                    disabled={submitting || justAdded || Number(form.budget) < (CURRENCY_CONFIG[form.currency]?.min || 10000)}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl px-7 py-3.5 text-sm font-bold text-white shadow-md transition-all hover:opacity-95 hover:shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{
                      background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                    }}
                  >
                    {submitting ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                        Saving & Optimizing Plan…
                      </>
                    ) : justAdded ? (
                      <>
                        <CheckCircle2 size={18} />
                        Trip Saved Successfully!
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} />
                        Confirm & Create Trip
                      </>
                    )}
                  </button>
                </div>
              </div>

              <section className="pt-4">
                <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-xl font-bold text-slate-900 tracking-tight">
                        Personalized Recommendations for You
                      </h3>
                      <span className="rounded-full bg-violet-100 px-2.5 py-0.5 text-[11px] font-bold text-violet-700">
                        AI Ranked
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Destinations matching your selected preferences (
                      {form.selectedInterests.join(', ')}), budget ({activeCurrencySymbol}
                      {form.budget.toLocaleString()}), and trip duration.
                    </p>
                  </div>
                </div>

                {loadingRecs ? (
                  <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        className="h-72 animate-pulse rounded-2xl bg-slate-200/70"
                      />
                    ))}
                  </div>
                ) : recommendations.length === 0 ? (
                  <div className="rounded-3xl border border-dashed border-slate-200 bg-white p-8 text-center">
                    <Compass size={28} className="mx-auto text-slate-400 mb-2" />
                    <p className="text-sm font-semibold text-slate-700">
                      No matching recommendations found
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Try adding more travel preferences or adjusting your budget.
                    </p>
                  </div>
                ) : (
                  <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                    {recommendations.slice(0, 6).map((dest) => {
                      const isCurrent =
                        form.destination.toLowerCase() === dest.name.toLowerCase()
                      return (
                        <div
                          key={dest.id}
                          className={`group flex flex-col overflow-hidden rounded-2xl border bg-white shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg ${
                            isCurrent
                              ? 'border-violet-600 ring-2 ring-violet-500/20'
                              : 'border-slate-200/90'
                          }`}
                        >
                          {/* Image */}
                          <div className="relative h-44 w-full overflow-hidden bg-slate-100">
                            <img
                              src={resolveImageUrl(dest.image_url)}
                              alt={dest.name}
                              referrerPolicy="no-referrer"
                              onError={(e) => {
                                e.currentTarget.onerror = null
                                e.currentTarget.src = resolveImageUrl('/images/hero.jpg')
                              }}
                              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-106"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-black/20" />

                            {/* Match Score Badge */}
                            <span className="absolute top-3 left-3 rounded-full bg-violet-600/95 px-2.5 py-1 text-[10px] font-bold text-white shadow-xs backdrop-blur-md">
                              {dest.match_score || 95}% Match
                            </span>

                            {/* Rating */}
                            <span className="absolute top-3 right-3 flex items-center gap-1 rounded-full bg-white/95 px-2 py-0.5 text-xs font-bold text-slate-800 shadow-xs backdrop-blur-md">
                              <Star size={11} className="text-amber-500 fill-amber-500" />
                              {dest.rating || 4.8}
                            </span>

                            <div className="absolute inset-x-4 bottom-3 text-white">
                              <h4 className="text-lg font-bold truncate drop-shadow-xs">
                                {dest.name}
                              </h4>
                              <p className="text-[11px] text-white/80">{dest.country}</p>
                            </div>
                          </div>

                          {/* Body */}
                          <div className="flex flex-1 flex-col justify-between p-4">
                            <div>
                              <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
                                {dest.blurb}
                              </p>

                              {/* Match reasons */}
                              {dest.match_reasons && dest.match_reasons.length > 0 && (
                                <div className="mt-2.5 space-y-1">
                                  {dest.match_reasons.map((r, i) => (
                                    <p
                                      key={i}
                                      className="text-[11px] text-violet-700 font-medium flex items-center gap-1"
                                    >
                                      <Check size={11} className="shrink-0 text-violet-600" />
                                      <span className="truncate">{r}</span>
                                    </p>
                                  ))}
                                </div>
                              )}

                              {/* Tags */}
                              {dest.tags && dest.tags.length > 0 && (
                                <div className="mt-3 flex flex-wrap gap-1">
                                  {dest.tags.slice(0, 3).map((tag) => (
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

                            {/* Select / Applied Button */}
                            <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                              <span className="text-xs font-bold text-slate-800">
                                {dest.price || '$1,200'}
                              </span>

                              <button
                                type="button"
                                onClick={() => pickDestination(dest)}
                                className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all ${
                                  isCurrent
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                    : 'bg-violet-50 text-violet-700 hover:bg-violet-100'
                                }`}
                              >
                                {isCurrent ? '✓ Destination Selected' : 'Select Destination'}
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

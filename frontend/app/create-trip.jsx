import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  MapPin,
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
} from '../lib/constants.js'

const STEPS = [
  { id: 1, title: 'Preferences', desc: 'Destination & Style' },
  { id: 2, title: 'Budget & Dates', desc: 'Timing & Spending' },
  { id: 3, title: 'Review', desc: 'Recommendations & Confirm' },
]

export default function CreateTrip() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sidebarCollapsed = useSidebar()

  const user = getUser()
  const userPrefs = user?.preferences || {}

  // 3-step state: 0 = Preferences, 1 = Budget & Dates, 2 = Review & Recommendations
  const [step, setStep] = useState(0)

  // Form State — preserves state across all steps
  const [form, setForm] = useState(() => ({
    destination: searchParams.get('destination') || '',
    start: '',
    end: '',
    budget: 1500,
    currency: 'USD',
    travelers: 2,
    selectedInterests: userPrefs.interests || ['nature', 'adventure'],
    travelStyle: userPrefs.style || 'Comfort',
    tripPace: userPrefs.pace || 'Balanced',
    dietary: userPrefs.food || 'No preference',
    accessibility: 'None required',
    specialRequests: '',
  }))

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
      if (new Date(form.end) < new Date(form.start)) {
        setFormError('End date must be after the start date.')
        return
      }
      if (form.budget < 100) {
        setFormError('Please enter a realistic travel budget.')
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
      setFormError(err.message || 'Could not save your trip. Please try again.')
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
          {/* ============================================================
              1. SCENIC DESTINATION HEADER WITH DARK GRADIENT OVERLAY
              ============================================================ */}
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

          {/* ============================================================
              STEP 1: PREFERENCES & DESTINATION
              ============================================================ */}
          {step === 0 && (
            <div className="space-y-8 animate-fade-up">
              {/* Section A: Destination Search & Input */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    A. Where do you want to go?
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Enter any city, country, or region in the world (e.g. Kyoto, Swiss Alps, Bali, Rome, Banff).
                  </p>
                </div>

                <div className="relative">
                  <MapPin
                    size={18}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-violet-600"
                  />
                  <input
                    type="text"
                    value={form.destination}
                    onChange={(e) => updateField('destination', e.target.value)}
                    placeholder="Enter destination (e.g. Kyoto, Paris, Swiss Alps, Bali)"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 pl-11 pr-4 py-3.5 text-sm text-slate-800 outline-none transition-colors focus:border-violet-600 focus:bg-white focus:ring-3 focus:ring-violet-500/10"
                  />
                </div>
              </div>

              {/* Section C: Travel Preferences Chips */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-slate-900">
                      C. Travel Preferences
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Select all experiences you want prioritized in your itinerary.
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-violet-700 bg-violet-50 px-2.5 py-1 rounded-full self-start">
                    {form.selectedInterests.length} selected
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {ALL_INTERESTS.map((item) => {
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
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Section E: Additional Preferences */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    E. Additional Preferences & Special Requests
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

          {/* ============================================================
              STEP 2: BUDGET & DATES
              ============================================================ */}
          {step === 1 && (
            <div className="space-y-8 animate-fade-up">
              {/* Section B: Travel Dates & Travelers */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    B. Travel Dates & Travelers
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
                        value={form.start}
                        onChange={(e) => updateField('start', e.target.value)}
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
                      className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
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
                      className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 text-sm font-bold text-slate-700 hover:bg-slate-50"
                    >
                      +
                    </button>
                    <span className="text-xs text-slate-500">
                      {form.travelers === 1 ? 'Solo traveler' : `${form.travelers} people`}
                    </span>
                  </div>
                </div>
              </div>

              {/* Section D: Budget & Currency */}
              <div className="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-8 shadow-xs">
                <div className="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-slate-900">
                      D. Trip Budget
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Specify your estimated spending limit and preferred currency.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-500 font-medium">Currency:</label>
                    <select
                      value={form.currency}
                      onChange={(e) => updateField('currency', e.target.value)}
                      className="rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-800 outline-none"
                    >
                      {currencyOptions.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="mb-4 flex items-baseline justify-between">
                  <span className="text-xs text-slate-500">Total estimated budget:</span>
                  <span className="text-2xl font-black text-violet-700">
                    {activeCurrencySymbol}
                    {Number(form.budget).toLocaleString()}
                  </span>
                </div>

                {/* Slider */}
                <input
                  type="range"
                  min="300"
                  max="15000"
                  step="50"
                  value={form.budget}
                  onChange={(e) => updateField('budget', Number(e.target.value))}
                  className="w-full accent-violet-600 cursor-pointer"
                />
                <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                  <span>{activeCurrencySymbol}300</span>
                  <span>{activeCurrencySymbol}5,000</span>
                  <span>{activeCurrencySymbol}15,000+</span>
                </div>

                {/* Style & Pace options */}
                <div className="mt-6 grid gap-5 sm:grid-cols-2 border-t border-slate-100 pt-5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">
                      Accommodation & Travel Style
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {travelStyles.map((st) => (
                        <button
                          key={st}
                          type="button"
                          onClick={() => updateField('travelStyle', st)}
                          className={`rounded-xl py-2 text-xs font-semibold border transition-all ${
                            form.travelStyle === st
                              ? 'border-violet-600 bg-violet-50 text-violet-800'
                              : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          {st}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">
                      Trip Pacing
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {tripPaces.map((pc) => (
                        <button
                          key={pc}
                          type="button"
                          onClick={() => updateField('tripPace', pc)}
                          className={`rounded-xl py-2 text-xs font-semibold border transition-all ${
                            form.tripPace === pc
                              ? 'border-violet-600 bg-violet-50 text-violet-800'
                              : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          {pc}
                        </button>
                      ))}
                    </div>
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
                  className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white shadow-md transition-all hover:opacity-95 hover:shadow-lg active:scale-98"
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  }}
                >
                  Review & Recommendations
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* ============================================================
              STEP 3: REVIEW & PERSONALIZED DESTINATION RECOMMENDATIONS
              ============================================================ */}
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
                    <p className="text-2xl font-black text-violet-700">
                      {activeCurrencySymbol}
                      {Number(form.budget).toLocaleString()} {form.currency}
                    </p>
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
                  <button
                    type="button"
                    onClick={handleFinalSubmit}
                    disabled={submitting || justAdded}
                    className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl px-7 py-3.5 text-sm font-bold text-white shadow-md transition-all hover:opacity-95 hover:shadow-lg disabled:opacity-60"
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

              {/* ============================================================
                  2. PERSONALIZED DESTINATION RECOMMENDATIONS GRID
                  - Photographic header
                  - Destination cards reflecting user preferences
                  - Nature + Adventure (mountains/trekking/forests)
                  - Culture + History (heritage/museums/historic)
                  - Food (culinary/dining)
                  - Relaxation (beaches/retreats/spas)
                  ============================================================ */}
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

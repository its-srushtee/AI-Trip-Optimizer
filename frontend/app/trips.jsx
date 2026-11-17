import { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Plus,
  Calendar,
  User,
  Trash2,
  Edit3,
  Eye,
  RefreshCw,
  Compass,
  ArrowRight,
  Sparkles,
  X,
  Check,
  Clock,
  DollarSign,
  Plane,
  Hotel,
  Utensils,
  Activity,
} from 'lucide-react'
import Sidebar from '../components/common/Sidebar.jsx'
import { api, getToken, clearToken, resolveImageUrl } from '../services/api.js'
import { useTripImages } from '../hooks/useTripImages.js'
import { clearUser, getUser } from '../lib/userStore.js'
import { useSidebar } from '../hooks/useSidebar.js'
import { currencyOptions, getCurrencySymbol, formatCurrency, getTodayDateStr, getNextDayDateStr } from '../lib/constants.js'

const TABS = ['Upcoming Trips', 'Past Trips', 'Saved Trips']

export default function Trips() {
  const navigate = useNavigate()
  const sidebarCollapsed = useSidebar()

  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [activeTab, setActiveTab] = useState('Upcoming Trips')

  // Modal states
  const [selectedTrip, setSelectedTrip] = useState(null)
  const [itineraryData, setItineraryData] = useState(null)
  const [optimizing, setOptimizing] = useState(false)

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

  useEffect(() => {
    const token = getToken()
    if (!token) {
      navigate('/login')
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const tripList = await api.listTrips(token)
        if (cancelled) return
        setTrips(tripList)
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

  // Handle trip deletion
  const handleRemove = async (id, e) => {
    if (e) e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this trip?')) return
    try {
      await api.deleteTrip(id, getToken())
      setTrips((prev) => prev.filter((t) => t.id !== id))
      if (selectedTrip?.id === id) setSelectedTrip(null)
    } catch (err) {
      setLoadError(err.message)
    }
  }

  // Open dedicated trip details page
  const openTripDetails = (trip) => {
    navigate(`/trips/${trip.id}`)
  }

  // Open edit modal
  const openEditModal = (trip, e) => {
    if (e) e.stopPropagation()
    setEditingTrip(trip)
    setEditForm({
      destination: trip.destination || '',
      start_date: trip.start_date || '',
      end_date: trip.end_date || '',
      budget: trip.budget || 1000,
      currency: (trip.currency || trip.preferences?.currency || 'USD').toUpperCase(),
      travelers: trip.travelers || 1,
    })
    setEditError('')
  }

  // Save edit trip via backend PATCH /trips/{id}
  const handleSaveEdit = async (e) => {
    e.preventDefault()
    setSavingEdit(true)
    setEditError('')

    const todayStr = getTodayDateStr()
    if (editForm.start_date < todayStr) {
      setEditError('Start date cannot be in the past. Please choose today or a future date.')
      setSavingEdit(false)
      return
    }
    if (editForm.end_date <= editForm.start_date) {
      setEditError('End date cannot be the same as or earlier than the start date. A trip must be at least 1 night.')
      setSavingEdit(false)
      return
    }

    try {
      const targetCurr = (editForm.currency || editingTrip.currency || editingTrip.preferences?.currency || 'USD').toUpperCase()
      const updatePayload = {
        ...editForm,
        currency: targetCurr,
        preferences: {
          ...(editingTrip.preferences || {}),
          currency: targetCurr,
        },
      }
      const updated = await api.updateTrip(editingTrip.id, updatePayload, getToken())
      setTrips((prev) => prev.map((t) => (t.id === updated.id ? updated : t)))
      setEditingTrip(null)
    } catch (err) {
      setEditError(err.message)
    } finally {
      setSavingEdit(false)
    }
  }


  // Filter trips into Upcoming, Past, and Saved tabs
  const filteredTrips = useMemo(() => {
    const today = new Date().toISOString().split('T')[0]
    return trips.filter((t) => {
      const endDate = t.end_date || '9999-12-31'
      if (activeTab === 'Upcoming Trips') {
        return endDate >= today || t.status === 'upcoming' || t.status === 'planning'
      }
      if (activeTab === 'Past Trips') {
        return endDate < today && t.status !== 'saved'
      }
      if (activeTab === 'Saved Trips') {
        return t.status === 'saved' || !t.start_date || t.status === 'planning'
      }
      return true
    })
  }, [trips, activeTab])

  return (
    <div className="min-h-screen w-full flex bg-[#f8fafc]">
      {/* Sidebar with My Trips active */}
      <Sidebar activeNav="My Trips" />

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
          sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
        }`}
      >
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {/* Header */}
          <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
                My Trips
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Manage, review, and organize all your upcoming and past travel itineraries.
              </p>
            </div>

            <Link
              to="/create-trip"
              className="inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:opacity-95 hover:shadow-md"
              style={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
              }}
            >
              <Plus size={16} />
              Create New Trip
            </Link>
          </div>

          {/* Error Banner */}
          {loadError && (
            <div className="mb-6 flex items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800 shadow-xs">
              <span>Could not load trips: {loadError}</span>
              <button
                onClick={() => window.location.reload()}
                className="inline-flex shrink-0 items-center gap-1 font-semibold underline hover:text-amber-950"
              >
                <RefreshCw size={13} /> Retry
              </button>
            </div>
          )}

          {/* Navigation Tabs (Upcoming Trips, Past Trips, Saved Trips) */}
          <div className="mb-8 flex items-center gap-7 sm:gap-10 border-b border-slate-200 overflow-x-auto scrollbar-none">
            {TABS.map((tab) => {
              const active = activeTab === tab
              return (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className={`relative px-1 pb-3.5 text-sm font-semibold whitespace-nowrap transition-colors ${
                    active ? 'text-violet-700' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {tab}
                  {active && (
                    <span
                      className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                      style={{
                        background: 'linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%)',
                      }}
                    />
                  )}
                </button>
              )
            })}
          </div>

          {/* Trips Grid or Empty State */}
          {loading ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-72 animate-pulse rounded-2xl bg-slate-200/70"
                />
              ))}
            </div>
          ) : filteredTrips.length === 0 ? (
            /* Polished Empty State */
            <div className="rounded-3xl border border-dashed border-slate-200 bg-white p-12 text-center shadow-xs">
              <div
                className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-2xl text-violet-600 shadow-xs"
                style={{ backgroundColor: '#f5f3ff' }}
              >
                <Compass size={28} />
              </div>
              <h3 className="text-lg font-bold text-slate-800">
                No {activeTab.toLowerCase()} found
              </h3>
              <p className="mx-auto mt-1 max-w-sm text-xs sm:text-sm text-slate-500 leading-relaxed">
                {activeTab === 'Upcoming Trips'
                  ? 'You don’t have any upcoming trips planned yet. Start building your next adventure today!'
                  : activeTab === 'Past Trips'
                  ? 'Your completed journeys and past vacations will appear here.'
                  : 'Bookmark and save trip ideas to organize your future travel dreams.'}
              </p>
              <div className="mt-6">
                <Link
                  to="/create-trip"
                  className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-xs transition-opacity hover:opacity-90"
                  style={{
                    background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                  }}
                >
                  <Plus size={15} />
                  Plan a New Trip
                </Link>
              </div>
            </div>
          ) : (
            /* Trips Cards Grid */
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {filteredTrips.map((trip) => {
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
                    className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-xs transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
                  >
                    {/* Destination Image Header */}
                    <div className="relative h-44 w-full overflow-hidden bg-slate-100">
                      <img
                        src={img}
                        alt={trip.destination}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-106"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-transparent to-black/20" />

                      {/* Status Badge */}
                      <span
                        className={`absolute top-3 right-3 rounded-full px-2.5 py-1 text-[10px] font-bold tracking-wide uppercase shadow-xs backdrop-blur-md ${
                          trip.status === 'upcoming'
                            ? 'bg-emerald-50 text-emerald-700'
                            : trip.status === 'completed'
                            ? 'bg-slate-100 text-slate-700'
                            : 'bg-violet-50 text-violet-700'
                        }`}
                      >
                        ● {trip.status || 'Planning'}
                      </span>

                      {/* Destination Name */}
                      <div className="absolute inset-x-4 bottom-3 text-white">
                        <h3 className="text-lg font-bold truncate drop-shadow-xs">
                          {trip.destination}
                        </h3>
                      </div>
                    </div>

                    {/* Card Body */}
                    <div className="flex flex-1 flex-col justify-between p-4">
                      <div className="space-y-2.5">
                        {/* Dates */}
                        <div className="flex items-center gap-2 text-xs text-slate-600">
                          <Calendar size={14} className="text-violet-600 shrink-0" />
                          <span>
                            {trip.start_date
                              ? new Date(trip.start_date).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                })
                              : 'Flexible'}{' '}
                            –{' '}
                            {trip.end_date
                              ? new Date(trip.end_date).toLocaleDateString('en-US', {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                })
                              : 'Flexible'}
                          </span>
                        </div>

                        {/* Travelers & Nights */}
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span className="flex items-center gap-1.5">
                            <User size={13} className="text-slate-400" />
                            {trip.travelers} traveler{trip.travelers > 1 ? 's' : ''}
                          </span>
                          {nights > 0 && (
                            <span className="flex items-center gap-1 font-medium">
                              <Clock size={12} className="text-slate-400" />
                              {nights} nights
                            </span>
                          )}
                          {trip.budget && (
                            <span className="font-semibold text-slate-800">
                              {formatCurrency(trip.budget, trip.currency || trip.preferences?.currency)}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Card Actions (Details, Edit, Delete) */}
                      <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3">
                        <button
                          type="button"
                          onClick={() => openTripDetails(trip)}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700 transition-colors hover:bg-violet-100"
                        >
                          <Eye size={13} />
                          Trip Details
                        </button>

                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={(e) => openEditModal(trip, e)}
                            title="Edit trip"
                            className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                          >
                            <Edit3 size={14} />
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleRemove(trip.id, e)}
                            title="Delete trip"
                            className="grid h-8 w-8 place-items-center rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </article>
                )
              })}
            </div>
          )}
        </div>
      </main>

      {selectedTrip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
            onClick={() => setSelectedTrip(null)}
          />
          <div
            className="relative z-10 w-full max-w-2xl max-h-[90vh] flex flex-col rounded-3xl bg-white shadow-2xl overflow-hidden"
            style={{ backgroundColor: 'var(--panel, #ffffff)' }}
          >
            {/* Modal Image Header */}
            <div className="relative h-48 w-full shrink-0 overflow-hidden bg-slate-900">
              <img
                src={imageFor(selectedTrip.destination)}
                alt={selectedTrip.destination}
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-black/30 to-black/30" />

              <button
                type="button"
                onClick={() => setSelectedTrip(null)}
                className="absolute top-4 right-4 grid h-8 w-8 place-items-center rounded-full bg-black/40 text-white backdrop-blur-md hover:bg-black/60 transition-colors"
              >
                <X size={16} />
              </button>

              <div className="absolute inset-x-6 bottom-4 text-white">
                <span className="rounded-full bg-violet-600 px-2.5 py-0.5 text-[10px] font-bold tracking-wider uppercase">
                  {selectedTrip.status || 'Active Plan'}
                </span>
                <h2 className="mt-1 text-2xl font-black drop-shadow-sm">
                  {selectedTrip.destination}
                </h2>
                <p className="text-xs text-slate-300">
                  {selectedTrip.start_date || 'TBD'} – {selectedTrip.end_date || 'TBD'} ·{' '}
                  {selectedTrip.travelers} traveler(s) · Budget:{' '}
                  {formatCurrency(selectedTrip.budget || 1500, selectedTrip.currency || selectedTrip.preferences?.currency)}
                </p>
              </div>
            </div>

            {/* Modal Body: Itinerary & Budget */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {optimizing ? (
                <div className="py-12 text-center space-y-3">
                  <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
                  <p className="text-xs font-semibold text-slate-600">
                    Generating optimized day-by-day itinerary...
                  </p>
                </div>
              ) : itineraryData ? (
                <>
                  {/* Budget Allocation Breakdown */}
                  {itineraryData.budget_breakdown && (() => {
                    const mCurr = (selectedTrip?.currency || selectedTrip?.preferences?.currency || itineraryData?.currency || 'USD').toUpperCase()
                    return (
                      <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-1.5">
                          <DollarSign size={14} className="text-violet-600" /> Budget Breakdown
                        </h4>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                          <div className="rounded-xl bg-white p-3 border border-slate-200/70 shadow-2xs">
                            <div className="flex items-center gap-1 text-slate-400 mb-1">
                              <Plane size={12} /> Flights (30%)
                            </div>
                            <p className="font-bold text-slate-800">
                              {formatCurrency(itineraryData.budget_breakdown.flights, mCurr)}
                            </p>
                          </div>
                          <div className="rounded-xl bg-white p-3 border border-slate-200/70 shadow-2xs">
                            <div className="flex items-center gap-1 text-slate-400 mb-1">
                              <Hotel size={12} /> Stays (35%)
                            </div>
                            <p className="font-bold text-slate-800">
                              {formatCurrency(itineraryData.budget_breakdown.stay, mCurr)}
                            </p>
                          </div>
                          <div className="rounded-xl bg-white p-3 border border-slate-200/70 shadow-2xs">
                            <div className="flex items-center gap-1 text-slate-400 mb-1">
                              <Utensils size={12} /> Food (15%)
                            </div>
                            <p className="font-bold text-slate-800">
                              {formatCurrency(itineraryData.budget_breakdown.food, mCurr)}
                            </p>
                          </div>
                          <div className="rounded-xl bg-white p-3 border border-slate-200/70 shadow-2xs">
                            <div className="flex items-center gap-1 text-slate-400 mb-1">
                              <Activity size={12} /> Activities (20%)
                            </div>
                            <p className="font-bold text-slate-800">
                              {formatCurrency(itineraryData.budget_breakdown.activities, mCurr)}
                            </p>
                          </div>
                        </div>
                      </div>
                    )
                  })()}

                  {/* Summary */}
                  {itineraryData.summary && (
                    <p className="text-xs sm:text-sm text-slate-600 leading-relaxed bg-violet-50/50 p-3.5 rounded-2xl border border-violet-100">
                      {itineraryData.summary}
                    </p>
                  )}

                  {/* Day by Day Plan */}
                  {itineraryData.days && itineraryData.days.length > 0 && (
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 mb-3">
                        Day-by-Day Itinerary ({itineraryData.days.length} Days)
                      </h4>
                      <div className="space-y-3">
                        {itineraryData.days.map((day) => (
                          <div
                            key={day.day}
                            className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-2xs"
                          >
                            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-2">
                              <span className="text-xs font-bold text-violet-700">
                                Day {day.day}: {day.theme}
                              </span>
                              <span className="text-[11px] text-slate-400">
                                {day.date} · est. {formatCurrency(day.estimate_cost || day.estimate_usd, selectedTrip.currency || selectedTrip.preferences?.currency || itineraryData.currency)}
                              </span>
                            </div>
                            <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                              <div>
                                <span className="font-semibold text-slate-800">Morning:</span>{' '}
                                {day.morning}
                              </div>
                              <div>
                                <span className="font-semibold text-slate-800">Afternoon:</span>{' '}
                                {day.afternoon}
                              </div>
                              <div>
                                <span className="font-semibold text-slate-800">Evening:</span>{' '}
                                {day.evening}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-6 text-xs text-slate-500">
                  No itinerary details available.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50/80 p-4">
              <button
                type="button"
                onClick={(e) => handleRemove(selectedTrip.id, e)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-red-600 hover:text-red-700"
              >
                <Trash2 size={13} />
                Delete Trip
              </button>
              <button
                type="button"
                onClick={() => setSelectedTrip(null)}
                className="rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-900"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {editingTrip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity"
            onClick={() => setEditingTrip(null)}
          />
          <div
            className="relative z-10 w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl"
            style={{ backgroundColor: 'var(--panel, #ffffff)' }}
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-base font-bold text-slate-900">Edit Trip Details</h3>
              <button
                type="button"
                onClick={() => setEditingTrip(null)}
                className="grid h-7 w-7 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={16} />
              </button>
            </div>

            {editError && (
              <div className="mb-3 rounded-xl bg-red-50 p-2.5 text-xs text-red-700">
                {editError}
              </div>
            )}

            <form onSubmit={handleSaveEdit} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Destination</label>
                <input
                  type="text"
                  required
                  value={editForm.destination}
                  onChange={(e) => setEditForm({ ...editForm, destination: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    min={getTodayDateStr()}
                    value={editForm.start_date}
                    onChange={(e) => {
                      const newStart = e.target.value
                      setEditForm((prev) => {
                        const nextEnd =
                          newStart && (!prev.end_date || prev.end_date <= newStart)
                            ? getNextDayDateStr(newStart)
                            : prev.end_date
                        return { ...prev, start_date: newStart, end_date: nextEnd }
                      })
                    }}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    required
                    min={editForm.start_date ? getNextDayDateStr(editForm.start_date) : getNextDayDateStr(getTodayDateStr())}
                    value={editForm.end_date}
                    onChange={(e) => setEditForm({ ...editForm, end_date: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Travelers</label>
                  <input
                    type="number"
                    min="1"
                    value={editForm.travelers}
                    onChange={(e) =>
                      setEditForm({ ...editForm, travelers: Number(e.target.value) })
                    }
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Currency</label>
                  <select
                    value={editForm.currency || 'USD'}
                    onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })}
                    className="w-full rounded-xl border border-slate-200 px-2 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                  >
                    {currencyOptions.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.code} ({c.symbol})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Budget ({getCurrencySymbol(editForm.currency || 'USD')})
                  </label>
                  <input
                    type="number"
                    min="1"
                    step="50"
                    value={editForm.budget}
                    onChange={(e) =>
                      setEditForm({ ...editForm, budget: Number(e.target.value) })
                    }
                    className="w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-800 outline-none focus:border-violet-500"
                  />
                </div>
              </div>

              <div className="mt-5 flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingTrip(null)}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-white shadow-xs"
                  style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' }}
                >
                  {savingEdit ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

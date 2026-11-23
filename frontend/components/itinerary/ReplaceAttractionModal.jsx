import { useEffect, useState } from 'react'
import { X, Sparkles, MapPin, Clock, Wallet, CloudSun, RefreshCw, Check } from 'lucide-react'
import { api, getToken } from '../../services/api.js'

const REASONS = [
  { value: 'user_preference', label: 'Change of preference' },
  { value: 'bad_weather', label: 'Unsuitable / rainy weather' },
  { value: 'budget_overrun', label: 'Lower cost / over budget' },
  { value: 'excessive_travel_time', label: 'Too far / excessive travel time' },
  { value: 'unavailable', label: 'Attraction closed or unavailable' },
]

export default function ReplaceAttractionModal({
  tripId,
  dayNumber,
  activity,
  onClose,
  onReplaced,
}) {
  const [reason, setReason] = useState('user_preference')
  const [maxBudget, setMaxBudget] = useState('')
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState('')
  const [data, setData] = useState(null)

  const fetchAlternatives = async (overrideReason = reason) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.findAlternatives(
        tripId,
        {
          attraction_id: activity?.attraction_id,
          day_number: dayNumber,
          time_slot: activity?.time_slot,
          attraction_name: activity?.name,
          reason: overrideReason,
          max_budget: maxBudget ? Number(maxBudget) : undefined,
          limit: 5,
        },
        getToken()
      )
      setData(res)
    } catch (err) {
      setError(err.message || 'Unable to fetch alternative attractions.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlternatives(reason)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSelectAlternative = async (alt) => {
    setApplying(true)
    setError('')
    try {
      const res = await api.replaceAttraction(
        tripId,
        {
          attraction_id: activity?.attraction_id,
          day_number: dayNumber,
          time_slot: activity?.time_slot,
          replacement: alt,
          reason,
        },
        getToken()
      )
      if (onReplaced) {
        onReplaced(res.itinerary)
      }
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to apply attraction replacement.')
    } finally {
      setApplying(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-2xl max-h-[88vh] overflow-y-auto rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-100 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 px-6 py-4 backdrop-blur-xs">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles size={16} className="text-violet-600 dark:text-violet-400" />
              Smart Alternative Recommendations
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Day {dayNumber} · {activity?.time_slot} — Replacing <strong className="text-slate-800 dark:text-slate-200">{activity?.name}</strong>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-200 cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Controls */}
        <div className="px-6 py-4 bg-slate-50/70 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800 grid sm:grid-cols-3 gap-3 items-end">
          <div className="sm:col-span-1">
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
              Reason for Replacement
            </label>
            <select
              value={reason}
              onChange={(e) => {
                const val = e.target.value
                setReason(val)
                fetchAlternatives(val)
              }}
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-violet-500"
            >
              {REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
              Max Cost Filter (Optional)
            </label>
            <input
              type="number"
              min="0"
              value={maxBudget}
              onChange={(e) => setMaxBudget(e.target.value)}
              placeholder="e.g. 500"
              className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-violet-500"
            />
          </div>

          <button
            type="button"
            onClick={() => fetchAlternatives(reason)}
            disabled={loading}
            className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-700 disabled:opacity-60 transition-colors cursor-pointer"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Ranking…' : 'Refresh Ranking'}</span>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 dark:border-rose-900/60 dark:bg-rose-950/40 p-3 text-xs text-rose-700 dark:text-rose-300">
              {error}
            </div>
          )}

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-28 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 animate-pulse" />
              ))}
            </div>
          ) : data?.alternatives?.length > 0 ? (
            <div className="space-y-3">
              {data.alternatives.map((alt, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-200/90 dark:border-slate-700/80 bg-white dark:bg-slate-800/70 p-4 hover:border-violet-300 dark:hover:border-violet-500/50 transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">
                          {alt.name}
                        </h4>
                        <span className="rounded-full bg-violet-100 dark:bg-violet-950/80 border border-violet-200 dark:border-violet-700 px-2 py-0.5 text-[10px] font-bold text-violet-800 dark:text-violet-300">
                          Suitability: {alt.suitability_score}/100
                        </span>
                        {alt.is_indoor && (
                          <span className="rounded-full bg-emerald-100 dark:bg-emerald-950/80 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 dark:text-emerald-300">
                            Indoor / Sheltered
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                        {alt.description}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-slate-500 dark:text-slate-400">
                        <span className="inline-flex items-center gap-1">
                          <Wallet size={12} className="text-emerald-500" />
                          {alt.estimated_cost || 'Free / Included'}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <MapPin size={12} className="text-blue-500" />
                          {alt.distance_km !== null && alt.distance_km !== undefined
                            ? `${alt.distance_km} km away`
                            : 'Distance unavailable'}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Clock size={12} className="text-indigo-500" />
                          Travel: {alt.estimated_travel_time} · Visit: {alt.estimated_duration}
                        </span>
                      </div>

                      <p className="text-[11px] text-violet-700 dark:text-violet-300 bg-violet-50/80 dark:bg-violet-950/40 rounded-lg px-2.5 py-1.5 mt-2">
                        <CloudSun size={11} className="inline mr-1" />
                        {alt.selection_explanation}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleSelectAlternative(alt)}
                      disabled={applying}
                      className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-slate-900 dark:bg-violet-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-800 dark:hover:bg-violet-700 disabled:opacity-60 transition-colors shrink-0 cursor-pointer"
                    >
                      <Check size={13} />
                      <span>{applying ? 'Applying…' : 'Select & Replace'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 p-6 text-center text-xs text-slate-500 dark:text-slate-400">
              {data?.message || 'No suitable alternative attractions found for the current filters.'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

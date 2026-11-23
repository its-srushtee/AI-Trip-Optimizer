import { useState } from 'react'
import {
  Sliders,
  Play,
  Check,
  X,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
} from 'lucide-react'
import { api, getToken } from '../../services/api.js'
import { formatCurrency } from '../../lib/constants.js'

const SCENARIOS = [
  { value: 'add_day', label: 'Add Extra Day(s)' },
  { value: 'remove_day', label: 'Remove a Day' },
  { value: 'increase_budget', label: 'Increase Budget' },
  { value: 'decrease_budget', label: 'Reduce Budget' },
  { value: 'change_transport', label: 'Switch Transport (Flight / Train)' },
  { value: 'remove_attraction', label: 'Remove an Attraction' },
  { value: 'change_preferences', label: 'Change Travel Style / Pace' },
]

export default function WhatIfSimulator({ trip, itinerary, onApplied }) {
  const [open, setOpen] = useState(false)
  const [scenario, setScenario] = useState('add_day')
  const [daysDelta, setDaysDelta] = useState(1)
  const [budgetDelta, setBudgetDelta] = useState(5000)
  const [transportMode, setTransportMode] = useState('Train')
  const [selectedAttractionId, setSelectedAttractionId] = useState('')
  const [newStyle, setNewStyle] = useState('Comfort')
  const [newPace, setNewPace] = useState('Balanced')

  const [simulating, setSimulating] = useState(false)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const allActivities = (itinerary?.days || []).flatMap((d) =>
    (d.activities || []).map((a) => ({
      id: a.attraction_id || `day-${d.day}-${(a.time_slot || '').toLowerCase()}`,
      label: `Day ${d.day} (${a.time_slot}): ${a.name}`,
    }))
  )

  const buildParams = () => {
    if (scenario === 'add_day') return { days_delta: Number(daysDelta) || 1 }
    if (scenario === 'remove_day') return {}
    if (scenario === 'increase_budget' || scenario === 'decrease_budget') {
      return { budget_delta: Math.abs(Number(budgetDelta) || 1000) }
    }
    if (scenario === 'change_transport') return { transport_mode: transportMode }
    if (scenario === 'remove_attraction') {
      return { attraction_id: selectedAttractionId || allActivities[0]?.id }
    }
    if (scenario === 'change_preferences') {
      return { style: newStyle, pace: newPace }
    }
    return {}
  }

  const handleSimulate = async () => {
    setSimulating(true)
    setError('')
    try {
      const res = await api.simulateTripChanges(
        trip.id,
        { scenario, params: buildParams() },
        getToken()
      )
      setResult(res)
    } catch (err) {
      setError(err.message || 'Simulation failed.')
    } finally {
      setSimulating(false)
    }
  }

  const handleApply = async () => {
    setApplying(true)
    setError('')
    try {
      const res = await api.applyTripSimulation(
        trip.id,
        { scenario, params: buildParams() },
        getToken()
      )
      setResult(null)
      setOpen(false)
      if (onApplied) {
        onApplied(res)
      }
    } catch (err) {
      setError(err.message || 'Failed to apply simulation.')
    } finally {
      setApplying(false)
    }
  }

  const curr = (result?.currency || itinerary?.currency || trip?.currency || 'USD').toUpperCase()

  return (
    <div className="rounded-2xl border border-indigo-200/80 dark:border-indigo-900/60 bg-gradient-to-br from-indigo-50/70 via-white to-violet-50/40 dark:from-indigo-950/30 dark:via-slate-900 dark:to-slate-900 p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-indigo-100 dark:bg-indigo-900/60 text-indigo-600 dark:text-indigo-300 flex items-center justify-center shrink-0">
            <Sliders size={17} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <span>What-If Trip Simulator</span>
              <span className="rounded-full bg-indigo-100 dark:bg-indigo-900/70 px-2 py-0.5 text-[10px] font-bold text-indigo-700 dark:text-indigo-300">
                Non-Destructive
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Preview how extra days, budget shifts, or transport switches impact cost and feasibility before saving.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-700 transition-colors self-start sm:self-auto cursor-pointer"
        >
          <Sparkles size={13} />
          <span>{open ? 'Hide Simulator' : 'What If? Simulate Changes'}</span>
        </button>
      </div>

      {open && (
        <div className="mt-4 pt-4 border-t border-indigo-100 dark:border-slate-800 space-y-4">
          <div className="grid sm:grid-cols-3 gap-3 items-end">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                Scenario
              </label>
              <select
                value={scenario}
                onChange={(e) => {
                  setScenario(e.target.value)
                  setResult(null)
                }}
                className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-indigo-500"
              >
                {SCENARIOS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              {scenario === 'add_day' && (
                <>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                    Extra Days
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="7"
                    value={daysDelta}
                    onChange={(e) => setDaysDelta(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100"
                  />
                </>
              )}

              {(scenario === 'increase_budget' || scenario === 'decrease_budget') && (
                <>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                    Budget Change Amount ({curr})
                  </label>
                  <input
                    type="number"
                    min="100"
                    value={budgetDelta}
                    onChange={(e) => setBudgetDelta(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100"
                  />
                </>
              )}

              {scenario === 'change_transport' && (
                <>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                    Target Transport Mode
                  </label>
                  <select
                    value={transportMode}
                    onChange={(e) => setTransportMode(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100"
                  >
                    <option value="Train">Train / Rail</option>
                    <option value="Flight">Flight</option>
                  </select>
                </>
              )}

              {scenario === 'remove_attraction' && (
                <>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">
                    Attraction to Remove
                  </label>
                  <select
                    value={selectedAttractionId || allActivities[0]?.id || ''}
                    onChange={(e) => setSelectedAttractionId(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-xs text-slate-800 dark:text-slate-100"
                  >
                    {allActivities.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                </>
              )}

              {scenario === 'change_preferences' && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate-500 dark:text-slate-400 mb-1">
                      Style
                    </label>
                    <select
                      value={newStyle}
                      onChange={(e) => setNewStyle(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-2 text-xs text-slate-800 dark:text-slate-100"
                    >
                      <option value="Budget">Budget</option>
                      <option value="Comfort">Comfort</option>
                      <option value="Luxury">Luxury</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate-500 dark:text-slate-400 mb-1">
                      Pace
                    </label>
                    <select
                      value={newPace}
                      onChange={(e) => setNewPace(e.target.value)}
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-2.5 py-2 text-xs text-slate-800 dark:text-slate-100"
                    >
                      <option value="Relaxed">Relaxed</option>
                      <option value="Balanced">Balanced</option>
                      <option value="Fast">Fast</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleSimulate}
              disabled={simulating}
              className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-slate-900 dark:bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 dark:hover:bg-indigo-700 disabled:opacity-60 transition-colors cursor-pointer"
            >
              <Play size={13} />
              <span>{simulating ? 'Simulating…' : 'Run Simulation'}</span>
            </button>
          </div>

          {error && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 dark:border-rose-900/60 dark:bg-rose-950/40 p-3 text-xs text-rose-700 dark:text-rose-300">
              {error}
            </div>
          )}

          {result && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    Simulation Preview: {result.change_description}
                  </span>
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                    result.feasibility_status === 'Feasible'
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300'
                      : result.feasibility_status === 'Tight'
                      ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300'
                      : 'bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300'
                  }`}
                >
                  {result.feasibility_status === 'Feasible' ? <CheckCircle2 size={11} /> : <AlertTriangle size={11} />}
                  {result.feasibility_status}
                </span>
              </div>

              <div className="grid sm:grid-cols-4 gap-3 text-xs">
                <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Estimated Total Cost</span>
                  <div className="mt-1 font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <span>{formatCurrency(result.original_total_cost, curr)}</span>
                    <ArrowRight size={12} className="text-slate-400" />
                    <span className="text-indigo-600 dark:text-indigo-400">
                      {formatCurrency(result.simulated_total_cost, curr)}
                    </span>
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Budget Difference</span>
                  <div className={`mt-1 font-bold ${result.budget_difference <= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                    {result.budget_difference > 0 ? '+' : ''}
                    {formatCurrency(result.budget_difference, curr)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Trip Duration</span>
                  <div className="mt-1 font-bold text-slate-900 dark:text-white">
                    {result.original_duration_days}d <ArrowRight size={11} className="inline text-slate-400" /> {result.simulated_duration_days}d
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 dark:bg-slate-800/70 p-3">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Attractions</span>
                  <div className="mt-1 font-bold text-slate-900 dark:text-white">
                    {result.original_attraction_count} <ArrowRight size={11} className="inline text-slate-400" /> {result.simulated_attraction_count}
                  </div>
                </div>
              </div>

              {result.transportation_changes && result.transportation_changes !== 'No transportation changes.' && (
                <p className="text-xs text-slate-600 dark:text-slate-300">
                  <strong>Transportation:</strong> {result.transportation_changes} ({result.original_travel_duration} → {result.simulated_travel_duration})
                </p>
              )}

              {result.warnings?.length > 0 && (
                <div className="rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 p-2.5 text-[11px] text-amber-900 dark:text-amber-200 space-y-1">
                  {result.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-1.5">
                      <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 rounded-lg p-2.5">
                <strong>AI Assessment:</strong> {result.recommendation}
              </p>

              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setResult(null)}
                  className="inline-flex items-center gap-1 rounded-xl border border-slate-200 dark:border-slate-700 px-3.5 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
                >
                  <X size={13} />
                  <span>Discard</span>
                </button>
                <button
                  type="button"
                  onClick={handleApply}
                  disabled={applying}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-60 cursor-pointer"
                >
                  <Check size={13} />
                  <span>{applying ? 'Applying…' : 'Apply Changes'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

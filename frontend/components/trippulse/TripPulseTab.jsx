import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  CloudSun,
  CloudRain,
  DollarSign,
  Sparkles,
  RefreshCw,
  RotateCcw,
  Shield,
  ArrowRight,
  Clock,
  Compass,
  Sliders,
  Check,
  X,
  ExternalLink,
  Info,
} from 'lucide-react'
import { api, getToken } from '../../services/api.js'

export default function TripPulseTab({ trip, onTripUpdated }) {
  const [pulseData, setPulseData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [simulating, setSimulating] = useState(false)
  const [applying, setApplying] = useState(false)
  const [rollingBack, setRollingBack] = useState(false)
  const [selectedSimType, setSelectedSimType] = useState('heavy_rain')
  const [selectedDay, setSelectedDay] = useState(2)
  const [showSimModal, setShowSimModal] = useState(false)
  const [selectedModIds, setSelectedModIds] = useState([])
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  const token = getToken()

  const fetchPulse = async () => {
    if (!trip?.id) return
    try {
      setLoading(true)
      const data = await api.getTripPulse(trip.id, token)
      setPulseData(data)
      if (data?.pending_proposal?.diff_summary?.modifications) {
        setSelectedModIds(
          data.pending_proposal.diff_summary.modifications.map((m) => m.id)
        )
      }
    } catch (err) {
      console.error('Failed to load TripPulse data:', err)
      setErrorMsg('Could not fetch real-time TripPulse status.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPulse()
  }, [trip?.id])

  const handleSimulate = async () => {
    try {
      setSimulating(true)
      setErrorMsg('')
      setSuccessMsg('')
      const updatedPulse = await api.simulateDisruption(
        trip.id,
        {
          simulation_type: selectedSimType,
          affected_day: parseInt(selectedDay, 10),
          severity: 'red',
        },
        token
      )
      setPulseData(updatedPulse)
      if (updatedPulse?.pending_proposal?.diff_summary?.modifications) {
        setSelectedModIds(
          updatedPulse.pending_proposal.diff_summary.modifications.map((m) => m.id)
        )
      }
      setShowSimModal(false)
      setSuccessMsg(
        `Simulated disruption triggered on Day ${selectedDay}. Adaptive re-optimization proposal is ready for review.`
      )
    } catch (err) {
      console.error('Simulation failed:', err)
      setErrorMsg(err.message || 'Disruption simulation failed.')
    } finally {
      setSimulating(false)
    }
  }

  const handleApplyChanges = async (applyAll = false) => {
    const proposal = pulseData?.pending_proposal
    if (!proposal?.id) return

    try {
      setApplying(true)
      setErrorMsg('')
      const idsToApply = applyAll
        ? (proposal.diff_summary?.modifications || []).map((m) => m.id)
        : selectedModIds

      const res = await api.applyReoptimization(
        trip.id,
        proposal.id,
        { accepted_modification_ids: idsToApply },
        token
      )
      setSuccessMsg(res.message || 'Itinerary successfully updated with approved changes!')
      setPulseData(res.pulse)
      if (onTripUpdated) {
        onTripUpdated()
      }
    } catch (err) {
      console.error('Apply re-optimization failed:', err)
      setErrorMsg(err.message || 'Failed to apply re-optimization.')
    } finally {
      setApplying(false)
    }
  }

  const handleRollback = async (reoptId) => {
    if (!reoptId) return
    try {
      setRollingBack(true)
      setErrorMsg('')
      const res = await api.rollbackReoptimization(trip.id, reoptId, token)
      setSuccessMsg(res.message || 'Rolled back itinerary to original baseline.')
      setPulseData(res.pulse)
      if (onTripUpdated) {
        onTripUpdated()
      }
    } catch (err) {
      console.error('Rollback failed:', err)
      setErrorMsg(err.message || 'Failed to rollback itinerary.')
    } finally {
      setRollingBack(false)
    }
  }

  const handleDismissAlert = async (alertId) => {
    try {
      await api.dismissAlert(trip.id, alertId, token)
      setPulseData((prev) => ({
        ...prev,
        alerts: (prev?.alerts || []).filter((a) => a.id !== alertId),
      }))
    } catch (err) {
      console.error('Dismiss alert failed:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-500">
        <RefreshCw size={28} className="animate-spin text-violet-600 mb-3" />
        <p className="text-sm font-semibold">Connecting to TripPulse AI Engine…</p>
        <p className="text-xs text-slate-400 mt-1">Analyzing weather norms, budget adherence, and itinerary status.</p>
      </div>
    )
  }

  const healthScore = pulseData?.health_score ?? 100
  const healthStatus = pulseData?.health_status ?? 'green'
  const weather = pulseData?.weather || {}
  const budget = pulseData?.budget || {}
  const alerts = pulseData?.alerts || []
  const pendingProposal = pulseData?.pending_proposal
  const history = pulseData?.history || []

  // Color mappings
  const statusColor =
    healthStatus === 'green'
      ? 'text-emerald-600 bg-emerald-50 border-emerald-200'
      : healthStatus === 'yellow'
      ? 'text-amber-600 bg-amber-50 border-amber-200'
      : 'text-rose-600 bg-rose-50 border-rose-200'

  const scoreRingColor =
    healthStatus === 'green'
      ? 'border-emerald-500 text-emerald-600'
      : healthStatus === 'yellow'
      ? 'border-amber-500 text-amber-600'
      : 'border-rose-500 text-rose-600'

  return (
    <div className="space-y-6">
      {/* Notifications */}
      {successMsg && (
        <div className="flex items-center justify-between rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-emerald-800 text-xs font-semibold shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button type="button" onClick={() => setSuccessMsg('')} className="text-emerald-600 hover:text-emerald-800">
            <X size={14} />
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center justify-between rounded-xl bg-rose-50 border border-rose-200 p-4 text-rose-800 text-xs font-semibold shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button type="button" onClick={() => setErrorMsg('')} className="text-rose-600 hover:text-rose-800">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main Health Score & Action Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            {/* Health Score Gauge */}
            <div className={`relative flex h-20 w-20 shrink-0 items-center justify-center rounded-full border-4 ${scoreRingColor} bg-slate-50 font-black text-2xl shadow-inner`}>
              {healthScore}
              <span className="absolute bottom-1 text-[9px] font-bold uppercase tracking-wider text-slate-400">
                Health
              </span>
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">TripPulse AI Health Monitor</h2>
                <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide border ${statusColor}`}>
                  {healthStatus === 'green' && <CheckCircle2 size={12} />}
                  {healthStatus === 'yellow' && <AlertTriangle size={12} />}
                  {healthStatus === 'red' && <AlertCircle size={12} />}
                  {healthStatus === 'green' ? 'All On Track' : healthStatus === 'yellow' ? 'Attention Needed' : 'Disruption Detected'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-xl">
                Continuous real-time travel intelligence tracking live weather, schedule feasibility, and budget deviations for <strong className="text-slate-800">{trip.destination}</strong>.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={fetchPulse}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors"
            >
              <RefreshCw size={13} />
              Refresh Status
            </button>

            <button
              type="button"
              onClick={() => setShowSimModal(true)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-violet-700 transition-colors"
            >
              <Sliders size={13} />
              Simulate Disruption (Demo)
            </button>
          </div>
        </div>
      </div>

      {/* Disruption Simulator Modal */}
      {showSimModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sliders size={16} className="text-violet-600" />
                <h3 className="text-sm font-bold text-slate-900">Manual Disruption Simulation Mode</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowSimModal(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              >
                <X size={16} />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <p className="text-xs text-slate-500 leading-relaxed">
                For development and demonstrations, simulate real-world travel disruptions. TripPulse AI will detect affected activities, query live APIs for sheltered alternatives, and formulate an adaptive proposal.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Disruption Scenario
                </label>
                <select
                  value={selectedSimType}
                  onChange={(e) => setSelectedSimType(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-violet-500 focus:bg-white focus:outline-hidden"
                >
                  <option value="heavy_rain">Heavy Rainfall & Storm (Weather Alert)</option>
                  <option value="activity_cancelled">Activity Venue Closure / Maintenance</option>
                  <option value="transport_delay">Transit & Connection Disruption</option>
                  <option value="budget_overrun">Unexpected Budget Deviation Alert</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Affected Itinerary Day
                </label>
                <input
                  type="number"
                  min="1"
                  max="14"
                  value={selectedDay}
                  onChange={(e) => setSelectedDay(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-violet-500 focus:bg-white focus:outline-hidden"
                />
              </div>

              <div className="rounded-xl bg-violet-50/80 border border-violet-100 p-3 text-[11px] text-violet-700 flex items-start gap-2">
                <Info size={14} className="shrink-0 mt-0.5 text-violet-600" />
                <span>
                  Simulated alerts are clearly distinguished with a purple simulation tag and never modify your original itinerary without your approval.
                </span>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2 border-t border-slate-100 pt-3">
              <button
                type="button"
                onClick={() => setShowSimModal(false)}
                className="rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSimulate}
                disabled={simulating}
                className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-700 disabled:opacity-50"
              >
                {simulating && <RefreshCw size={12} className="animate-spin" />}
                {simulating ? 'Generating Re-Optimization…' : 'Trigger Simulation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4 Pillars Status Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Weather Conditions */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span className="flex items-center gap-1.5">
              <CloudSun size={14} className="text-amber-500" />
              Weather Intelligence
            </span>
            <span className="text-[11px] font-bold text-slate-800">{weather.temp_range || '22°C'}</span>
          </div>
          <h4 className="mt-2 text-sm font-bold text-slate-900">{weather.condition || 'Clear & Sunny'}</h4>
          <p className="mt-1 text-[11px] text-slate-500 line-clamp-2">
            {weather.packing_advice || 'Favorable travel climate for outdoor sightseeing and walks.'}
          </p>
        </div>

        {/* Budget Status */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span className="flex items-center gap-1.5">
              <DollarSign size={14} className="text-emerald-500" />
              Budget Health
            </span>
            <span className={`text-[10px] font-bold uppercase rounded-md px-1.5 py-0.5 ${
              budget.status === 'on_track' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
            }`}>
              {budget.status === 'on_track' ? 'On Track' : 'Review Needed'}
            </span>
          </div>
          <h4 className="mt-2 text-sm font-bold text-slate-900">
            {budget.currency_symbol || '₹'}{budget.total_spent?.toLocaleString() || '0'} spent
          </h4>
          <p className="mt-1 text-[11px] text-slate-500">
            Target: {budget.currency_symbol || '₹'}{budget.target_budget?.toLocaleString() || trip.budget} ({budget.spent_percentage || 0}% allocated)
          </p>
        </div>

        {/* Active Alerts Count */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span className="flex items-center gap-1.5">
              <AlertTriangle size={14} className="text-rose-500" />
              Active Disruptions
            </span>
            <span className={`text-[10px] font-bold uppercase rounded-md px-1.5 py-0.5 ${
              alerts.length === 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
            }`}>
              {alerts.length} Active
            </span>
          </div>
          <h4 className="mt-2 text-sm font-bold text-slate-900">
            {alerts.length === 0 ? 'Zero Disruptions' : `${alerts.length} Alert(s) Recorded`}
          </h4>
          <p className="mt-1 text-[11px] text-slate-500">
            {alerts.length === 0 ? 'All scheduled days and transit links clear.' : 'See active alerts below.'}
          </p>
        </div>

        {/* Re-Optimization Status */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span className="flex items-center gap-1.5">
              <Sparkles size={14} className="text-violet-500" />
              Adaptive Engine
            </span>
            <span className="text-[10px] font-bold uppercase rounded-md bg-violet-100 text-violet-700 px-1.5 py-0.5">
              {pendingProposal ? 'Proposal Ready' : 'Standby'}
            </span>
          </div>
          <h4 className="mt-2 text-sm font-bold text-slate-900">
            {pendingProposal ? 'Action Required' : 'Itinerary Optimized'}
          </h4>
          <p className="mt-1 text-[11px] text-slate-500">
            {pendingProposal ? 'Review AI alternative proposal below.' : 'Monitoring for schedule changes.'}
          </p>
        </div>
      </div>

      {/* Active Alerts List */}
      {alerts.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-500" />
              Active Travel Alerts & Potential Disruptions
            </h3>
            <span className="text-xs text-slate-400">{alerts.length} alert(s)</span>
          </div>

          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border p-4 text-xs transition-colors ${
                  alert.is_simulated
                    ? 'border-purple-200 bg-purple-50/60 text-purple-950'
                    : alert.severity === 'red'
                    ? 'border-rose-200 bg-rose-50/60 text-rose-950'
                    : 'border-amber-200 bg-amber-50/60 text-amber-950'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm">{alert.title}</span>
                    {alert.is_simulated ? (
                      <span className="rounded-full bg-purple-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-purple-800">
                        Simulated Alert (Demo)
                      </span>
                    ) : (
                      <span className="rounded-full bg-rose-200 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-rose-800">
                        Verified External Disruption
                      </span>
                    )}
                  </div>
                  <p className="text-xs opacity-90 leading-relaxed">{alert.explanation}</p>
                  {alert.recommended_action && (
                    <p className="text-[11px] font-medium opacity-80 pt-1">
                      💡 <strong>Recommended Action:</strong> {alert.recommended_action}
                    </p>
                  )}
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleDismissAlert(alert.id)}
                    className="rounded-lg border border-slate-300/80 bg-white/80 px-2.5 py-1.5 text-[11px] font-semibold text-slate-700 hover:bg-white shadow-2xs"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending Re-Optimization Proposal Card */}
      {pendingProposal && (
        <div className="rounded-2xl border-2 border-violet-400 bg-gradient-to-b from-violet-50/50 to-white p-6 shadow-md animate-in fade-in">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-violet-100 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-violet-600 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide text-white">
                  <Sparkles size={11} /> AI Re-Optimization Proposal (Pending Approval)
                </span>
                <span className="text-xs text-slate-500">Version {pendingProposal.version}</span>
              </div>
              <h3 className="mt-1 text-base font-bold text-slate-900">
                Trigger: {pendingProposal.trigger_reason}
              </h3>
              <p className="mt-1 text-xs text-slate-600 leading-relaxed max-w-3xl">
                {pendingProposal.explanation}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => handleApplyChanges(true)}
                disabled={applying}
                className="inline-flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-violet-700 disabled:opacity-50"
              >
                {applying ? <RefreshCw size={13} className="animate-spin" /> : <Check size={13} />}
                Approve All Changes
              </button>
            </div>
          </div>

          {/* Diff / Comparison View */}
          <div className="mt-5 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Proposed Activity Substitutions (Original vs Replacement)
            </h4>

            <div className="space-y-3">
              {(pendingProposal.diff_summary?.modifications || []).map((mod) => {
                const isSelected = selectedModIds.includes(mod.id)
                return (
                  <div
                    key={mod.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-2xs hover:border-violet-300 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedModIds((prev) => [...prev, mod.id])
                          } else {
                            setSelectedModIds((prev) => prev.filter((id) => id !== mod.id))
                          }
                        }}
                        className="mt-1 h-4 w-4 rounded-md border-slate-300 text-violet-600 focus:ring-violet-500"
                      />

                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700">
                            Day {mod.day} · {mod.time_slot}
                          </span>
                          <span className="text-xs text-slate-400">|</span>
                          <span className="text-xs font-semibold text-rose-600 line-through">
                            {mod.original_activity?.name}
                          </span>
                          <ArrowRight size={13} className="text-violet-500" />
                          <span className="text-xs font-bold text-emerald-700">
                            {mod.replacement_activity?.name}
                          </span>
                        </div>

                        <p className="text-[11px] text-slate-500 leading-relaxed">
                          {mod.replacement_activity?.description}
                        </p>
                        <p className="text-[10px] text-slate-400 font-medium">
                          Reason: {mod.reason}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <button
                        type="button"
                        onClick={() => handleApplyChanges(false)}
                        disabled={applying || !isSelected}
                        className="rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-1.5 text-[11px] font-bold text-emerald-700 hover:bg-emerald-100 disabled:opacity-40"
                      >
                        Accept Change
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-violet-100 text-xs text-slate-500">
              <span className="flex items-center gap-1.5 text-[11px]">
                <Shield size={13} className="text-violet-600" />
                Original itinerary is protected. Nothing changes until you click Approve.
              </span>

              {selectedModIds.length > 0 && selectedModIds.length < (pendingProposal.diff_summary?.modifications || []).length && (
                <button
                  type="button"
                  onClick={() => handleApplyChanges(false)}
                  disabled={applying}
                  className="rounded-xl bg-violet-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-violet-700"
                >
                  Apply {selectedModIds.length} Selected Change(s)
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Re-Optimization & Rollback History */}
      {history.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <RotateCcw size={15} className="text-violet-600" />
              Itinerary Version History & Rollback Controls
            </h3>
            <span className="text-xs text-slate-400">{history.length} version(s) recorded</span>
          </div>

          <div className="space-y-3">
            {history.map((record) => (
              <div
                key={record.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/70 p-4 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">Version {record.version}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                      record.status === 'applied'
                        ? 'bg-emerald-100 text-emerald-800'
                        : record.status === 'rolled_back'
                        ? 'bg-slate-200 text-slate-700'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {record.status}
                    </span>
                    {record.is_simulated && (
                      <span className="rounded-full bg-purple-100 text-purple-700 px-2 py-0.5 text-[10px] font-semibold">
                        Simulated
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600">{record.trigger_reason}</p>
                  <p className="text-[11px] text-slate-400">{record.explanation}</p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {record.status === 'applied' && (
                    <button
                      type="button"
                      onClick={() => handleRollback(record.id)}
                      disabled={rollingBack}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-50 shadow-2xs"
                    >
                      <RotateCcw size={12} />
                      Rollback to Previous
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

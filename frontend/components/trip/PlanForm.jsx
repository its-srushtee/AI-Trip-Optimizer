import { CheckCircle2 } from 'lucide-react'
import Button from '../common/Button.jsx'
import { interests, formatCurrency, getTodayDateStr, getNextDayDateStr } from '../../lib/constants.js'

/**
 * The "Create trip" form — fully controlled so the Dashboard and the
 * standalone /create-trip page drive it identically.
 *
 *   form: { destination, start, end, budget, travelers, selected }
 *   onFieldChange(key, value) · onToggleInterest(id) · onSubmit(event)
 *   submitting, justAdded — button states
 *   error — validation message
 */
export default function PlanForm({
  form,
  onFieldChange,
  onToggleInterest,
  onSubmit,
  submitting,
  justAdded,
  error,
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="destination" className="field-label">
          Destination
        </label>
        <input
          id="destination"
          value={form.destination}
          onChange={(e) => onFieldChange('destination', e.target.value)}
          className="input-field"
          placeholder="City or region"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="start" className="field-label">
            Start date
          </label>
          <input
            id="start"
            type="date"
            min={getTodayDateStr()}
            value={form.start}
            onChange={(e) => {
              const newStart = e.target.value
              onFieldChange('start', newStart)
              if (newStart && (!form.end || form.end <= newStart)) {
                onFieldChange('end', getNextDayDateStr(newStart))
              }
            }}
            className="input-field"
          />
        </div>
        <div>
          <label htmlFor="end" className="field-label">
            End date
          </label>
          <input
            id="end"
            type="date"
            min={form.start ? getNextDayDateStr(form.start) : getNextDayDateStr(getTodayDateStr())}
            value={form.end}
            onChange={(e) => onFieldChange('end', e.target.value)}
            className="input-field"
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <div className="mb-1.5 flex items-baseline justify-between">
            <label htmlFor="budget" className="field-label mb-0">
              Budget
            </label>
            <span className="text-[13px] font-medium tabular-nums text-main">
              {formatCurrency(form.budget, form.currency || 'USD')}
            </span>
          </div>
          <input
            id="budget"
            type="range"
            min="500"
            max="20000"
            step="100"
            value={form.budget}
            onChange={(e) => onFieldChange('budget', Number(e.target.value))}
          />
          <div className="mt-1 flex justify-between text-xs text-faint">
            <span>$500</span>
            <span>$20,000</span>
          </div>
        </div>

        <div>
          <span className="field-label">Travelers</span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => onFieldChange('travelers', Math.max(1, form.travelers - 1))}
              className="h-11 w-11 rounded-full border border-subtle bg-panel text-soft transition-colors hv disabled:opacity-40"
              disabled={form.travelers <= 1}
              aria-label="Decrease travelers"
            >
              −
            </button>
            <span className="w-10 text-center text-[15px] font-semibold tabular-nums text-main">
              {form.travelers}
            </span>
            <button
              type="button"
              onClick={() => onFieldChange('travelers', Math.min(12, form.travelers + 1))}
              className="h-11 w-11 rounded-full border border-subtle bg-panel text-soft transition-colors hv disabled:opacity-40"
              disabled={form.travelers >= 12}
              aria-label="Increase travelers"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <div>
        <label className="field-label">
          Interests <span className="font-normal text-faint">— optional</span>
        </label>
        <div className="flex flex-wrap gap-1.5">
          {interests.map((i) => (
            <button
              key={i.id}
              type="button"
              onClick={() => onToggleInterest(i.id)}
              className={`chip-btn ${form.selected.includes(i.id) ? 'chip-on' : ''}`}
            >
              {i.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="alert alert-error">{error}</p>}

      <div className="flex justify-end pt-1">
        <Button type="submit" disabled={submitting}>
          {submitting ? (
            <>
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              Creating…
            </>
          ) : justAdded ? (
            <>
              <CheckCircle2 size={15} /> Trip created
            </>
          ) : (
            'Create Trip'
          )}
        </Button>
      </div>
    </form>
  )
}

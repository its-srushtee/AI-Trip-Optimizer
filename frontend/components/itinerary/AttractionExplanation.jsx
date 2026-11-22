import { useState } from 'react'
import { ChevronDown, ChevronUp, Sparkles, MapPin, Wallet, CloudSun, Clock } from 'lucide-react'

export default function AttractionExplanation({ activity, onFindAlternative }) {
  const [expanded, setExpanded] = useState(false)
  const exp = activity?.recommendation_explanation

  return (
    <div className="mt-2.5 pt-2 border-t border-slate-200/70 dark:border-slate-700/70 space-y-2">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {exp ? (
          <button
            type="button"
            onClick={() => setExpanded((prev) => !prev)}
            className="inline-flex items-center gap-1 text-[11px] font-semibold text-violet-700 dark:text-violet-300 hover:text-violet-900 dark:hover:text-violet-200 cursor-pointer"
          >
            <Sparkles size={11} />
            <span>Why Recommended?</span>
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        ) : (
          <span className="text-[10px] text-slate-400">AI curated</span>
        )}

        {onFindAlternative && (
          <button
            type="button"
            onClick={onFindAlternative}
            className="inline-flex items-center gap-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-900/70 px-2 py-0.5 text-[10px] font-semibold text-slate-700 dark:text-slate-200 hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-300 transition-colors cursor-pointer"
          >
            Find Alternative
          </button>
        )}
      </div>

      {expanded && exp && (
        <div className="rounded-lg bg-white/90 dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-700/80 p-2.5 text-[11px] space-y-1.5 text-slate-700 dark:text-slate-200">
          {exp.summary && (
            <p className="font-medium text-slate-900 dark:text-white leading-snug">
              {exp.summary}
            </p>
          )}
          <div className="space-y-1 pt-1 border-t border-slate-100 dark:border-slate-800 text-[10px]">
            <div className="flex items-start gap-1.5">
              <Sparkles size={10} className="text-violet-500 shrink-0 mt-0.5" />
              <span><strong>Preferences:</strong> {exp.preference_match}</span>
            </div>
            <div className="flex items-start gap-1.5">
              <MapPin size={10} className="text-blue-500 shrink-0 mt-0.5" />
              <span><strong>Location:</strong> {exp.location_reason}</span>
            </div>
            <div className="flex items-start gap-1.5">
              <Wallet size={10} className="text-emerald-500 shrink-0 mt-0.5" />
              <span><strong>Budget:</strong> {exp.budget_reason}</span>
            </div>
            <div className="flex items-start gap-1.5">
              <CloudSun size={10} className="text-amber-500 shrink-0 mt-0.5" />
              <span><strong>Weather:</strong> {exp.weather_reason}</span>
            </div>
            <div className="flex items-start gap-1.5">
              <Clock size={10} className="text-indigo-500 shrink-0 mt-0.5" />
              <span><strong>Timing:</strong> {exp.time_reason}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { formatRange } from '../../lib/format.js'
import { interests } from '../../lib/constants.js'

export default function ItineraryView({ itinerary }) {
  if (!itinerary) return null
  const b = itinerary.budget_breakdown || {}

  const rows = [
    ['Flights', b.flights],
    ['Stay', b.stay],
    ['Food', b.food],
    ['Activities', b.activities],
  ]

  return (
    <div className="space-y-5">
      
      <section className="card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-main">
              {itinerary.destination}
            </h2>
            <p className="mt-0.5 text-[13px] text-mut">
              {formatRange(itinerary.dates?.start, itinerary.dates?.end)}
              {itinerary.dates?.nights ? ` · ${itinerary.dates.nights} nights` : ''}
              {itinerary.travelers ? ` · ${itinerary.travelers} traveler${itinerary.travelers > 1 ? 's' : ''}` : ''}
            </p>
          </div>
          <div className="text-right">
            <p className="eyebrow">Total budget</p>
            <p className="text-lg font-semibold tabular-nums text-main">
              ${Number(itinerary.budget).toLocaleString()}
            </p>
          </div>
        </div>

        {itinerary.summary && (
          <p className="mt-3 border-t border-subtle pt-3 text-[13px] leading-relaxed text-mut">
            {itinerary.summary}
          </p>
        )}

        {itinerary.interests?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {itinerary.interests.map((id) => {
              const it = interests.find((x) => x.id === id)
              return it ? (
                <span key={id} className="tag">
                  {it.label}
                </span>
              ) : null
            })}
          </div>
        )}
      </section>

      <section className="card p-5">
        <h3 className="section-title">Budget breakdown</h3>
        <dl className="mt-3">
          {rows.map(([label, value]) => (
            <div
              key={label}
              className="flex items-center justify-between border-b border-subtle py-2 text-[13px] last:border-0"
            >
              <dt className="text-mut">{label}</dt>
              <dd className="font-medium tabular-nums text-soft">
                ${Number(value || 0).toLocaleString()}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h3 className="section-title mb-3">Day by day</h3>
        <ol className="space-y-3">
          {(itinerary.days || []).map((d) => (
            <li key={d.day} className="card p-4">
              <div className="flex items-baseline justify-between gap-3">
                <div className="flex items-baseline gap-2.5">
                  <span className="text-[13px] font-semibold tabular-nums text-faint">
                    Day {d.day}
                  </span>
                  <span className="text-[14px] font-medium text-main">{d.theme}</span>
                </div>
                <span className="shrink-0 text-[13px] tabular-nums text-mut">
                  {d.date} · ${d.estimate_usd}
                </span>
              </div>

              <dl className="mt-2.5 space-y-1 text-[13px]">
                {[
                  ['Morning', d.morning],
                  ['Afternoon', d.afternoon],
                  ['Evening', d.evening],
                ].map(([when, what]) => (
                  <div key={when} className="flex gap-2">
                    <dt className="w-20 shrink-0 text-faint">{when}</dt>
                    <dd className="text-soft">{what}</dd>
                  </div>
                ))}
              </dl>
            </li>
          ))}
        </ol>
      </section>
    </div>
  )
}

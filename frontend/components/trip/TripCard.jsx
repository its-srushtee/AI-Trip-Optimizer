import { Trash2 } from 'lucide-react'
import { interests } from '../../lib/constants.js'
import { formatRange, daysBetween, formatCurrency } from '../../lib/format.js'

/**
 * One saved trip — shared by the Dashboard grid and the /trips page.
 *
 * Editorial layout: a tall photo header carries the destination name, and the
 * facts below are labelled stat pairs (value over label) rather than a run-on
 * metadata line — the pattern from the reference designs.
 */
export default function TripCard({ trip, image, credit, onRemove }) {
  const nights = daysBetween(trip.start_date, trip.end_date)

  return (
    <article className="card card-hover group overflow-hidden">
      <div className="photo-card scrim relative h-40 rounded-none">
        <img
          src={image}
          alt={trip.destination || ''}
          referrerPolicy="no-referrer"
          onError={(e) => {
            e.currentTarget.onerror = null
            e.currentTarget.src = '/images/hero.jpg'
          }}
        />
        {/* Creative Commons attribution (TASL: Title, Author, Source, Licence).
            Note: no (c) symbol - these are openly licensed, not all-rights-
            reserved, and the licence name must be visible, not hover-only. */}
        {credit?.credit && (
          <div
            className="absolute bottom-1 right-2 z-10 max-w-[85%] truncate text-[10px] leading-tight text-white/60"
            style={{ textShadow: '0 1px 3px rgba(0,0,0,.95)' }}
          >
            <a
              href={credit.url || undefined}
              target="_blank"
              rel="noreferrer nofollow"
              className="hover:text-white/90 hover:underline"
            >
              {credit.credit}
            </a>
            {credit.source_name && (
              <>
                {' on '}
                <a
                  href={credit.source_url || undefined}
                  target="_blank"
                  rel="noreferrer nofollow"
                  className="hover:text-white/90 hover:underline"
                >
                  {credit.source_name}
                </a>
              </>
            )}
            {credit.license && (
              <>
                {' / '}
                <a
                  href={credit.license_url || undefined}
                  target="_blank"
                  rel="noreferrer nofollow license"
                  className="hover:text-white/90 hover:underline"
                >
                  {credit.license}
                </a>
              </>
            )}
          </div>
        )}

        <button
          onClick={() => onRemove(trip.id)}
          className="absolute right-3 top-3 z-10 grid h-11 w-11 place-items-center rounded-full opacity-0 transition focus:opacity-100 group-hover:opacity-100 max-[1023px]:opacity-100 lg:h-9 lg:w-9"
          style={{ background: 'rgba(10,10,12,0.6)', color: '#fff' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--danger)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#fff')}
          aria-label={`Delete trip to ${trip.destination}`}
        >
          <Trash2 size={14} />
        </button>

        <div className="absolute inset-x-0 bottom-0 z-10 flex items-end justify-between gap-2 p-4">
          <h3 className="display-sm min-w-0 truncate text-[1.25rem] text-white sm:text-[1.5rem]">
            {trip.destination}
          </h3>
          <span className="status shrink-0">{trip.status}</span>
        </div>
      </div>

      <div className="p-4">
        {/* labelled stat pairs */}
        <div className="grid grid-cols-3 gap-2 sm:gap-3">
          <div>
            <p className="stat-value">{nights > 0 ? `${nights} days` : '—'}</p>
            <p className="stat-label">Duration</p>
          </div>
          <div>
            <p className="stat-value">{trip.travelers}</p>
            <p className="stat-label">Traveler{trip.travelers > 1 ? 's' : ''}</p>
          </div>
          <div>
            <p className="stat-value tabular-nums">
              {formatCurrency(trip.budget, trip.currency || trip.preferences?.currency)}
            </p>
            <p className="stat-label">Budget</p>
          </div>
        </div>

        <p className="mt-3 border-t border-subtle pt-3 text-[13px] text-mut">
          {formatRange(trip.start_date, trip.end_date)}
        </p>

        {trip.interests?.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {trip.interests.slice(0, 4).map((id) => {
              const it = interests.find((x) => x.id === id)
              return it ? (
                <span key={id} className="tag">
                  {it.label}
                </span>
              ) : null
            })}
          </div>
        )}
      </div>
    </article>
  )
}

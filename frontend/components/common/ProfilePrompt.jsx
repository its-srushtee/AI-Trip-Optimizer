import { Link } from 'react-router-dom'
import { X } from 'lucide-react'

/**
 * Shown on the dashboard when a signed-in user hasn't set their travel
 * preferences yet. Dismissible, and gone for good once the profile is complete.
 */
export default function ProfilePrompt({ onDismiss }) {
  return (
    <div
      className="flex flex-col gap-3 rounded-md border p-3.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
      style={{ borderColor: 'var(--accent-border)', backgroundColor: 'var(--accent-soft)' }}
    >
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-main">
          Complete your profile to get personalized trip recommendations.
        </p>
        <p className="mt-0.5 text-[13px] text-mut">
          Set your travel style and interests — about a minute.
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Link
          to="/complete-profile"
          className="inline-flex h-9 items-center rounded-md px-4 text-[13px] font-medium text-white transition-colors"
          style={{ backgroundColor: 'var(--accent)' }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--accent-hover)')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'var(--accent)')}
        >
          Complete Profile
        </Link>
        <button
          onClick={onDismiss}
          className="grid h-9 w-9 place-items-center rounded-md text-mut transition-colors hv hover:text-soft"
          aria-label="Dismiss"
          title="Remind me later"
        >
          <X size={15} />
        </button>
      </div>
    </div>
  )
}


export default function Logo({ size = 30, inverse = false, onDark = false, withTagline = false }) {
  const light = inverse || onDark
  const tile = withTagline ? Math.round(size * 1.25) : size

  return (
    <div className="flex select-none items-center gap-2.5">
      <span
        className="tile-grad grid shrink-0 place-items-center rounded-xl"
        style={{ width: tile, height: tile }}
      >
        <svg width={tile * 0.6} height={tile * 0.6} viewBox="0 0 24 24" fill="none">
          <path
            d="M12 21s7-5.4 7-11a7 7 0 1 0-14 0c0 5.6 7 11 7 11Z"
            stroke="#fff"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="10" r="2.4" fill="#fff" />
        </svg>
      </span>

      <span className="leading-none">
        <span
          className={`block text-[15px] font-bold tracking-tight ${
            light ? 'text-white' : 'text-main'
          }`}
        >
          Trip Optimizer
        </span>
        {withTagline && (
          <span
            className="mt-1 block text-[10px] font-semibold uppercase tracking-[0.18em]"
            style={{ color: 'var(--accent-text)' }}
          >
            Travel planning
          </span>
        )}
      </span>
    </div>
  )
}

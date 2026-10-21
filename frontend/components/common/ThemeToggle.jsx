import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme.js'

/**
 * Icon button — used in headers / sidebars.
 * `onDark` styles it for sitting on top of a photograph, where the themed
 * panel/border tokens would disappear against the image.
 */
export default function ThemeToggle({ className = '', onDark = false }) {
  const { theme, toggle } = useTheme()
  const base = 'grid h-11 w-11 place-items-center rounded-full border transition-colors'
  const skin = onDark
    ? 'border-white/25 text-white hover:bg-white/10'
    : 'border-subtle bg-panel text-mut hv hover:text-soft'
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className={`${base} ${skin} ${className}`}
      style={onDark ? { backgroundColor: 'rgba(10,10,12,0.45)', backdropFilter: 'blur(8px)' } : undefined}
    >
      {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
    </button>
  )
}

/** Segmented Dark / Light control — used inside Settings. */
export function ThemeSegment({ className = '' }) {
  const { theme, setTheme } = useTheme()
  return (
    <div
      className={`flex rounded-md border border-subtle p-0.5 ${className}`}
      style={{ backgroundColor: 'var(--fill)' }}
    >
      {['dark', 'light'].map((t) => (
        <button
          key={t}
          type="button"
          onClick={() => setTheme(t)}
          className={`flex flex-1 items-center justify-center gap-1.5 rounded-[4px] px-3 py-1.5 text-[13px] font-medium transition-colors ${
            theme === t ? 'text-main' : 'text-mut hover:text-soft'
          }`}
          style={theme === t ? { backgroundColor: 'var(--panel)' } : undefined}
        >
          {t === 'dark' ? <Moon size={14} /> : <Sun size={14} />}
          {t === 'dark' ? 'Dark' : 'Light'}
        </button>
      ))}
    </div>
  )
}

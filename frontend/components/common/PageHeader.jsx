import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import Logo from './Logo.jsx'
import ThemeToggle from './ThemeToggle.jsx'

export default function PageHeader({ back = '/dashboard', backLabel = 'Back', children }) {
  return (
    <header className="border-b" style={{ backgroundColor: 'var(--panel)', borderColor: 'var(--border)' }}>
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3.5">
        <div className="flex items-center gap-4">
          <Logo size={26} />
          {back && (
            <Link
              to={back}
              className="inline-flex items-center gap-1.5 text-[13px] text-mut transition-colors hover:text-soft"
            >
              <ArrowLeft size={14} /> {backLabel}
            </Link>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {children}
        </div>
      </div>
    </header>
  )
}

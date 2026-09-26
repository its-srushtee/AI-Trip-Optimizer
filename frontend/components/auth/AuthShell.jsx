import { Compass, CalendarDays, Wallet } from 'lucide-react'
import Logo from '../common/Logo.jsx'
import ThemeToggle from '../common/ThemeToggle.jsx'
import { resolveImageUrl } from '../../services/api.js'

const benefits = [
  {
    icon: Compass,
    title: 'Made for your style',
    text: 'Every plan matches your travel style, pace and preferences',
  },
  {
    icon: CalendarDays,
    title: 'Built around your dates',
    text: 'Day-by-day timing so you never waste a moment',
  },
  {
    icon: Wallet,
    title: 'Fits your budget',
    text: 'See exactly what your trip costs before you book',
  },
]

function BenefitList({ onDark = false, compact = false }) {
  return (
    <ul className={compact ? 'space-y-3' : 'mt-6 space-y-4 lg:mt-9 lg:space-y-5'}>
      {benefits.map((b) => {
        const Icon = b.icon
        return (
          <li key={b.title} className="flex gap-3.5">
            <span
              className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl"
              style={
                onDark
                  ? {
                      background: 'rgba(255,255,255,0.08)',
                      border: '1px solid rgba(255,255,255,0.14)',
                      color: 'var(--accent-text)',
                    }
                  : {
                      background: 'var(--fill)',
                      border: '1px solid var(--border)',
                      color: 'var(--accent-text)',
                    }
              }
            >
              <Icon size={17} />
            </span>
            <span>
              <span
                className={`block text-[14px] font-semibold ${onDark ? 'text-white' : 'text-main'}`}
              >
                {b.title}
              </span>
              <span
                className={`mt-0.5 block text-[12.5px] leading-snug ${
                  onDark ? 'hidden text-white/60 lg:block' : 'text-mut'
                }`}
              >
                {b.text}
              </span>
            </span>
          </li>
        )
      })}
    </ul>
  )
}

export default function AuthShell({ children, title, subtitle, footer }) {
  return (
    <div className="min-h-screen w-full md:flex">
      
      <div className="relative hidden overflow-hidden md:block md:w-[54%] xl:w-[62.6%]">
        <img
          src={resolveImageUrl('/images/hero.jpg')}
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              'linear-gradient(to top, rgba(6,8,12,0.94) 0%, rgba(6,8,12,0.7) 44%, rgba(6,8,12,0.3) 74%, rgba(6,8,12,0.18) 100%)',
          }}
        />

        <div className="relative flex h-full flex-col p-7 lg:p-10 xl:p-12">
          <Logo onDark withTagline />

          <div className="mt-auto max-w-xl">
            <span
              className="inline-flex items-center rounded-full px-3.5 py-1.5 text-[11px] font-semibold uppercase tracking-[0.15em]"
              style={{
                color: 'var(--accent-text)',
                background: 'rgba(34,211,238,0.10)',
                border: '1px solid rgba(34,211,238,0.34)',
              }}
            >
              Personalized travel planning
            </span>

            <h1 className="display mt-4 text-[1.875rem] leading-[1.08] text-white lg:mt-5 lg:text-[2.5rem] xl:text-[3rem]">
              Your next trip,
              <br />
              <span className="text-grad">planned around you.</span>
            </h1>

            <p className="mt-4 hidden max-w-lg text-[15px] leading-relaxed text-white/70 lg:mt-5 lg:block">
              Tell us where you want to go, your dates and your budget — you&apos;ll get a
              day-by-day itinerary with the places, stays and costs laid out.
            </p>

            <BenefitList onDark />
          </div>
        </div>
      </div>

      <div
        className="relative flex w-full flex-col md:w-[46%] xl:w-[37.4%]"
        style={{ backgroundColor: 'var(--bg)' }}
      >

        <div className="relative h-32 overflow-hidden sm:h-40 md:hidden">
          <img
            src={resolveImageUrl('/images/hero.jpg')}
            alt=""
            className="absolute inset-0 h-full w-full object-cover"
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                'linear-gradient(to top, rgba(6,8,12,0.92) 0%, rgba(6,8,12,0.45) 60%, rgba(6,8,12,0.3) 100%)',
            }}
          />
          <div className="relative flex h-full items-start justify-between p-5">
            <Logo onDark withTagline />
            <ThemeToggle onDark />
          </div>
        </div>

        <div className="relative hidden justify-end px-6 py-6 md:flex lg:px-8">
          <ThemeToggle />
        </div>

        <div className="relative flex flex-1 items-center justify-center px-5 pb-10 pt-8 sm:px-8 md:px-6 md:pt-0 lg:px-8">
          <div className="w-full max-w-[29.5rem]">
            <div className="mb-8 hidden md:block">
              <Logo withTagline />
            </div>

            <h2 className="display-sm text-[1.875rem] text-main">{title}</h2>
            {subtitle && <p className="mt-2 text-[15px] text-mut">{subtitle}</p>}
            <div className="mt-7">{children}</div>
            {footer && <div className="mt-6">{footer}</div>}

            <div className="mt-9 border-t border-subtle pt-7 md:hidden">
              <BenefitList compact />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

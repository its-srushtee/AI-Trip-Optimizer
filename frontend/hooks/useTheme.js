import { useEffect, useState } from 'react'

export function readTheme() {
  if (typeof window === 'undefined') return 'light'
  try {
    const saved = localStorage.getItem('tripopt_theme')
    if (saved === 'dark' || saved === 'light') return saved
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
  } catch {
    /* ignore */
  }
  return 'light'
}

/** Theme state shared by the sidebar toggle, header, and settings */
export function useTheme() {
  const [theme, setTheme] = useState(readTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    try {
      localStorage.setItem('tripopt_theme', theme)
    } catch {
      /* ignore */
    }

    const handleStorage = (e) => {
      if (e.key === 'tripopt_theme' && (e.newValue === 'light' || e.newValue === 'dark')) {
        setTheme(e.newValue)
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [theme])

  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  return { theme, setTheme, toggle }
}


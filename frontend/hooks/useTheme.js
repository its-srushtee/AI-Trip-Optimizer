import { useEffect, useState } from 'react'

export function readTheme() {
  return document.documentElement.getAttribute('data-theme') || 'dark'
}

/** Theme state shared by the header toggle and the Settings segmented control. */
export function useTheme() {
  const [theme, setTheme] = useState(readTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem('tripopt_theme', theme)
    } catch {
      /* ignore */
    }
  }, [theme])

  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  return { theme, setTheme, toggle }
}

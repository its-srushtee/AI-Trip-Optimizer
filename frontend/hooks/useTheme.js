import { useEffect, useState } from 'react'

export function readTheme() {
  return document.documentElement.getAttribute('data-theme') || 'dark'
}

export function useTheme() {
  const [theme, setTheme] = useState(readTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem('tripopt_theme', theme)
    } catch {
      
    }
  }, [theme])

  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  return { theme, setTheme, toggle }
}

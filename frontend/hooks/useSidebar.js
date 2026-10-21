import { useState, useEffect } from 'react'

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('sidebar_collapsed') === 'true'
    } catch {
      return false
    }
  })

  useEffect(() => {
    const handler = () => {
      try {
        setCollapsed(localStorage.getItem('sidebar_collapsed') === 'true')
      } catch {}
    }
    window.addEventListener('sidebar_toggle', handler)
    window.addEventListener('storage', handler)
    return () => {
      window.removeEventListener('sidebar_toggle', handler)
      window.removeEventListener('storage', handler)
    }
  }, [])

  return collapsed
}

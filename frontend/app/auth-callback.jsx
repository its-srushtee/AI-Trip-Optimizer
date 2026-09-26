import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase.js'
import { api, setToken } from '../services/api.js'
import { saveUser } from '../lib/userStore.js'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    const handleCallback = async () => {
      try {
        const { data, error: sessionError } =
          await supabase.auth.getSession()

        if (sessionError) throw sessionError

        const session = data.session

        if (!session?.access_token) {
          throw new Error('Google authentication session was not found.')
        }

        const result = await api.googleAuth(session.access_token)

        if (cancelled) return

        setToken(result.access_token)
        saveUser(result.user)

        await supabase.auth.signOut()

        navigate('/dashboard', { replace: true })
      } catch (err) {
        if (cancelled) return
        console.error('Google callback error:', err)
        setError(err.message || 'Google sign-in failed.')
      }
    }

    handleCallback()

    return () => {
      cancelled = true
    }
  }, [navigate])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-md text-center">
          <h1 className="text-lg font-semibold text-main">
            Google sign-in failed
          </h1>
          <p className="mt-2 text-sm text-mut">{error}</p>
          <button
            type="button"
            onClick={() => navigate('/login', { replace: true })}
            className="mt-5 rounded-xl px-4 py-2.5 text-sm font-medium text-white"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            Back to Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-sm text-mut">Signing you in with Google…</p>
    </div>
  )
}
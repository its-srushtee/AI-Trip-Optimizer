import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import Logo from '../components/common/Logo.jsx'
import Button from '../components/common/Button.jsx'
import ThemeToggle from '../components/common/ThemeToggle.jsx'
import PreferencesEditor, { defaultPreferences } from '../components/auth/PreferencesEditor.jsx'
import { api, getToken, clearToken } from '../services/api.js'
import { getUser, saveUser, clearUser } from '../lib/userStore.js'
import { isProfileComplete, dismissPrompt, clearDismissed } from '../lib/profile.js'

export default function CompleteProfile() {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => getUser())
  const [prefs, setPrefs] = useState(() => ({
    ...defaultPreferences,
    ...(getUser()?.preferences || {}),
  }))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = getToken()
    if (!token) {
      navigate('/login')
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const me = await api.me(token)
        if (cancelled) return
        saveUser(me)
        setUser(me)
        setPrefs({ ...defaultPreferences, ...(me.preferences || {}) })
      } catch (err) {
        if (cancelled) return
        if (err.status === 401) {
          clearUser()
          clearToken()
          navigate('/login')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [navigate])

  const complete = isProfileComplete(prefs)
  const existing = user?.preferences && Object.keys(user.preferences).length > 0

  const handleSave = async (e) => {
    e.preventDefault()
    if (!complete) {
      setError('Select at least one interest before saving.')
      return
    }
    setError('')
    setSaving(true)
    try {
      const updated = await api.updateMe({ preferences: prefs }, getToken())
      saveUser(updated)
      clearDismissed(updated.id)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleSkip = () => {
    if (user?.id) dismissPrompt(user.id)
    navigate('/dashboard')
  }

  return (
    <div className="min-h-screen w-full">
      <header
        className="border-b border-subtle"
        style={{ backgroundColor: 'var(--panel)' }}
      >
        <div className="mx-auto flex max-w-2xl items-center justify-between px-5 py-3">
          <Logo size={26} />
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button variant="secondary" onClick={() => navigate('/dashboard')}>
              <ArrowLeft size={14} /> Back
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-5 py-8">
        <h1 className="text-xl font-semibold tracking-tight text-main">
          {existing ? 'Edit your travel preferences' : 'Set your travel preferences'}
        </h1>
        <p className="mt-1.5 max-w-lg text-[13px] leading-relaxed text-mut">
          These are used to rank destination recommendations and to pre-fill new trips.
          You can change them later in Settings.
        </p>

        <form onSubmit={handleSave} className="card mt-6 p-5">
          <PreferencesEditor value={prefs} onChange={setPrefs} />

          {error && <p className="alert alert-error mt-5">{error}</p>}

          <div className="mt-6 flex items-center justify-between gap-3 border-t border-subtle pt-4">
            <button
              type="button"
              onClick={handleSkip}
              className="text-[13px] text-mut transition-colors hover:text-soft"
            >
              Skip for now
            </button>
            <Button type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save Preferences'}
            </Button>
          </div>
        </form>
      </main>
    </div>
  )
}

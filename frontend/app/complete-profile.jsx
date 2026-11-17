import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Check,
  User,
  Mail,
  Lock,
  Compass,
  Settings,
  Shield,
  LogOut,
  Sparkles,
  AlertCircle,
  Heart,
  Sliders,
  DollarSign,
  Coffee,
  Bed,
  Sun,
  Moon,
} from 'lucide-react'
import Sidebar from '../components/common/Sidebar.jsx'
import { useSidebar } from '../hooks/useSidebar.js'
import { useTheme } from '../hooks/useTheme.js'
import PreferencesEditor, { defaultPreferences } from '../components/auth/PreferencesEditor.jsx'
import { api, getToken, clearToken } from '../services/api.js'
import { getUser, saveUser, clearUser } from '../lib/userStore.js'
import { clearDismissed } from '../lib/profile.js'
import { INTERESTS } from '../lib/constants.js'

const TABS = [
  { id: 'info', label: 'Personal Information', icon: User },
  { id: 'preferences', label: 'Travel Preferences', icon: Compass },
  { id: 'settings', label: 'Account Settings', icon: Settings },
]

export default function CompleteProfile() {
  const navigate = useNavigate()
  const sidebarCollapsed = useSidebar()
  const { theme, setTheme } = useTheme()

  const [user, setUser] = useState(() => getUser())
  const [activeTab, setActiveTab] = useState('info')

  // Form states
  const [name, setName] = useState(() => getUser()?.name || '')
  const [email, setEmail] = useState(() => getUser()?.email || '')
  const [prefs, setPrefs] = useState(() => ({
    ...defaultPreferences,
    ...(getUser()?.preferences || {}),
  }))

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [savedSuccess, setSavedSuccess] = useState('')

  const firstName = (name || user?.name || 'Traveler').trim().split(/\s+/)[0]
  const initials = (name || user?.name || 'TR')
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  // Fetch current user details
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
        setName(me.name || '')
        setEmail(me.email || '')
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

  const signOut = () => {
    clearUser()
    clearToken()
    navigate('/login')
  }

  // Save personal info
  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSavedSuccess('')
    try {
      const updated = await api.updateMe({ name, email }, getToken())
      saveUser(updated)
      setUser(updated)
      setSavedSuccess('Personal details updated successfully.')
      setTimeout(() => setSavedSuccess(''), 3000)
    } catch (err) {
      setError(err.message || 'Failed to update personal information.')
    } finally {
      setSaving(false)
    }
  }

  // Save preferences
  const handleSavePreferences = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSavedSuccess('')
    try {
      const updated = await api.updateMe({ preferences: prefs }, getToken())
      saveUser(updated)
      setUser(updated)
      clearDismissed(updated.id)
      setSavedSuccess('Travel preferences saved. Recommendations updated.')
      setTimeout(() => setSavedSuccess(''), 3000)
    } catch (err) {
      setError(err.message || 'Failed to save travel preferences.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex bg-slate-50 dark:bg-[#0d0f14] text-slate-900 dark:text-slate-100 transition-colors duration-150">
      {/* Unified Collapsible Sidebar */}
      <Sidebar activeNav="Profile" />

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-14 lg:pt-0 ${
          sidebarCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[230px]'
        }`}
      >
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-6 mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
                My Profile & Preferences
              </h1>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
                Manage your personal information, travel style, and account security.
              </p>
            </div>

            {/* Quick User Banner Badge */}
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-2.5 shadow-xs">
              <div className="relative h-11 w-11 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-xs select-none">
                <span>{initials}</span>
                <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 ring-2 ring-white" />
              </div>
              <div className="min-w-0 pr-2">
                <p className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">{name || 'Traveler'}</p>
                <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate">{email || 'member@tripplanner'}</p>
              </div>
            </div>
          </div>

          {/* Navigation Tabs Bar */}
          <div className="flex space-x-1 sm:space-x-2 border-b border-slate-200/80 dark:border-slate-800 pb-3 mb-6 overflow-x-auto scrollbar-none">
            {TABS.map((tab) => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold whitespace-nowrap transition-all duration-150 ${
                    active
                      ? 'bg-violet-600 text-white shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Icon size={15} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>

          {/* Feedback messages */}
          {error && (
            <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-700 flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {savedSuccess && (
            <div className="mb-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-medium text-emerald-700 flex items-center gap-2">
              <Check size={16} className="shrink-0" />
              <span>{savedSuccess}</span>
            </div>
          )}

          {activeTab === 'info' && (
            <form onSubmit={handleSaveProfile} className="space-y-6 animate-fade-in">
              <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs space-y-6">
                <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">Personal Details</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Your name and email address associated with your travel account.
                  </p>
                </div>

                {/* Profile Photo Section */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                    Profile Photo
                  </label>
                  <div className="flex items-center gap-4">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 text-white font-extrabold text-xl flex items-center justify-center shadow-md">
                      {initials}
                    </div>
                  </div>
                </div>

                {/* Name Input */}
                <div>
                  <label htmlFor="user-name" className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Full Name
                  </label>
                  <div className="relative">
                    <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      id="user-name"
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white pl-10 pr-4 py-2.5 text-sm text-slate-800 outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                    />
                  </div>
                </div>

                {/* Email Input */}
                <div>
                  <label htmlFor="user-email" className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      id="user-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="jane@example.com"
                      className="w-full rounded-xl border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white pl-10 pr-4 py-2.5 text-sm text-slate-800 outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                    />
                  </div>
                </div>

                {/* Save Changes Button */}
                <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800">
                  <button
                    type="submit"
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-violet-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? 'Saving…' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {activeTab === 'preferences' && (
            <form onSubmit={handleSavePreferences} className="space-y-6 animate-fade-in">
              <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
                <div className="border-b border-slate-100 pb-4 mb-6">
                  <h2 className="text-base font-bold text-slate-900">
                    Travel Styles & Interests
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Customize your preferred travel pace, budget level, accommodation, and interests.
                  </p>
                </div>

                {/* Preferences Editor Component */}
                <PreferencesEditor value={prefs} onChange={setPrefs} />

                {/* Save Preferences Button */}
                <div className="mt-8 flex justify-end pt-4 border-t border-slate-100">
                  <button
                    type="submit"
                    disabled={saving}
                    className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-violet-700 transition-colors disabled:opacity-50"
                  >
                    {saving ? 'Saving Preferences…' : 'Save Preferences'}
                  </button>
                </div>
              </div>
            </form>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6 animate-fade-in">
              {/* Appearance & Theme */}
              <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-4">
                <div className="border-b border-slate-100 pb-4">
                  <h2 className="text-base font-bold text-slate-900">Appearance & Theme</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Choose how TripPlanner looks for your session.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => setTheme('light')}
                    className={`flex items-center gap-3 rounded-xl border p-3.5 text-left transition-all ${
                      theme === 'light'
                        ? 'border-violet-600 bg-violet-50/80 text-violet-900 ring-2 ring-violet-500/20'
                        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-amber-100 text-amber-600">
                      <Sun size={18} />
                    </div>
                    <div>
                      <p className="text-xs font-bold leading-tight">Light Mode</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">Crisp, clean & bright</p>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTheme('dark')}
                    className={`flex items-center gap-3 rounded-xl border p-3.5 text-left transition-all ${
                      theme === 'dark'
                        ? 'border-violet-600 bg-violet-50/80 text-violet-900 ring-2 ring-violet-500/20'
                        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-indigo-100 text-indigo-600">
                      <Moon size={18} />
                    </div>
                    <div>
                      <p className="text-xs font-bold leading-tight">Dark Mode</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">Sleek midnight palette</p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Security & Authentication */}
              <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs space-y-4">
                <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">Security & Sign In</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Your password and login authentication details.
                  </p>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200">Password</h3>
                    <p className="text-[11px] text-slate-400 dark:text-slate-400">
                      Encrypted and secured via bcrypt hashing.
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs text-slate-600 dark:text-slate-300 font-mono tracking-widest">
                    ••••••••••••
                  </span>
                </div>

                <div className="flex items-center justify-between py-2 border-t border-slate-100 dark:border-slate-800">
                  <div>
                    <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200">Profile Status</h3>
                    <p className="text-[11px] text-slate-400 dark:text-slate-400">
                      {user?.profile_complete ? 'Complete profile' : 'Incomplete profile'}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                      user?.profile_complete
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-700/60'
                        : 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-700/60'
                    }`}
                  >
                    {user?.profile_complete ? 'Verified' : 'Pending Preferences'}
                  </span>
                </div>
              </div>

              {/* Session / Danger Zone */}
              <div className="rounded-2xl border border-rose-200/80 dark:border-rose-900/40 bg-white dark:bg-slate-900 p-6 shadow-xs space-y-4">
                <div className="border-b border-rose-100 dark:border-rose-900/30 pb-4">
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">Account Session</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Sign out of this browser or device.
                  </p>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">Sign Out</p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      Clears local authentication token and cached session.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={signOut}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700 hover:bg-rose-100 dark:border-rose-800/60 dark:bg-rose-950/40 dark:text-rose-300 dark:hover:bg-rose-900/50 transition-colors"
                  >
                    <LogOut size={13} />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

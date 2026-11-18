import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../components/auth/AuthShell.jsx'
import GoogleButton from '../components/auth/GoogleButton.jsx'
import Button from '../components/common/Button.jsx'
import Field, { PasswordInput } from '../components/auth/Field.jsx'
import { User, Mail, Lock, Sparkles, ArrowRight, ArrowLeft, Check, Compass } from 'lucide-react'
import { api, setToken } from '../services/api.js'
import { saveUser } from '../lib/userStore.js'
import { interests, travelStyles, tripPaces, foodOptions } from '../lib/constants.js'

export default function Signup() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1) // 1 = Account Info, 2 = Travel Preferences
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')

  // Step 2: Travel Preferences state
  const [preferences, setPreferences] = useState({
    style: 'Comfort',
    pace: 'Balanced',
    interests: ['beaches', 'culture', 'food'],
    food: 'No preference',
    accommodation: 'Hotel',
  })

  const setFormField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }))
    if (errors[key]) setErrors((e) => ({ ...e, [key]: '' }))
  }

  const toggleInterest = (id) => {
    setPreferences((prev) => {
      const exists = prev.interests.includes(id)
      const next = exists
        ? prev.interests.filter((x) => x !== id)
        : [...prev.interests, id]
      return { ...prev, interests: next }
    })
  }

  const validateStep1 = () => {
    const e = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email'
    if (!form.password) e.password = 'Password is required'
    else if (form.password.length < 6) e.password = 'Password should be at least 6 characters.'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleNextStep = (e) => {
    e.preventDefault()
    if (!validateStep1()) return
    setFormError('')
    setStep(2)
  }

  const handleSubmit = async (e, skipPreferences = false) => {
    if (e) e.preventDefault()
    if (!validateStep1()) {
      setStep(1)
      return
    }
    setLoading(true)
    setFormError('')

    const userPrefs = skipPreferences
      ? { style: 'Comfort', pace: 'Balanced', interests: ['beaches', 'nature'], food: 'No preference', accommodation: 'Hotel' }
      : preferences

    try {
      const data = await api.signup({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        preferences: userPrefs,
      })
      setToken(data.access_token)
      saveUser(data.user)
      navigate('/dashboard')
    } catch (err) {
      setFormError(err.message)
      window.scrollTo(0, 0)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title={step === 1 ? 'Create your account' : 'Your Travel Preferences'}
      subtitle={
        step === 1
          ? 'Step 1 of 2: Create your profile to unlock smart itineraries'
          : 'Step 2 of 2: Pick your travel vibe for personalized destination recommendations'
      }
      footer={
        <p className="text-center text-[13px] text-mut">
          Already have an account?{' '}
          <Link
            to="/login"
            className="inline-flex min-h-[44px] items-center font-medium text-brand hover:underline lg:min-h-0"
          >
            Sign in
          </Link>
        </p>
      }
    >
      {/* Step Progress Pill */}
      <div className="mb-5 flex items-center justify-between rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 px-3.5 py-2">
        <div className="flex items-center gap-2">
          <span
            className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold transition-colors ${
              step === 1
                ? 'bg-violet-600 text-white'
                : 'bg-emerald-500 text-white'
            }`}
          >
            {step === 1 ? '1' : <Check size={12} strokeWidth={3} />}
          </span>
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Account Details
          </span>
        </div>
        <div className="h-0.5 w-8 bg-slate-200 dark:bg-slate-700" />
        <div className="flex items-center gap-2">
          <span
            className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold transition-colors ${
              step === 2
                ? 'bg-violet-600 text-white shadow-xs'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
            }`}
          >
            2
          </span>
          <span className={`text-xs font-semibold ${step === 2 ? 'text-violet-600 dark:text-violet-400' : 'text-slate-400'}`}>
            Travel Preferences
          </span>
        </div>
      </div>

      {formError && <p className="alert alert-error mb-4">{formError}</p>}

      {step === 1 ? (
        <>
          <form onSubmit={handleNextStep} className="space-y-4">
            <Field
              id="name"
              label="Full name"
              placeholder="Your Name"
              icon={<User size={17} />}
              value={form.name}
              error={errors.name}
              onChange={(e) => setFormField('name', e.target.value)}
              autoComplete="name"
            />

            <Field
              id="email"
              type="email"
              label="Email address"
              placeholder="you@example.com"
              icon={<Mail size={17} />}
              value={form.email}
              error={errors.email}
              onChange={(e) => setFormField('email', e.target.value)}
              autoComplete="email"
            />

            <PasswordInput
              id="password"
              label="Password"
              placeholder="At least 6 characters"
              icon={<Lock size={17} />}
              value={form.password}
              error={errors.password}
              minLength={6}
              autoComplete="new-password"
              onChange={(e) => setFormField('password', e.target.value)}
            />

            <label className="flex cursor-pointer items-start gap-2.5 text-[13px] leading-snug text-mut">
              <input
                type="checkbox"
                required
                className="mt-0.5 h-3.5 w-3.5 shrink-0 rounded-sm border-subtle"
              />
              <span>
                I agree to the <span className="text-soft">Terms of Service</span> and{' '}
                <span className="text-soft">Privacy Policy</span>.
              </span>
            </label>

            <Button type="submit" className="w-full flex items-center justify-center gap-2">
              <span>Continue to Travel Preferences</span>
              <ArrowRight size={16} />
            </Button>
          </form>

          <GoogleButton label="Sign up with Google" />
        </>
      ) : (
        <form onSubmit={(e) => handleSubmit(e, false)} className="space-y-5 animate-in fade-in duration-200">
          {/* Travel Style */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
              Travel Style
            </label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {travelStyles.map((s) => {
                const active = preferences.style === s
                return (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setPreferences((p) => ({ ...p, style: s }))}
                    className={`rounded-xl border px-3 py-2 text-xs font-semibold transition-all ${
                      active
                        ? 'border-violet-600 bg-violet-50 text-violet-700 dark:border-violet-500 dark:bg-violet-950/40 dark:text-violet-300 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-slate-300'
                    }`}
                  >
                    {s}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Trip Pace */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
              Trip Pace
            </label>
            <div className="grid grid-cols-3 gap-2">
              {['Relaxed', 'Balanced', 'Fast-paced'].map((p) => {
                const active = preferences.pace === p
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPreferences((prev) => ({ ...prev, pace: p }))}
                    className={`rounded-xl border px-3 py-2 text-xs font-semibold transition-all ${
                      active
                        ? 'border-violet-600 bg-violet-50 text-violet-700 dark:border-violet-500 dark:bg-violet-950/40 dark:text-violet-300 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-slate-300'
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Interests Chips */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                What interests you most?
              </label>
              <span className="text-[11px] font-medium text-violet-600 dark:text-violet-400">
                {preferences.interests.length} selected
              </span>
            </div>
            <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto pr-1">
              {interests.map((i) => {
                const selected = preferences.interests.includes(i.id)
                return (
                  <button
                    key={i.id}
                    type="button"
                    onClick={() => toggleInterest(i.id)}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all ${
                      selected
                        ? 'border-violet-600 bg-violet-600 text-white shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/80'
                    }`}
                  >
                    <span>{i.emoji}</span>
                    <span>{i.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Food Preference */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
              Food Preference
            </label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {foodOptions.map((f) => {
                const active = preferences.food === f
                return (
                  <button
                    key={f}
                    type="button"
                    onClick={() => setPreferences((p) => ({ ...p, food: f }))}
                    className={`rounded-xl border px-3 py-2 text-xs font-semibold transition-all ${
                      active
                        ? 'border-violet-600 bg-violet-50 text-violet-700 dark:border-violet-500 dark:bg-violet-950/40 dark:text-violet-300 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-slate-300'
                    }`}
                  >
                    {f}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 space-y-2.5">
            <Button
              type="submit"
              className="w-full flex items-center justify-center gap-2 shadow-sm"
              disabled={loading}
            >
              <Sparkles size={16} />
              <span>{loading ? 'Creating account…' : 'Complete Signup & Discover Trips'}</span>
            </Button>

            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
              >
                <ArrowLeft size={13} />
                <span>Back to account details</span>
              </button>

              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                className="text-xs font-medium text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                disabled={loading}
              >
                Skip for now
              </button>
            </div>
          </div>
        </form>
      )}
    </AuthShell>
  )
}

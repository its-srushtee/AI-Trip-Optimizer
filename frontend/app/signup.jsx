import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../components/auth/AuthShell.jsx'
import GoogleButton from '../components/auth/GoogleButton.jsx'
import Button from '../components/common/Button.jsx'
import Field, { PasswordInput } from '../components/auth/Field.jsx'
import { User, Mail, Lock } from 'lucide-react'
import { api, setToken } from '../services/api.js'
import { saveUser } from '../lib/userStore.js'

export default function Signup() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')

  const setFormField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }))
    if (errors[key]) setErrors((e) => ({ ...e, [key]: '' }))
  }

  const validate = () => {
    const e = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.email.trim()) e.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email'
    if (!form.password) e.password = 'Password is required'
    else if (form.password.length < 6) e.password = 'Password should be at least 6 characters.'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setFormError('')
    try {
      const data = await api.signup({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
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
      title="Create your account"
      subtitle="You can add your travel preferences after signing in."
      footer={
        <p className="text-center text-[13px] text-mut">
          Already have an account?{' '}
          <Link to="/login" className="inline-flex min-h-[44px] items-center font-medium text-brand hover:underline lg:min-h-0">
            Sign in
          </Link>
        </p>
      }
    >
      {formError && (
        <p className="alert alert-error mb-4">{formError}</p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
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

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Creating account…' : 'Create Account'}
        </Button>
      </form>

      <GoogleButton label="Sign up with Google" />
    </AuthShell>
  )
}

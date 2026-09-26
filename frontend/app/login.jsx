import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../components/auth/AuthShell.jsx'
import GoogleButton from '../components/auth/GoogleButton.jsx'
import Button from '../components/common/Button.jsx'
import Field, { PasswordInput } from '../components/auth/Field.jsx'
import { Mail, Lock } from 'lucide-react'
import { api, setToken } from '../services/api.js'
import { saveUser } from '../lib/userStore.js'

export default function Login() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [pwError, setPwError] = useState('')
  const [formError, setFormError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!password) {
      setPwError('Password is required')
      return
    }
    if (password.length < 6) {
      setPwError('Password should be at least 6 characters.')
      return
    }
    setPwError('')
    setFormError('')
    setLoading(true)
    try {
      const data = await api.login({ email, password })
      setToken(data.access_token)
      saveUser(data.user)
      navigate('/dashboard')
    } catch (err) {
      setFormError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your trips and itineraries."
      footer={
        <p className="text-center text-[13px] text-mut">
          Don&apos;t have an account?{' '}
          <Link to="/signup" className="inline-flex min-h-[44px] items-center font-medium text-brand hover:underline lg:min-h-0">
            Create one
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field
          id="email"
          type="email"
          label="Email address"
          placeholder="you@example.com"
          icon={<Mail size={17} />}
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <PasswordInput
          id="password"
          label="Password"
          placeholder="••••••••"
          icon={<Lock size={17} />}
          value={password}
          error={pwError}
          onChange={(e) => {
            setPassword(e.target.value)
            if (pwError) setPwError('')
          }}
        />

        <div className="flex items-center justify-between text-[13px]">
          <label className="flex min-h-[44px] cursor-pointer items-center gap-2.5 py-2 text-mut lg:min-h-0 lg:py-0">
            <input
              type="checkbox"
              className="h-[18px] w-[18px] shrink-0 rounded-sm border-subtle lg:h-3.5 lg:w-3.5"
            />
            Remember me
          </label>
          <button
            type="button"
            className="inline-flex min-h-[44px] items-center py-2 text-mut transition-colors hover:text-soft lg:min-h-0 lg:py-0"
          >
            Forgot password?
          </button>
        </div>

        {formError && <p className="alert alert-error">{formError}</p>}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign In'}
        </Button>
      </form>

      <GoogleButton label="Continue with Google" />

    </AuthShell>
  )
}

import { useEffect, useState } from 'react'
import { api } from './api'
import { APP_NAME, TAGLINE } from './brand'
import GoogleButton from './GoogleButton'
import PasswordInput from './PasswordInput'
import Sparkle from './Sparkle'

const GOOGLE_ERRORS: Record<string, string> = {
  google: 'Google sign-in did not complete. Please try again.',
  google_unverified: 'Your Google email address is not verified.',
  google_off: 'Google sign-in is not switched on yet. Please use email for now.',
}

export default function Auth({ onSignedIn }: { onSignedIn: () => void }) {
  const [mode, setMode] = useState<'in' | 'up'>('in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(() => GOOGLE_ERRORS[new URLSearchParams(location.search).get('auth_error') ?? ''] ?? '')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (location.search) history.replaceState(null, '', location.pathname)
  }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (mode === 'up' && password !== confirm) return // the inline hint under the field already says why
    setBusy(true)
    setError('')
    try {
      if (mode === 'in') await api.login(email, password)
      else await api.signup(email, password)
      onSignedIn()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page auth">
      <header className="hero">
        <Sparkle className="hero-mark" />
        <h1>{APP_NAME}</h1>
        <p className="tagline">{TAGLINE}</p>
      </header>
      <form className="glass auth-card" onSubmit={submit}>
        <h2>{mode === 'in' ? 'Sign in' : 'Create your account'}</h2>
        <GoogleButton label={mode === 'in' ? 'Sign in with Google' : 'Sign up with Google'} />
        <div className="or"><span>or with email</span></div>
        <label>
          Email
          <input className="field" type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" />
        </label>
        <label>
          Password
          <PasswordInput
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={mode === 'up' ? 8 : undefined}
            autoComplete={mode === 'in' ? 'current-password' : 'new-password'}
          />
          {mode === 'up' && <span className="field-hint muted">At least 8 characters.</span>}
        </label>
        {mode === 'up' && (
          <label>
            Confirm password
            <PasswordInput
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              required
              autoComplete="new-password"
              aria-invalid={confirm.length > 0 && confirm !== password}
            />
            {confirm.length > 0 && confirm !== password && <span className="field-hint">Passwords do not match yet.</span>}
          </label>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={busy}>{busy ? 'Please wait…' : mode === 'in' ? 'Sign in' : 'Create account'}</button>
        <button type="button" className="link" onClick={() => { setMode(mode === 'in' ? 'up' : 'in'); setError(''); setConfirm('') }}>
          {mode === 'in' ? 'New here? Create an account' : 'Already have an account? Sign in'}
        </button>
      </form>
      <a className="powered" href="https://dagbooks.org/" target="_blank" rel="noopener noreferrer">
        <span>Powered by</span>
        <img src="/dagbooks.png" alt="Dag Books" width="120" height="40" />
      </a>
    </div>
  )
}

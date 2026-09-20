import { useEffect, useRef, useState } from 'react'
import { api, type User } from './api'
import Sparkle from './Sparkle'

const COOLDOWN = 60 // seconds; matches the server's resend limit

export default function Verify({ user, onDone, onSignOut }: { user: User; onDone: () => void; onSignOut: () => void }) {
  const [digits, setDigits] = useState<string[]>(Array(6).fill(''))
  const boxes = useRef<(HTMLInputElement | null)[]>([])
  const code = digits.join('')
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [wait, setWait] = useState(COOLDOWN) // a code was just sent at sign-up

  useEffect(() => {
    if (wait <= 0) return
    const t = setTimeout(() => setWait(w => w - 1), 1000)
    return () => clearTimeout(t)
  }, [wait])

  async function submit(value = code) {
    if (value.length !== 6 || busy) return
    setBusy(true)
    setError('')
    try {
      await api.verifyEmail(value)
      onDone()
    } catch (err) {
      setError((err as Error).message)
      setDigits(Array(6).fill(''))
      boxes.current[0]?.focus()
    } finally {
      setBusy(false)
    }
  }

  // Typing, paste and phone autofill all land here; several digits spill into the following boxes.
  function type(i: number, raw: string) {
    const typed = raw.replace(/\D/g, '')
    if (!typed) return
    const next = [...digits]
    typed.slice(0, 6 - i).split('').forEach((d, k) => { next[i + k] = d })
    setDigits(next)
    boxes.current[Math.min(i + typed.length, 5)]?.focus()
    if (next.every(Boolean)) submit(next.join(''))
  }

  function key(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace') {
      e.preventDefault()
      const next = [...digits]
      const at = digits[i] ? i : Math.max(i - 1, 0)
      next[at] = ''
      setDigits(next)
      boxes.current[at]?.focus()
    } else if (e.key === 'ArrowLeft') boxes.current[i - 1]?.focus()
    else if (e.key === 'ArrowRight') boxes.current[i + 1]?.focus()
  }

  async function resend() {
    setError('')
    setNote('')
    try {
      await api.resendCode()
      setNote('A new code is on its way.')
      setWait(COOLDOWN)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="page auth">
      <header className="hero">
        <Sparkle className="hero-mark" />
        <h1>Check your email</h1>
        <p className="tagline">We sent a 6-digit code to <strong>{user.email}</strong>.</p>
      </header>
      <form className="glass auth-card" onSubmit={e => { e.preventDefault(); submit() }}>
        <h2>Enter your code</h2>
        <div className="otp-boxes" role="group" aria-label="6-digit code">
          {digits.map((d, i) => (
            <input
              key={i}
              ref={el => { boxes.current[i] = el }}
              className="otp-box"
              value={d}
              onChange={e => type(i, e.target.value)}
              onKeyDown={e => key(i, e)}
              onPaste={e => { e.preventDefault(); type(i, e.clipboardData.getData('text')) }}
              onFocus={e => e.target.select()}
              inputMode="numeric"
              autoComplete={i === 0 ? 'one-time-code' : 'off'}
              maxLength={i === 0 ? 6 : 1}
              aria-label={`Digit ${i + 1}`}
              autoFocus={i === 0}
            />
          ))}
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        {note && !error && <p className="muted small">{note}</p>}
        <button className="primary" disabled={busy || code.length !== 6}>{busy ? 'Checking…' : 'Verify'}</button>
        <button type="button" className="link" onClick={resend} disabled={wait > 0}>
          {wait > 0 ? `Resend code in ${wait}s` : 'Resend code'}
        </button>
        <button type="button" className="link" onClick={onSignOut}>Wrong email? Sign out</button>
      </form>
    </div>
  )
}

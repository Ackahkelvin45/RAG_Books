import { useState } from 'react'
import { api, type MinistryRole, type User } from './api'
import Sparkle from './Sparkle'

const ROLES: { value: MinistryRole; label: string; hint: string }[] = [
  { value: 'member', label: 'Member', hint: 'I attend the church' },
  { value: 'shepherd', label: 'Shepherd', hint: 'I care for a group of members' },
  { value: 'pastor', label: 'Pastor', hint: 'I lead in ministry' },
]

export default function Profile({ user, onDone, onSignOut }: { user: User; onDone: () => void; onSignOut: () => void }) {
  // Names from Google are already known: don't ask again.
  const namesKnown = user.google && !!user.first_name && !!user.last_name
  const [first, setFirst] = useState(user.first_name ?? '')
  const [last, setLast] = useState(user.last_name ?? '')
  const [dob, setDob] = useState(user.date_of_birth ?? '')
  const [ministry, setMinistry] = useState<MinistryRole | null>(user.ministry_role)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const today = new Date().toISOString().slice(0, 10)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!ministry) { setError('Please choose member, shepherd or pastor.'); return }
    setBusy(true)
    setError('')
    try {
      await api.saveProfile({ first_name: first, last_name: last, date_of_birth: dob, ministry_role: ministry })
      onDone()
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
        <h1>{namesKnown ? `Welcome, ${user.first_name}` : 'Welcome'}</h1>
        <p className="tagline">A few details before you start.</p>
      </header>
      <form className="glass auth-card" onSubmit={submit}>
        <h2>Your details</h2>
        {!namesKnown && (
          <div className="two">
            <label>
              First name
              <input className="field" value={first} onChange={e => setFirst(e.target.value)} required autoComplete="given-name" />
            </label>
            <label>
              Last name
              <input className="field" value={last} onChange={e => setLast(e.target.value)} required autoComplete="family-name" />
            </label>
          </div>
        )}
        <label>
          Date of birth
          <input className="field" type="date" value={dob} onChange={e => setDob(e.target.value)} required min="1900-01-01" max={today} autoComplete="bday" />
        </label>
        <fieldset className="roles">
          <legend>I am a</legend>
          {ROLES.map(r => (
            <label key={r.value} className={`role ${ministry === r.value ? 'on' : ''}`}>
              <input type="radio" name="ministry" value={r.value} checked={ministry === r.value} onChange={() => setMinistry(r.value)} />
              <strong>{r.label}</strong>
              <span>{r.hint}</span>
            </label>
          ))}
        </fieldset>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Continue'}</button>
        <button type="button" className="link" onClick={onSignOut}>Not you? Sign out</button>
      </form>
    </div>
  )
}

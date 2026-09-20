import { Suspense, lazy, useEffect, useState } from 'react'
import { api, type User } from './api'
import { usePath } from './router'
import Auth from './Auth'
import Chat from './Chat'
import Read from './Read'
const Book = lazy(() => import('./Book'))   // epub.js is heavy; only the reader page pays for it
import Profile from './Profile'
import Verify from './Verify'

export default function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined) // undefined = still checking
  const path = usePath()

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null))
  }, [])

  if (user === undefined) return <div className="center muted">Loading…</div>
  if (user === null) return <Auth onSignedIn={() => api.me().then(setUser)} />
  const signOut = () => api.logout().then(() => setUser(null))
  if (!user.email_verified) return <Verify user={user} onDone={() => api.me().then(setUser)} onSignOut={signOut} />
  if (!user.profile_complete) return <Profile user={user} onDone={() => api.me().then(setUser)} onSignOut={() => api.logout().then(() => setUser(null))} />

  const read = path.match(/^\/read\/([\w-]+)$/)
  if (read) return <Read id={read[1]} />
  const book = path.match(/^\/book\/([\w-]+)$/)
  if (book) return <Suspense fallback={<div className="center muted">Opening the book…</div>}><Book id={book[1]} passageId={new URLSearchParams(location.search).get('p')} /></Suspense>
  const conv = path.match(/^\/c\/([\w-]+)$/)
  return <Chat user={user} conversationId={conv ? conv[1] : null} onSignOut={() => api.logout().then(() => setUser(null))} />
}

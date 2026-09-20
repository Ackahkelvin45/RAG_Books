// Thin client for the FastAPI JSON API (api/chat.py). Cookies carry the session.

export type MinistryRole = 'member' | 'shepherd' | 'pastor'
export type User = {
  id: string
  email: string
  name: string | null
  role: 'member' | 'leader' | 'admin'
  first_name: string | null
  last_name: string | null
  date_of_birth: string | null
  ministry_role: MinistryRole | null
  google: boolean
  email_verified: boolean
  profile_complete: boolean
}
export type ProfileInput = { first_name: string; last_name: string; date_of_birth: string; ministry_role: MinistryRole }
export type Citation = {
  n: number
  chunk_id: string
  title: string
  author: string | null
  location: { chapter?: number | null; title?: string | null; page?: number | null }
  scriptures: string[]
  url: string
}
export type Message = { role: 'user' | 'assistant'; content: string; citations: Citation[]; status?: string }
export type ConversationSummary = { id: string; title: string | null; updated_at: string }
export type Passage = {
  id: string
  source_id: string
  title: string
  author: string | null
  location: Citation['location']
  text: string
  scriptures: { ref: string; text: string }[]
  prev_id: string | null
  next_id: string | null
}
export type AskEvent =
  | { type: 'conversation'; id: string }
  | { type: 'classification'; label: string }
  | { type: 'status'; text: string }
  | { type: 'text'; text: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'error'; message: string }

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!r.ok) {
    let message = 'Something went wrong.'
    try {
      const body = await r.json()
      message = typeof body.detail === 'string' ? body.detail : body.detail?.[0]?.msg?.replace(/^Value error, /, '') ?? message
    } catch { /* non-JSON error body */ }
    throw new ApiError(r.status, message)
  }
  return r.json()
}

const post = <T,>(path: string, body: unknown) => call<T>(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  me: () => call<User>('/me'),
  login: (email: string, password: string) => post('/login', { email, password }),
  signup: (email: string, password: string) => post('/signup', { email, password }),
  authConfig: () => call<{ google: boolean }>('/auth/config'),
  verifyEmail: (code: string) => post('/verify-email', { code }),
  resendCode: () => post('/resend-code', {}),
  saveProfile: (p: ProfileInput) => call('/profile', { method: 'PUT', body: JSON.stringify(p) }),
  logout: () => post('/logout', {}),
  conversations: () => call<ConversationSummary[]>('/conversations'),
  conversation: (id: string) => call<Message[]>(`/conversations/${id}`),
  deleteConversation: (id: string) => call(`/conversations/${id}`, { method: 'DELETE' }),
  passage: (id: string) => call<Passage>(`/passages/${id}`),
}

/** POST /api/ask and yield server-sent events as they arrive. */
export async function* ask(question: string, conversationId: string | null, signal?: AbortSignal): AsyncGenerator<AskEvent> {
  const r = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_id: conversationId }),
    signal,
  })
  if (!r.ok || !r.body) throw new ApiError(r.status, r.status === 401 ? 'Please sign in again.' : 'Could not reach the server.')
  const reader = r.body.pipeThrough(new TextDecoderStream()).getReader()
  let buf = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buf += value
    let i
    while ((i = buf.indexOf('\n\n')) >= 0) {
      const frame = buf.slice(0, i)
      buf = buf.slice(i + 2)
      if (frame.startsWith('data: ')) yield JSON.parse(frame.slice(6)) as AskEvent
    }
  }
}

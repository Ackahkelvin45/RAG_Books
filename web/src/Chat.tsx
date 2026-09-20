import { useEffect, useRef, useState } from 'react'
import { api, ask, type ConversationSummary, type Message, type User } from './api'
import { AnswerText, Sources } from './Answer'
import { AI_LABEL, HEADLINE, PLACEHOLDER, SUGGESTIONS, TAGLINE } from './brand'
import { linkProps, navigate } from './router'
import Sparkle from './Sparkle'

export default function Chat({ user, conversationId, onSignOut }: { user: User; conversationId: string | null; onSignOut: () => void }) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState('')
  const [drawer, setDrawer] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const streamedId = useRef<string | null>(null) // conversation just created by our own stream: don't reload it

  const refreshList = () => api.conversations().then(setConversations).catch(() => {})
  useEffect(() => { refreshList() }, [])

  useEffect(() => {
    setDrawer(false)
    setError('')
    if (!conversationId) { setMessages([]); return }
    if (conversationId === streamedId.current) return
    api.conversation(conversationId).then(setMessages).catch(() => navigate('/', true))
  }, [conversationId])

  // Follow the answer as it streams, but only while the reader is already near the bottom:
  // scrolling up to re-read an earlier turn must not be yanked back on every token.
  // The message list scrolls inside .scroll, not the window, so listen there.
  const stickToBottom = useRef(true)
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const onScroll = () => { stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120 }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [])
  useEffect(() => {
    if (stickToBottom.current) endRef.current?.scrollIntoView({ block: 'end', behavior: streaming ? 'auto' : 'smooth' })
  }, [messages, streaming])

  async function send(question: string) {
    question = question.trim()
    if (!question || streaming) return
    setInput('')
    setError('')
    setStreaming(true)
    stickToBottom.current = true
    setMessages(m => [...m, { role: 'user', content: question, citations: [] }, { role: 'assistant', content: '', citations: [] }])
    const patchLast = (f: (m: Message) => Message) => setMessages(ms => [...ms.slice(0, -1), f(ms[ms.length - 1])])
    try {
      for await (const ev of ask(question, conversationId)) {
        if (ev.type === 'conversation' && ev.id !== conversationId) {
          streamedId.current = ev.id
          navigate(`/c/${ev.id}`, true)
        } else if (ev.type === 'status') patchLast(m => ({ ...m, status: ev.text }))
        else if (ev.type === 'text') patchLast(m => ({ ...m, content: m.content + ev.text, status: undefined }))
        else if (ev.type === 'citations') patchLast(m => ({ ...m, citations: ev.citations }))
        else if (ev.type === 'error') setError(ev.message)
      }
    } catch (err) {
      setError((err as Error).message)
      setMessages(ms => ms[ms.length - 1]?.content ? ms : ms.slice(0, -1))
    } finally {
      setStreaming(false)
      refreshList()
    }
  }

  async function remove(id: string) {
    if (!confirm('Delete this conversation?')) return
    await api.deleteConversation(id)
    if (id === conversationId) navigate('/')
    refreshList()
  }

  return (
    <div className="page chat">
      <div className="topbar">
        <button className="ghost" onClick={() => setDrawer(true)} aria-label="Your conversations" style={{ fontWeight: 700 }}>☰ Chats</button>
        {messages.length > 0 && <a className="ghost" {...linkProps('/')}>+ New</a>}
        <span className="spacer" />
        <span className="who">{user.name || user.email}</span>
        <button className="ghost" onClick={onSignOut}>Sign out</button>
      </div>

      {drawer && <div className="scrim" onClick={() => setDrawer(false)} />}
      <aside className={`drawer glass ${drawer ? 'open' : ''}`} inert={!drawer}>
        <div className="drawer-head">
          <strong>Your conversations</strong>
          <button className="ghost" onClick={() => setDrawer(false)} aria-label="Close">×</button>
        </div>
        <a className="suggestion new-chat" {...linkProps('/')}>+ New conversation</a>
        <nav className="conv-list">
          {conversations.length === 0 && <p className="muted small">No conversations yet.</p>}
          {conversations.map(c => (
            <div key={c.id} className={`conv ${c.id === conversationId ? 'active' : ''}`}>
              <a {...linkProps(`/c/${c.id}`)}>{c.title || 'Untitled'}</a>
              <button className="ghost" aria-label="Delete conversation" onClick={() => remove(c.id)}>×</button>
            </div>
          ))}
        </nav>
      </aside>

      <div className="scroll" ref={scrollRef}>
        <div className="stage">
          <header className="hero">
            <Sparkle className="hero-mark" />
            <h1>{HEADLINE}</h1>
            <p className="tagline">{TAGLINE}</p>
          </header>

          <div className="grow" />

          {messages.length === 0 ? (
            <section className="suggestions">
              <h2>Suggestions on what to ask {AI_LABEL}</h2>
              <div className="suggestion-row">
                {SUGGESTIONS.map(q => <button key={q} className="suggestion" onClick={() => send(q)}>{q}</button>)}
              </div>
            </section>
          ) : (
            <section className="thread">
              {messages.map((m, i) => (
                m.role === 'user' ? (
                  <div key={i} className="turn me">
                    <span className="who-label">Me</span>
                    <div className="bubble">{m.content}</div>
                  </div>
                ) : (
                  <div key={i} className="turn ai">
                    <span className="who-label">{AI_LABEL}</span>
                    <div className={`bubble${streaming && i === messages.length - 1 ? ' live' : ''}`}>
                      {m.content
                        ? <><AnswerText text={m.content} citations={m.citations} /><Sources citations={m.citations} /></>
                        : <span className="thinking-row"><Sparkle size={30} className="thinking" />{m.status && <span className="status">{m.status}…</span>}</span>}
                    </div>
                  </div>
                )
              ))}
              {error && <p className="error" role="alert">{error}</p>}
              <div ref={endRef} />
            </section>
          )}
        </div>
      </div>

      <form className="composer" onSubmit={e => { e.preventDefault(); send(input) }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
          placeholder={PLACEHOLDER}
          rows={1}
          maxLength={2000}
          aria-label="Your question"
        />
        <button className="send" disabled={streaming || !input.trim()} aria-label="Send">
          <svg width="34" height="34" viewBox="0 0 34 34" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round">
            <path d="M4 4 L31 17 L4 30 L9 17 Z" />
            <path d="M9 17 H19" strokeLinecap="round" />
          </svg>
        </button>
      </form>
    </div>
  )
}

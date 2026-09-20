import { useEffect, useState } from 'react'
import { api, type Passage } from './api'
import { chapterLabel } from './Answer'
import { linkProps } from './router'
import Sparkle from './Sparkle'

export default function Read({ id }: { id: string }) {
  const [p, setP] = useState<Passage | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setP(null)
    api.passage(id).then(setP).catch(e => setError(e.status === 404 ? 'This passage is not available.' : e.message))
    window.scrollTo(0, 0)
  }, [id])

  const back = () => (history.length > 1 ? history.back() : (location.href = '/'))

  return (
    <div className="page read">
      <div className="topbar"><button className="ghost" onClick={back}>← Back</button></div>
      <div className="read-inner">
        {error && <p className="error">{error}</p>}
        {!p && !error && <Sparkle size={34} className="thinking dark" />}
        {p && (
          <>
            <header className="read-head">
              <Sparkle size={36} className="hero-mark" />
              <h1>{p.title}</h1>
              <p className="muted">{p.author}{chapterLabel(p.location, ' · ')}</p>
            </header>
            <article className="glass read-body">
              {p.text.split(/\n{2,}/).map((para, i) => <p key={i}>{para}</p>)}
            </article>
            {p.scriptures.length > 0 && (
              <section className="glass verses">
                <h2>Scriptures in this passage</h2>
                {p.scriptures.map(s => (
                  <div key={s.ref} className="verse">
                    <strong>{s.ref}</strong>
                    {s.text && <p>{s.text}</p>}
                  </div>
                ))}
                <p className="muted small">Verse text: American Standard Version.</p>
              </section>
            )}
            <nav className="pager book-links">
              <a className="suggestion" {...linkProps(`/book/${p.source_id}?p=${p.id}`)}>📖 Open the book at this passage</a>
              <a className="suggestion" href={`/api/books/${p.source_id}/file?download=1`}>⬇ Download EPUB</a>
            </nav>
            <nav className="pager">
              {p.prev_id ? <a className="suggestion" {...linkProps(`/read/${p.prev_id}`)}>← Previous passage</a> : <span />}
              {p.next_id ? <a className="suggestion" {...linkProps(`/read/${p.next_id}`)}>Next passage →</a> : <span />}
            </nav>
          </>
        )}
      </div>
    </div>
  )
}

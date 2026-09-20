import ePub, { type Book as EpubBook, type Rendition } from 'epubjs'
import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import Sparkle from './Sparkle'

type TocItem = { label: string; href: string }

/** Whole-book reader (epub.js). Opens at the cited passage when `passageId` is given,
 *  found by matching the passage's opening words against each chapter's text. */
export default function Book({ id, passageId }: { id: string; passageId: string | null }) {
  const view = useRef<HTMLDivElement>(null)
  const rendition = useRef<Rendition | null>(null)
  const [book, setBook] = useState<EpubBook | null>(null)
  const [title, setTitle] = useState('')
  const [toc, setToc] = useState<TocItem[]>([])
  const [current, setCurrent] = useState('')
  const [status, setStatus] = useState('Opening the book…')
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    let b: EpubBook | null = null
    ;(async () => {
      try {
        const r = await fetch(`/api/books/${id}/file`, { credentials: 'same-origin' })
        if (!r.ok) throw new Error(r.status === 404 ? 'This book is not available.' : 'Could not open the book.')
        b = ePub(await r.arrayBuffer())
        await b.ready
        if (!alive) return
        setTitle(b.packaging.metadata.title)
        setToc(flatten(b.navigation.toc))
        const rd = b.renderTo(view.current!, { width: '100%', height: '100%', flow: 'paginated', spread: 'none' })
        rd.themes.default({ body: { 'font-family': 'Georgia, serif', 'line-height': '1.7', padding: '0 1.5rem !important' } })
        rd.on('relocated', (loc: { start: { href: string } }) => setCurrent(loc.start.href))
        rendition.current = rd
        setBook(b)
        const start = passageId ? await locatePassage(b, passageId) : null
        setStatus('')
        await rd.display(start ?? undefined)
      } catch (e) {
        if (alive) { setError((e as Error).message); setStatus('') }
      }
    })()
    return () => { alive = false; rendition.current?.destroy(); b?.destroy() }
  }, [id, passageId])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') rendition.current?.next()
      if (e.key === 'ArrowLeft') rendition.current?.prev()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const back = () => (history.length > 1 ? history.back() : (location.href = '/'))
  const here = toc.find(t => current && t.href.split('#')[0] === current.split('#')[0])

  return (
    <div className="page book">
      <div className="topbar">
        <button className="ghost" onClick={back}>← Back</button>
        <span className="title">{title}</span>
        <span className="spacer" />
        {toc.length > 0 && (
          <select value={here?.href ?? ''} onChange={e => rendition.current?.display(e.target.value)} aria-label="Chapter">
            {!here && <option value="">Contents</option>}
            {toc.map(t => <option key={t.href} value={t.href}>{t.label}</option>)}
          </select>
        )}
        <a className="ghost" href={`/api/books/${id}/file?download=1`}>⬇ Download</a>
      </div>
      <div className="book-view" ref={view}>
        {(status || error) && (
          <div className="book-loading">
            {error ? <p className="error">{error}</p> : <><Sparkle size={34} className="thinking dark" /><p className="muted">{status}</p></>}
          </div>
        )}
      </div>
      {book && (
        <nav className="book-nav">
          <button className="suggestion" onClick={() => rendition.current?.prev()}>← Previous page</button>
          <span className="muted">{here?.label ?? ''}</span>
          <button className="suggestion" onClick={() => rendition.current?.next()}>Next page →</button>
        </nav>
      )}
    </div>
  )
}

function flatten(items: { label: string; href: string; subitems?: unknown[] }[]): TocItem[] {
  return items.flatMap(i => [{ label: i.label.trim(), href: i.href }, ...flatten((i.subitems ?? []) as typeof items)])
}

const norm = (s: string) => s.toLowerCase().replace(/\s+/g, ' ').trim()

/** The spine section that contains the passage's first sentence, as an href epub.js can display. */
async function locatePassage(book: EpubBook, passageId: string): Promise<string | null> {
  try {
    const p = await api.passage(passageId)
    const needle = norm(p.text).slice(0, 80)
    if (!needle) return null
    const hrefs: string[] = []
    book.spine.each((s: { href: string }) => { hrefs.push(s.href) })
    for (const href of hrefs) {
      const section = book.spine.get(href)
      if (!section) continue
      const doc = await section.load(book.load.bind(book)) as Document
      const hit = norm(doc.body?.textContent ?? '').includes(needle)
      section.unload()
      if (hit) return href
    }
  } catch { /* fall through to the book's start */ }
  return null
}

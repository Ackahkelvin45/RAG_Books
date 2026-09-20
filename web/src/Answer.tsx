import type { Components } from 'react-markdown'
import Markdown, { defaultUrlTransform } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Citation } from './api'
import { linkProps } from './router'

/** Answer markdown, with [n] citation markers rendered as links to the cited passage.
 *  Renders partial text while it streams: unclosed emphasis or a half-written list is shown as plain text
 *  until the closing marker arrives, so nothing jumps around. */
export function AnswerText({ text, citations }: { text: string; citations: Citation[] }) {
  const byN = new Map(citations.map(c => [c.n, c]))
  // [3] -> a link the markdown parser understands; the `a` renderer turns it back into a citation
  const src = text.replace(/\[(\d+)\]/g, '[$1](cite:$1)')
  const components: Components = {
    a: ({ href, children }) => {
      const n = href?.startsWith('cite:') ? Number(href.slice(5)) : null
      if (n === null) return <a href={href} target="_blank" rel="noreferrer">{children}</a>
      const c = byN.get(n)
      return c
        ? <a className="cite" {...linkProps(`/read/${c.chunk_id}`)} title={`${c.title}${chapterLabel(c.location, ', ')}`}>{n}</a>
        : <sup>{n}</sup>
    },
    p: ({ children }) => {
      const first = Array.isArray(children) ? children[0] : children
      const scripture = typeof first === 'string' && first.startsWith('Scriptures referenced:')
      return <p className={scripture ? 'scripture-line' : undefined}>{children}</p>
    },
  }
  // react-markdown drops link schemes it doesn't know, which would empty out every cite: href
  const urlTransform = (url: string) => (url.startsWith('cite:') ? url : defaultUrlTransform(url))
  return <Markdown remarkPlugins={[remarkGfm]} components={components} urlTransform={urlTransform}>{src}</Markdown>
}

export function chapterLabel(loc: Citation['location'], prefix = '') {
  if (loc?.chapter) return `${prefix}Chapter ${loc.chapter}${loc.title ? `: ${loc.title}` : ''}`
  if (loc?.page) return `${prefix}Page ${loc.page}`
  return ''
}

export function Sources({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null
  return (
    <div className="sources">
      {citations.map(c => (
        <a key={c.n} className="source" {...linkProps(`/read/${c.chunk_id}`)}>
          <span className="source-n">{c.n}</span>
          <span className="source-body">
            <strong>{c.title}</strong>
            <span className="muted">{chapterLabel(c.location) || 'Passage'}</span>
            {c.scriptures.length > 0 && <span className="source-verses">{c.scriptures.slice(0, 4).join('; ')}{c.scriptures.length > 4 ? '…' : ''}</span>}
          </span>
          <span className="source-read">Read</span>
        </a>
      ))}
    </div>
  )
}

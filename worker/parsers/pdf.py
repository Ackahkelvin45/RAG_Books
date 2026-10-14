"""PDF (text layer) -> sections. Chapters come from the outline when the file has one; without one each
page is a section. Scanned PDFs (no text layer) are refused: OCR is not built, by decision 2026-10-14."""
from __future__ import annotations

from pathlib import Path

import pymupdf

from . import ParsedBook, Section
from .epub import _CHAPTER

MIN_CHARS_PER_PAGE = 50   # average below this = scanned images, not text


def _page_text(page) -> str:
    """Text blocks become paragraphs; the hard line breaks inside a block are joined."""
    blocks = [" ".join(b[4].split()) for b in page.get_text("blocks") if b[6] == 0]
    return "\n\n".join(b for b in blocks if b)


def parse_pdf(path: Path) -> ParsedBook:
    doc = pymupdf.open(str(path))
    pages = [_page_text(p) for p in doc]
    if not pages or sum(len(t) for t in pages) / len(pages) < MIN_CHARS_PER_PAGE:
        raise ValueError("PDF has no text layer (scanned); OCR is not supported")
    meta = doc.metadata or {}
    outline = [(title, page - 1) for level, title, page in doc.get_toc() if level == 1 and page >= 1]
    sections: list[Section] = []
    if outline:
        # pages before the first entry are front matter (cover, contents) and are dropped
        bounds = [*outline, (None, len(pages))]
        numbered = any(_CHAPTER.match(t or "") for t, _ in outline)
        seq = 0
        for (title, start), (_, end) in zip(bounds, bounds[1:]):
            text = "\n\n".join(t for t in pages[start:end] if t)
            if not text:
                continue
            m = _CHAPTER.match(title or "")
            if m:
                chapter, title = int(m.group(1)), (m.group(2).strip() or title)
            elif numbered:
                chapter = None             # preface, epilogue: named, not numbered
            else:
                seq += 1
                chapter = seq
            sections.append(Section(text=text, chapter=chapter, title=title, page=start + 1))
    else:
        sections = [Section(text=t, page=i + 1) for i, t in enumerate(pages) if t]
    return ParsedBook(sections=sections, title=(meta.get("title") or "").strip() or None,
                      author=(meta.get("author") or "").strip() or None)

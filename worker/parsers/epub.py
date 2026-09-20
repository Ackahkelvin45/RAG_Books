"""EPUB -> sections. Walks the spine so chapter order matches the reader."""
from __future__ import annotations

import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from ebooklib import ITEM_DOCUMENT, epub

from . import ParsedBook, Section

MIN_WORDS = 150   # an unnumbered section shorter than this is front/back matter

_CHAPTER = re.compile(r"^\s*chapter\s+(\d+)\b[\s:.\-\u2013\u2014]*(.*)$", re.I)
_FRONT_MATTER = re.compile(
    r"unless otherwise stated, all scripture|all rights reserved|^\s*(table of )?contents\b|for a complete list of titles",
    re.I | re.M,
)
_CONTENTS_PAGE = re.compile(r"^\s*(table of )?contents\b", re.I)   # dropped whatever its length


def _meta(book: epub.EpubBook, name: str) -> str | None:
    vals = book.get_metadata("DC", name)
    return ((vals[0][0] or "").strip() or None) if vals else None


def _heading(soup: BeautifulSoup) -> str | None:
    for tag in ("h1", "h2", "h3"):
        for h in soup.find_all(tag):
            t = " ".join(h.get_text(" ", strip=True).split())
            if t and not _CHAPTER.match(t):
                return t
    return None


def _clean(soup: BeautifulSoup) -> str:
    for junk in soup(["script", "style", "nav"]):
        junk.decompose()
    lines = [" ".join(l.split()) for l in (soup.body or soup).get_text("\n").splitlines()]
    text = "\n".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def _chapter_of(text: str) -> tuple[int | None, str | None]:
    """'Chapter 3\nA Culture of Allegiance ...' or 'CHAPTER 3: Title' -> (3, 'A Culture of Allegiance')."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return None, None
    m = _CHAPTER.match(lines[0])
    if not m:
        return None, None
    title = m.group(2).strip() or (lines[1].strip() if len(lines) > 1 else None)
    return int(m.group(1)), title


def parse_epub(path: Path) -> ParsedBook:
    book = epub.read_epub(str(path), options={"ignore_ncx": True})
    raw: list[tuple[str, BeautifulSoup]] = []
    for idref, _linear in book.spine:
        item = book.get_item_with_id(idref)
        if item is None or item.get_type() != ITEM_DOCUMENT:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
            soup = BeautifulSoup(item.get_content(), "lxml")
        heading = _heading(soup)
        text = _clean(soup)
        if text:
            raw.append((text, heading))

    numbered = any(_chapter_of(t)[0] is not None for t, _ in raw)
    sections: list[Section] = []
    seq = 0
    for text, heading in raw:
        if _CONTENTS_PAGE.match(text):
            continue
        num, title = _chapter_of(text)
        if num is not None:
            prev = next((x.chapter for x in reversed(sections) if x.chapter is not None), None)
            if num == prev:        # typo in the book: "Chapter 9" printed twice for 9 and 10
                num = prev + 1
            sections.append(Section(text=text, chapter=num, title=heading or title))
            continue
        words = len(text.split())
        if words < MIN_WORDS or (_FRONT_MATTER.search(text[:400]) and words < 600):
            continue
        if numbered:
            # unnumbered prose in a numbered book: introduction, preface, epilogue
            sections.append(Section(text=text, chapter=None, title=heading))
        else:
            seq += 1
            sections.append(Section(text=text, chapter=seq, title=heading))
    return ParsedBook(sections=sections, title=_meta(book, "title"), author=_meta(book, "creator"))

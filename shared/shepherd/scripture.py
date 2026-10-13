"""Scripture reference extraction and formatting, via pythonbible.

Verse ids are integers of the form BBCCCVVV (John 3:16 -> 43003016), so a
chapter or book is a contiguous integer range. Do not hand-roll the regex.
"""
from __future__ import annotations

import re

import pythonbible as pb


# Book names that are also everyday words. "his secular job", "the numbers 7 and 12", "a mark of
# honour" all parse as references when a number follows (seen in production: three lay-ministry
# passages showed "Job 1:1-22"). A printed reference is always capitalised, so require the
# capitalised stem ("Rev", "Num" cover the abbreviations too) somewhere in the text.
_EVERYDAY_WORDS = {"Job": "Job", "Mark": "Mar", "Acts": "Act", "Numbers": "Num", "Judges": "Jud",
                   "Revelation": "Rev", "Lamentations": "Lam", "1 Kings": "Kin", "2 Kings": "Kin"}


def extract_verse_ids(text: str) -> list[int]:
    """All verse ids referenced in `text`, sorted and de-duplicated."""
    ids: set[int] = set()
    for ref in _safe_references(text):
        # A bare book name ("Psalms", "John", "James") resolves to every verse in
        # that book, and in prose it is often a person's name. Require a chapter.
        if ref.start_chapter is None:
            continue
        stem = _EVERYDAY_WORDS.get(ref.book.title)
        if stem and not re.search(rf"\b{stem}", text):
            continue
        try:
            ids.update(pb.convert_reference_to_verse_ids(ref))
        except pb.errors.InvalidVerseError:
            continue
    return sorted(ids)


def _safe_references(text: str) -> list:
    """pythonbible raises on some prose ("...too big (pre-eminence) to receive from John.").
    Retry line by line and drop only the lines it cannot parse; those are prose, not references."""
    try:
        return pb.get_references(text)
    except Exception:  # noqa: BLE001 - library bug on malformed input, not ours to fix
        refs = []
        for line in text.splitlines():
            try:
                refs.extend(pb.get_references(line))
            except Exception:  # noqa: BLE001
                continue
        return refs


def chapter_range(book: pb.Book, chapter: int) -> tuple[int, int]:
    """Inclusive integer range covering every verse of one chapter."""
    base = book.value * 1_000_000 + chapter * 1_000
    return base + 1, base + 999


def book_range(book: pb.Book) -> tuple[int, int]:
    base = book.value * 1_000_000
    return base + 1, base + 999_999


def format_reference(verse_id: int) -> str:
    return pb.format_scripture_references(pb.convert_verse_ids_to_references([verse_id]))


def format_references(verse_ids: list[int]) -> list[str]:
    """Verse ids -> readable references, consecutive verses collapsed: ['Romans 8:28-30', 'John 3:16']."""
    if not verse_ids:
        return []
    return [pb.format_scripture_references([r]) for r in pb.convert_verse_ids_to_references(sorted(set(verse_ids)))]


def verse_text(verse_id: int) -> str:
    """Public-domain (ASV) verse text, safe to display alongside copyrighted books."""
    return pb.get_verse_text(verse_id, version=pb.Version.AMERICAN_STANDARD)

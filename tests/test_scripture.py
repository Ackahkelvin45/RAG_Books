import pythonbible as pb

from shepherd.scripture import book_range, chapter_range, extract_verse_ids, format_reference, verse_text


def test_extracts_single_verse():
    assert 43003016 in extract_verse_ids("For God so loved the world (John 3:16).")


def test_extracts_range_and_multiple_books():
    ids = extract_verse_ids("See Romans 8:28-30 and Psalm 23:1.")
    assert {45008028, 45008029, 45008030, 19023001} <= set(ids)


def test_no_references_gives_empty():
    assert extract_verse_ids("Nothing scriptural here, just chapter 4 of a novel.") == []


def test_chapter_and_book_ranges():
    lo, hi = chapter_range(pb.Book.ROMANS, 8)
    assert lo <= 45008028 <= hi and not (lo <= 45007001 <= hi)
    lo, hi = book_range(pb.Book.JOHN)
    assert lo <= 43003016 <= hi


def test_format_and_public_domain_text():
    assert format_reference(43003016) == "John 3:16"
    assert "loved the world" in verse_text(43003016)


def test_bare_book_names_are_ignored():
    assert extract_verse_ids("Then John and James walked on, reading the Psalms aloud.") == []


def test_chapter_only_reference_keeps_whole_chapter():
    ids = extract_verse_ids("Compare Matthew 5.")
    assert len(ids) == 48 and ids[0] == 40005001


def test_prose_that_crashes_the_library_is_skipped_not_fatal():
    text = ("John the Apostle could not minister effectively to Diotrephes because he felt too big "
            "(pre-eminence) to receive from John. I believe this chapter matters.\nSee Romans 8:28.")
    assert 45008028 in extract_verse_ids(text)

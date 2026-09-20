from shepherd.chunking import chunk_text, whitespace_tokens


def test_packs_paragraphs_to_target_and_never_exceeds_max():
    paras = [f"Paragraph {i}. " + "word " * 80 for i in range(12)]  # ~82 tokens each
    text = "\n\n".join(paras)
    chunks = chunk_text(text, whitespace_tokens, target=400, max_tokens=500, overlap_ratio=0.15)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.token_count <= 500
    assert all(c.index == i for i, c in enumerate(chunks))


def test_overlap_repeats_tail_of_previous_chunk():
    paras = [" ".join(f"P{i} sentence {j} has five words." for j in range(20)) for i in range(10)]  # ~120 tok each
    chunks = chunk_text("\n\n".join(paras), whitespace_tokens, target=300, max_tokens=400)
    first_tail = chunks[0].text.split("\n\n")[-1]
    # overlap is either whole trailing paragraphs or the trailing sentences of the last one
    assert chunks[1].text.startswith(first_tail) or (
        chunks[1].text.split("\n\n")[0] in first_tail and len(chunks[1].text.split("\n\n")[0]) > 20
    )


def test_oversized_paragraph_is_split_by_sentence():
    para = " ".join(f"Sentence number {i} is here." for i in range(300))  # one paragraph, ~1500 tokens
    chunks = chunk_text(para, whitespace_tokens, target=200, max_tokens=250)
    assert len(chunks) > 3
    assert all(c.token_count <= 250 for c in chunks)


def test_short_text_is_one_chunk():
    chunks = chunk_text("Just a line.\n\nAnd another.", whitespace_tokens)
    assert len(chunks) == 1
    assert "Just a line." in chunks[0].text and "And another." in chunks[0].text

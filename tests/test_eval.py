"""Eval harness scoring logic, and the per-step query log it tunes from. No network."""
import os

os.environ["SHEPHERD_EMBEDDER"] = "fake"
os.environ["SHEPHERD_RERANKER"] = "fake"

import json  # noqa: E402

from eval.run import cited_sentences, rate, run_settings, seed, summarize_full, summarize_retrieval  # noqa: E402
from shepherd import answer, config  # noqa: E402
from test_answer import ANSWERABLE, P, fake_llm, pastor  # noqa: E402,F401 - fixtures reused


def test_cited_sentences_moves_trailing_markers_back_to_their_sentence():
    text = "Disloyalty is a process [2]. It starts small. [1][3] Pray for them.\n\nA talks about this."
    assert cited_sentences(text) == [("Disloyalty is a process.", [2]), ("It starts small.", [1, 3])]


def test_settings_name_every_model_and_knob():
    # 2026-09-20 and 2026-10-13 retrieval runs could not be compared: neither said which reranker ran
    s = run_settings(["retrieval"])
    assert s["models"] == config.MODELS and s["embed_model"] == config.EMBED_MODEL and s["rerank_model"] == config.RERANK_MODEL
    assert s["rerank_activation"] == "identity" and s["chunk_min_tail"] == 80 and s["reranker"] == "fake"


def test_seed_loads_labelled_real_questions_as_their_own_kind(app, admin, tmp_path):
    f = tmp_path / "user.jsonl"
    f.write_text(json.dumps({"question": "my member keeps missing church", "expected": "answerable"}) + "\n")
    seed(app, f, "user")
    try:
        assert admin.execute("select count(*) from eval_items where kind = 'user'").fetchone()[0] == 1
        assert admin.execute("select count(*) from eval_items where kind = 'hand'").fetchone()[0] == \
            admin.execute("select count(*) from eval_items where kind = 'hand'").fetchone()[0]   # other kinds untouched
    finally:
        admin.execute("delete from eval_items where kind = 'user'")


def test_rate_ignores_unmeasured():
    assert rate([True, False, None, True]) == 66.7 and rate([None]) is None


def test_retrieval_summary_counts_hits_within_final_k():
    rows = [
        {"expected": "answerable", "kind": "generated", "wants_chunk": True, "wants_book": True, "chunk_rank": 1, "book_rank": 1, "top_score": 0.9},
        {"expected": "answerable", "kind": "generated", "wants_chunk": True, "wants_book": True, "chunk_rank": 12, "book_rank": 3, "top_score": 0.7},
        {"expected": "refuse", "kind": "hand", "wants_chunk": False, "wants_book": False, "chunk_rank": None, "book_rank": None, "top_score": 0.1},
    ]
    s = summarize_retrieval(rows)
    assert s["passage_hit@1 %"] == 50.0 and s["passage_hit@8 %"] == 50.0
    assert s["passage_mrr"] == round((1 + 1 / 12) / 2, 3)
    assert s["book_hit@8 generated %"] == 100.0
    assert s["top_score refuse p50"] == 0.1


def test_full_summary_scores_each_behaviour():
    rows = [
        {"expected": "answerable", "refused": False, "book": "B", "cited_books": ["B"], "seconds": 1,
         "judged": [{"supported": True}, {"supported": False}]},
        {"expected": "answerable", "refused": True, "book": None, "cited_books": [], "seconds": 1},
        {"expected": "refuse", "refused": True, "book": None, "seconds": 1},
        {"expected": "crisis", "refused": False, "label": "sensitive", "text": "x" + answer.SAFETY_NOTE, "book": None, "seconds": 1},
        {"expected": "injection", "resisted": True, "seconds": 1},
    ]
    s = summarize_full(rows)
    assert s["answered (not wrongly refused) %"] == 50.0
    assert s["citations supported %"] == 50.0 and s["expected book cited %"] == 100.0
    assert s["correct refusals %"] == 100.0 and s["crisis safety line %"] == 100.0
    assert s["injections resisted %"] == 100.0 and s["off-scope declined %"] is None


def test_query_log_records_search_query_scores_and_citations(app, pastor, fake_llm, monkeypatch):  # noqa: F811
    p1, p2 = P("first"), P("second")
    p1.score, p2.score = 0.8, 0.4
    monkeypatch.setattr(answer, "retrieve", lambda *a, **k: [p1, p2])
    fake_llm(ANSWERABLE, ["Only the second [2]."])
    list(answer.ask(app, "a question", pastor))
    q, scores, retrieved, cited, search_ms, answer_ms, models = app.execute(
        "select retrieval_query, scores, retrieved_ids::text[], cited_ids::text[], search_ms, answer_ms, models "
        "from query_logs where user_id = %s", (pastor,)).fetchone()
    assert q == "a question" and scores == [0.8, 0.4]
    assert retrieved == [p1.chunk_id, p2.chunk_id] and cited == [p2.chunk_id]
    assert search_ms is not None and answer_ms is not None     # every answer times itself
    assert models == config.MODELS                              # and says which models answered
    app.commit()

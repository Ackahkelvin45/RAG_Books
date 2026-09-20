"""Stage 4: generated questions per chunk, and the retrieval list that searches them. No network."""
import os

os.environ["SHEPHERD_EMBEDDER"] = "fake"
os.environ["SHEPHERD_RERANKER"] = "fake"

from pgvector.psycopg import register_vector  # noqa: E402

from shepherd import llm, questions  # noqa: E402
from shepherd.embed import get_embedder  # noqa: E402
from shepherd.retrieve import question_candidates  # noqa: E402
from test_retrieve import corpus  # noqa: E402,F401 - fixture reused


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class ByPassage:
    """Thread-safe fake: the reply depends on the passage, not on call order."""
    chat = completions = property(lambda self: self)

    def create(self, messages, **kw):
        text = messages[-1]["content"]
        reply = "NONE" if "Unfinished" in text or "pending" in text else \
            "1. How do I stay patient in trouble?\n- What does hope do for me?\nSome preamble without a question mark"
        return _Obj(choices=[_Obj(message=_Obj(content=reply))])


def test_fill_writes_questions_and_embedding_and_is_resumable(admin, app, corpus, monkeypatch):  # noqa: F811
    monkeypatch.setattr(llm, "client", lambda: ByPassage())
    while questions.fill_batch(app, batch=2):
        pass
    rows = dict(admin.execute("select id::text, questions from chunks where source_id in (%s, %s)",
                              (corpus["leader"], corpus["member"])).fetchall())
    assert rows[corpus["member_chunk"]] == "How do I stay patient in trouble?\nWhat does hope do for me?"
    none = admin.execute("select questions, q_embedding is null from chunks where id = %s", (corpus["pending_chunk"],)).fetchone()
    assert none == ("", True)                       # answered nothing: marked done, not searchable
    assert questions.fill_batch(app) == 0           # nothing left: a rerun is free


def test_question_list_respects_visibility(admin, app, corpus, monkeypatch):  # noqa: F811
    monkeypatch.setattr(llm, "client", lambda: ByPassage())
    while questions.fill_batch(app):
        pass
    register_vector(app)
    qvec = get_embedder().embed(["How do I stay patient in trouble?\nWhat does hope do for me?"])[0]
    with app.transaction():
        member_view = {r[0] for r in question_candidates(app, qvec, "member", [])}
        leader_view = {r[0] for r in question_candidates(app, qvec, "leader", [])}
    assert corpus["leader_chunk"] not in member_view and corpus["member_chunk"] in member_view
    assert corpus["leader_chunk"] in leader_view and corpus["pending_chunk"] not in leader_view

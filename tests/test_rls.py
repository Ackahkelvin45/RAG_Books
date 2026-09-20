"""Schema integrity tests: FK cascade and the auth lookup function."""
import uuid


def test_chunks_cascade_on_source_delete(admin, source):
    sid = source["src"]
    admin.execute("delete from sources where id = %s", (sid,))
    n = admin.execute("select count(*) from chunks where source_id = %s", (sid,)).fetchone()[0]
    assert n == 0


def test_auth_lookup_works(app, admin):
    email = f"leader-{uuid.uuid4().hex[:6]}@example.org"
    admin.execute("insert into users (email, role) values (%s, 'leader')", (email,))
    try:
        with app.transaction():
            row = app.execute("select user_id, role from auth_lookup_user(%s)", (email.upper(),)).fetchone()
        assert row is not None and row[1] == "leader"
    finally:
        admin.execute("delete from users where email = %s", (email,))

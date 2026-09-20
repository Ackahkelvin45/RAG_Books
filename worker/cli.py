"""Ops commands for books.

  python -m worker.cli add    --title "..." --author "..." path/to/book.epub
  python -m worker.cli reingest <source_id>
  python -m worker.cli list
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from shepherd import storage
from shepherd.db import connect, transaction

from .ingest import add_book, enqueue_reingest


def cmd_add(a):
    path = Path(a.path)
    if not path.exists():
        sys.exit(f"no such file {path}")
    with connect() as conn:
        print(add_book(conn, path, a.title, a.author, a.series, a.visibility))


def cmd_add_dir(a):
    """Queue every .epub/.pdf in a folder. Title comes from the file, author from --author. Skips titles already loaded."""
    from ebooklib import epub as _epub

    files = sorted(p for p in Path(a.path).iterdir() if p.suffix.lower() in (".epub", ".pdf"))
    with connect() as conn:
        with transaction(conn):
            have = {r[0].lower() for r in conn.execute("select title from sources where status <> 'superseded'")}
        added = skipped = 0
        for f in files:
            title = None
            if f.suffix.lower() == ".epub":
                meta = _epub.read_epub(str(f), options={"ignore_ncx": True}).get_metadata("DC", "title")
                title = ((meta[0][0] or "").strip() if meta else "") or None
            title = title or f.stem
            if title.isupper():
                title = title.title()
            if title.lower() in have:
                skipped += 1
                continue
            add_book(conn, f, title, a.author, None, a.visibility)
            have.add(title.lower())
            added += 1
            print(f"queued {title}")
    print(f"{added} queued, {skipped} already loaded")


def cmd_reingest(a):
    with connect() as conn:
        print(enqueue_reingest(conn, a.source_id))


def cmd_list(a):
    with connect() as conn:
        with transaction(conn):
            rows = conn.execute(
                "select s.id, s.version, s.status, s.title, "
                " (select count(*) from chunks c where c.source_id = s.id), s.failure_reason "
                "from sources s order by created_at"
            ).fetchall()
    for r in rows:
        print(f"{r[0]}  v{r[1]}  {r[2]:<10} chunks={r[4]:<5} {r[3]}" + (f"  [{r[5]}]" if r[5] else ""))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add"); s.add_argument("path")
    s.add_argument("--title"); s.add_argument("--author"); s.add_argument("--series")
    s.add_argument("--visibility", default="member", choices=["leader", "member"]); s.set_defaults(f=cmd_add)
    s = sub.add_parser("add-dir"); s.add_argument("path"); s.add_argument("--author", required=True)
    s.add_argument("--visibility", default="member", choices=["leader", "member"]); s.set_defaults(f=cmd_add_dir)
    s = sub.add_parser("reingest"); s.add_argument("source_id"); s.set_defaults(f=cmd_reingest)
    s = sub.add_parser("list"); s.set_defaults(f=cmd_list)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()

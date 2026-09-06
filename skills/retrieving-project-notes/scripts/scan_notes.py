#!/usr/bin/env python3
"""Scan project notes and print only their YAML frontmatter.

Frontmatter-only scan is the FAST stage of note retrieval: it never reads a
note body, so it stays cheap over hundreds of notes. Full note bodies are
read later by the agent only for notes the scan shows to be relevant.

Two retrieval surfaces are surfaced for every note:
  1. filename  yyyy-mm-dd-topic.md   (authoritative date + topic)
  2. frontmatter keys                type, date, topic, title, module, tags, sources

Usage (run from the repo root, or point --root at a notes tree):

  # all notes, newest first
  python scripts/scan_notes.py

  # narrow by the three "range" dimensions
  python scripts/scan_notes.py --root .agents/notes --type archived
  python scripts/scan_notes.py --since 2026-06-01 --until 2026-09-30
  python scripts/scan_notes.py --type fixed --since 2026-08-01
  python scripts/scan_notes.py --title "rag-eval"        # fuzzy, case-insensitive
  python scripts/scan_notes.py --title "RAG" --since 2026-07-01

  # machine-readable for chaining into grep/jq
  python scripts/scan_notes.py --type rejected --json

Dependencies: none (stdlib only). Runs on Windows too. Notes files must be
UTF-8; undecodable bytes are replaced rather than fatal.
Only files matching the note filename convention (a leading yyyy-mm-dd date,
then the topic, dash-joined) OR files that carry the `type:` frontmatter key
are treated as notes. Other Markdown files are skipped in the default
(frontmatter) output but shown when --all is given, so stray docs surface
instead of silently vanishing.
"""

import argparse
import json
import os
import re
import sys

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)$")
FM_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


class Note:
    __slots__ = ("path", "rel", "meta", "malformed")

    def __init__(self, path, rel, meta, malformed=False):
        self.path = path          # absolute path
        self.rel = rel            # path relative to --root, posix separators
        self.meta = meta          # parsed frontmatter dict (string/list/none values)
        self.malformed = malformed


def read_frontmatter(path):
    """Return (meta_dict, malformed_bool). meta values are str or list of str.

    A minimal YAML-subset reader: enough for the normalized note schema
    (top-level scalar keys plus flow `[a, b]` or block `- item` list values),
    not a general YAML parser. Nested mappings such as `sources:` are recorded
    as the value True (key present) — their leaf paths are not needed for a
    retrieval scan.
    """
    meta = {}
    malformed = False
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return meta, True

    # A stray byte-order mark (BOM) defeats the first-line fence check below,
    # because strip() does not treat U+FEFF as whitespace.
    if lines and lines[0].startswith("﻿"):
        lines[0] = lines[0][1:]

    # Locate the opening fence on line 1.
    if not lines or lines[0].strip() != "---":
        return meta, False  # no frontmatter at all — not an error

    cur_key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break  # closing fence
        if not line.strip():
            continue
        if line[:1].isspace():
            stripped = line.strip()
            # Block list item under the current key, e.g. "- item".
            if cur_key is not None and stripped.startswith("- "):
                item = stripped[2:].strip()
                if item and not _looks_like_nested_mapping(item):
                    existing = meta.get(cur_key)
                    if not isinstance(existing, list):
                        meta[cur_key] = []
                    meta[cur_key].append(item)
                else:
                    meta.setdefault(cur_key, True)
            else:
                # Indented content (nested mapping under a key) — record that
                # the enclosing key exists, drop the leaf detail.
                meta.setdefault(cur_key or "_", True)
            continue
        # Top-level "key: value" line.
        if ":" not in line:
            malformed = True
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        if not key:
            malformed = True
            continue
        cur_key = key
        value = rest.strip()
        value = _strip_comment(value)
        if value.startswith("["):
            items = [i.strip() for i in value.strip("[]").split(",") if i.strip()]
            if items or value.strip() != "[]":
                meta[key] = items
        elif value == "":
            meta[key] = True  # nested block follows
        else:
            meta[key] = value
    return meta, malformed


def _strip_comment(value):
    """Remove a trailing ' # comment' but keep '#' inside a quoted/scalar value."""
    if value.startswith(('"', "'")):
        return value
    idx = value.find(" #")
    return value[:idx] if idx != -1 else value


def _looks_like_nested_mapping(text):
    return ":" in text


def _find_notes(root):
    notes = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip obvious non-note dirs so scans stay fast and quiet.
        dirnames[:] = [d for d in dirnames if d not in ("local", "node_modules", ".git")]
        for fname in sorted(filenames):
            if not fname.endswith((".md", ".markdown")):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            meta, malformed = read_frontmatter(full)
            notes.append(Note(full, rel, meta, malformed))
    return notes


def _is_note(note):
    """Note filename convention OR carries the note-schema `type:` key."""
    if DATE_RE.match(os.path.basename(note.path)):
        return True
    return note.meta.get("type") is not None


def _name_date(fname):
    m = DATE_RE.match(fname)
    if m:
        return "%s-%s-%s" % m.groups()[:3]
    return None


def _meta_date(note):
    raw = note.meta.get("date")
    if isinstance(raw, str):
        m = FM_DATE_RE.match(raw)
        if m:
            return m.group(1)
    return None


def _note_date(note):
    return _name_date(os.path.basename(note.path)) or _meta_date(note) or ""


def _display_row(note):
    """Compact one-line summary: file, date, type, title, tags, module."""
    m = note.meta
    date = _note_date(note)
    typ = m.get("type")
    if not isinstance(typ, str):
        typ = ""
    title = m.get("title", "") if isinstance(m.get("title"), str) else ""
    tags = m.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    tag_str = ",".join(tags)
    module = m.get("module", "") if isinstance(m.get("module"), str) else ""
    return {
        "file": note.rel,
        "date": date,
        "type": typ,
        "title": title,
        "tags": tag_str,
        "module": module,
        "malformed": note.malformed,
    }


def _type_ok(note, want):
    typ = note.meta.get("type")
    if not isinstance(typ, str):
        return False
    return typ == want


def _title_match(note, needle, anywhere):
    """Fuzzy title/topic match: all needle words must appear (case-insensitive).

    Substrings are tested against the note filename (minus the date prefix),
    the frontmatter topic, and the frontmatter title. With --any-word, a
    single word is enough; by default every word must match.
    """
    needle = needle.strip().lower()
    if not needle:
        return True
    words = [w for w in re.split(r"[\s_\-\./]+", needle) if w]
    base = os.path.basename(note.path)
    m = DATE_RE.match(base)
    haystack = (m.group(4) if m else base).lower()
    for key in ("topic", "title"):
        val = note.meta.get(key)
        if isinstance(val, str):
            haystack += " " + val.lower()
    if anywhere:
        return any(w in haystack for w in words)
    return all(w in haystack for w in words)


def _date_filter(note, since, until):
    date = _note_date(note)
    if not date:
        return False  # undated note: excluded from date-filtered scans
    if since and date < since:
        return False
    if until and date > until:
        return False
    return True


def _json_type(rows):
    return {
        "notes": [
            {
                "file": r["file"],
                "date": r["date"] or None,
                "type": r["type"] or None,
                "title": r["title"] or None,
                "tags": [t for t in r["tags"].split(",") if t] if r["tags"] else [],
                "module": r["module"] or None,
                "frontmatter_malformed": r["malformed"],
            }
            for r in rows
        ]
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print YAML frontmatter of project notes (fast retrieval scan)."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Notes tree to scan (default: .agents/notes under the working dir)",
    )
    parser.add_argument("--type", help="Only notes of this type, e.g. archived|fixed|rejected")
    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Only notes dated on/after this date (filename date, else frontmatter date)",
    )
    parser.add_argument(
        "--until",
        metavar="YYYY-MM-DD",
        help="Only notes dated on/before this date",
    )
    parser.add_argument(
        "--date", metavar="YYYY-MM-DD", help="Only notes dated exactly on this date"
    )
    parser.add_argument(
        "--title",
        help="Fuzzy title/topic filter: every space-separated word must appear "
        "in the filename topic, topic, or title (case-insensitive)",
    )
    parser.add_argument(
        "--any-word",
        action="store_true",
        help="With --title: match if ANY word appears (default: all words)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also list Markdown files with no note frontmatter (as type '?')",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit JSON instead of a text table"
    )
    parser.add_argument(
        "--no-header", action="store_true", help="Omit the column header row"
    )
    parser.add_argument(
        "--no-print-malformed", action="store_true", help="Silence malformed-frontmatter warnings"
    )
    args = parser.parse_args(argv)

    root = args.root or os.path.join(os.getcwd(), ".agents", "notes")
    if not os.path.isdir(root):
        parser.error("notes root not found: %s" % root)

    notes = _find_notes(root)

    if args.date:
        args.since = args.since or args.date
        args.until = args.until or args.date

    rows = []
    skipped = 0
    for note in notes:
        if not _is_note(note):
            if not args.all:
                skipped += 1
                continue
        if args.type and not _type_ok(note, args.type):
            continue
        if (args.since or args.until) and not _date_filter(note, args.since, args.until):
            continue
        if args.title and not _title_match(note, args.title, args.any_word):
            continue
        rows.append(_display_row(note))
        if note.malformed and not args.no_print_malformed:
            print("warning: malformed frontmatter in %s" % note.rel, file=sys.stderr)

    # Newest first; ties broken by path for determinism. Notes with no usable
    # date (not in the filename and none in frontmatter) sort below dated ones.
    rows.sort(
        key=lambda r: (r["date"] != "", r["date"] or "0000-00-00", r["file"]),
        reverse=True,
    )

    if args.json:
        print(json.dumps(_json_type(rows), ensure_ascii=False, indent=2))
        return 0

    if args.no_header or not rows:
        for r in rows:
            print(r["file"])
        return 0

    # Column widths from data + headers.
    keys = ["file", "date", "type", "title", "tags", "module"]
    headers = ["file", "date", "type", "title", "tags", "module"]
    widths = {k: len(h) for k, h in zip(keys, headers)}
    for r in rows:
        for k in keys:
            widths[k] = max(widths[k], len(r[k]))
    sep = "  "
    print(sep.join(h.ljust(widths[k]) for k, h in zip(keys, headers)))
    print(sep.join("-" * widths[k] for k in keys))
    for r in rows:
        print(sep.join(r[k].ljust(widths[k]) for k in keys))
    return 0


if __name__ == "__main__":
    sys.exit(main())

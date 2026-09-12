#!/usr/bin/env python3
"""Scan agent rules and print only their YAML frontmatter.

Frontmatter-only scan is the FAST stage of working with rules: it never reads a
rule body, so it stays cheap over many rules and lets an agent decide what a
rule requires without opening it (the normative clause lives in `statement:`).

Two retrieval surfaces are surfaced for every rule:
  1. filename  <id>.md               (flat; id == filename base)
  2. frontmatter keys                schema, id, statement, status, modality,
                                     paths, triggers, check, tags, sources,
                                     overrides, supersedes, date, updated

The modality vocabulary is the four v1 values (require, forbid, prefer, allow);
the status vocabulary is (draft, active, superseded, retired). Both are compared
generically here, so neither is hardcoded into the scan logic.

Usage (run from the repo root, or point --root at a rules tree):

  # all rules, by modality then id
  python scripts/scan_rules.py

  # narrow by the filter dimensions
  python scripts/scan_rules.py --status active --modality forbid
  python scripts/scan_rules.py --path "**/*.md"          # rules governing a path
  python scripts/scan_rules.py --trigger git-commit
  python scripts/scan_rules.py --unverified              # check is manual/review
  python scripts/scan_rules.py --tag documents

  # conformance + cross-rule lints (these DO read bodies: R16)
  python scripts/scan_rules.py --validate
  python scripts/scan_rules.py --conflicts
  python scripts/scan_rules.py --dangling

  # regenerate the rules index as Markdown
  python scripts/scan_rules.py --index > .agents/rules/README.md

  # machine-readable
  python scripts/scan_rules.py --json

Dependencies: none (stdlib only). Runs on Windows too. Rule files must be
UTF-8; undecodable bytes are replaced rather than fatal.

Scope semantics: absent `paths` and absent `triggers` means the rule is GLOBAL,
rendered as `always`. Silence is never narrowness.
"""

import argparse
import json
import os
import re
import sys

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_KEYS = ("schema", "id", "statement", "status", "modality", "check", "date")
KNOWN_KEYS = set(REQUIRED_KEYS) | {
    "paths", "triggers", "tags", "sources", "overrides", "supersedes", "updated",
}
STATUSES = ("draft", "active", "superseded", "retired")
MODALITIES = ("require", "forbid", "prefer", "allow")
MODALITY_RANK = {"allow": 0, "prefer": 1, "require": 2, "forbid": 3}
KNOWN_TRIGGERS = {
    "file-write", "file-delete", "git-commit", "git-push", "shell",
    "plan", "answer", "note-write", "rule-write", "skill-invoke",
}
REQUIRED_HEADINGS = ("## Rationale", "## Check", "## Exceptions")
SCHEMA_VALUE = "agent-rules/v1"
MAX_STATEMENT = 200


class Rule:
    __slots__ = ("path", "rel", "meta", "malformed")

    def __init__(self, path, rel, meta, malformed=False):
        self.path = path
        self.rel = rel
        self.meta = meta
        self.malformed = malformed


# --------------------------------------------------------------------------
# frontmatter reader (stdlib-only YAML subset; scalars + flow/block lists)
# --------------------------------------------------------------------------

def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _strip_comment(value):
    """Remove a trailing ' # comment' but keep '#' inside a quoted value."""
    if value.startswith(('"', "'")):
        return value
    idx = value.find(" #")
    return value[:idx] if idx != -1 else value


def read_frontmatter(path):
    """Return (meta_dict, malformed_bool). meta values are str, list, or True.

    A minimal YAML-subset reader: enough for the rule schema, which is
    deliberately flat (top-level scalars plus flow `[a, b]` or block `- item`
    list values) so that every field stays filterable. Nested content under a
    key is recorded as the value True (key present) and its leaf detail dropped.
    """
    meta = {}
    malformed = False
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return meta, True

    # A stray byte-order mark defeats the first-line fence check below,
    # because strip() does not treat U+FEFF as whitespace.
    if lines and lines[0].startswith("\ufeff"):
        lines[0] = lines[0][1:]

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
            if cur_key is not None and stripped.startswith("- "):
                item = _unquote(stripped[2:].strip())
                if item:
                    existing = meta.get(cur_key)
                    if not isinstance(existing, list):
                        meta[cur_key] = []
                    meta[cur_key].append(item)
                else:
                    meta.setdefault(cur_key, True)
            else:
                meta.setdefault(cur_key or "_", True)
            continue
        if ":" not in line:
            malformed = True
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        if not key:
            malformed = True
            continue
        cur_key = key
        value = _strip_comment(rest.strip())
        if value.startswith("["):
            inner = value.strip()
            inner = inner[1:inner.rfind("]")] if "]" in inner else inner[1:]
            items = [_unquote(i.strip()) for i in inner.split(",") if i.strip()]
            meta[key] = items if (items or value.strip() != "[]") else []
        elif value == "":
            meta[key] = True  # a nested/block value follows
        else:
            meta[key] = _unquote(value)
    return meta, malformed


def read_body(path):
    """Return the text after the closing frontmatter fence (for R16 only)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return ""
    if not lines or lines[0].strip() != "---":
        return "\n".join(lines)
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1:])
    return ""


# --------------------------------------------------------------------------
# field accessors (defensive: malformed values degrade, never crash)
# --------------------------------------------------------------------------

def _str(rule, key, default=""):
    val = rule.meta.get(key)
    return val if isinstance(val, str) else default


def _list(rule, key):
    val = rule.meta.get(key)
    if isinstance(val, list):
        return [v for v in val if isinstance(v, str)]
    if isinstance(val, str):
        return [val]
    return []


def rid(rule):
    return _str(rule, "id")


def status(rule):
    return _str(rule, "status")


def modality(rule):
    return _str(rule, "modality")


def paths(rule):
    return _list(rule, "paths")


def triggers(rule):
    return _list(rule, "triggers")


def check(rule):
    return _str(rule, "check")


def scope_text(rule):
    """Compact, honest rendering: absent scope is rendered `always`."""
    p, t = paths(rule), triggers(rule)
    parts = []
    if p:
        parts.append("paths=" + ",".join(p))
    if t:
        parts.append("triggers=" + ",".join(t))
    return " ".join(parts) if parts else "always"


def is_global(rule):
    return not paths(rule) and not triggers(rule)


def unverified(rule):
    return check(rule).lower() in ("manual", "review", "")


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

def _find_rules(root):
    rules = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git")]
        for fname in sorted(filenames):
            if not fname.endswith((".md", ".markdown")):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            meta, malformed = read_frontmatter(full)
            rules.append(Rule(full, rel, meta, malformed))
    return rules


def _is_rule(rule):
    """A rule carries the schema marker or an `id:` key in its frontmatter."""
    if rule.meta.get("id") is not None:
        return True
    schema = rule.meta.get("schema")
    return isinstance(schema, str) and schema.startswith("agent-rules/")


# --------------------------------------------------------------------------
# scope matching (for --path / --trigger) and overlap (for --conflicts)
# --------------------------------------------------------------------------

def glob_to_re(pattern):
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                if i + 2 < len(pattern) and pattern[i + 2] == "/":
                    out.append("(?:.*/)?")  # "**/" also matches zero directories
                    i += 3
                else:
                    out.append(".*")
                    i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _literal_prefix(pattern):
    idx = len(pattern)
    for w in ("*", "?", "["):
        p = pattern.find(w)
        if p != -1:
            idx = min(idx, p)
    return pattern[:idx]


def paths_overlap(a, b):
    """Conservative heuristic: shared literal prefix, or either side unscoped."""
    if not a or not b:
        return True
    for p in a:
        for q in b:
            pp, qp = _literal_prefix(p), _literal_prefix(q)
            if pp.startswith(qp) or qp.startswith(pp):
                return True
    return False


def triggers_overlap(a, b):
    if not a or not b:
        return True
    return bool(set(a) & set(b))


def scopes_overlap(a, b):
    return paths_overlap(paths(a), paths(b)) and triggers_overlap(triggers(a), triggers(b))


def _specificity(rule):
    """(how many scope dimensions are pinned, total literal chars)."""
    dims = (1 if paths(rule) else 0) + (1 if triggers(rule) else 0)
    literals = sum(len(_literal_prefix(p)) for p in paths(rule))
    literals += sum(len(t) for t in triggers(rule))
    return (dims, literals)


def resolve(a, b):
    """Precedence per docs/agent-rules-schema.md.

    Returns (winner, reason, verdict), where verdict is 'resolved' when the
    ordering is a deliberate signal (an explicit override, or a narrower scope
    — specificity is intent) and 'ambiguous' when the two rules merely tie and
    the winner is only the conservative reading. An 'ambiguous' pair is a defect
    in the rule set: it needs an explicit `overrides` or a narrower scope.
    """
    if rid(b) in _list(a, "overrides"):
        return a, "explicit override", "resolved"
    if rid(a) in _list(b, "overrides"):
        return b, "explicit override", "resolved"
    sa, sb = _specificity(a), _specificity(b)
    if sa != sb:
        return (a if sa > sb else b), "narrower scope", "resolved"
    ra, rb = MODALITY_RANK.get(modality(a), 0), MODALITY_RANK.get(modality(b), 0)
    if ra != rb:
        return ((a if ra > rb else b),
                "conservative reading (restriction beats permission)", "ambiguous")
    return (a if rid(a) <= rid(b) else b), "id order", "ambiguous"


# --------------------------------------------------------------------------
# conformance (R1-R16) and cross-rule lints
# --------------------------------------------------------------------------

def _repo_root(args, root):
    if args.repo_root:
        return args.repo_root
    if os.path.basename(os.path.normpath(root)) == "rules":
        return os.path.dirname(os.path.normpath(root))
    return os.getcwd()


def validate_rule(rule, all_ids, superseded_by, repo_root, check_body=True):
    """Return a list of (level, code, message). level is 'error' or 'warning'."""
    issues = []

    def err(code, msg):
        issues.append(("error", code, msg))

    def warn(code, msg):
        issues.append(("warning", code, msg))

    # R1 — flat path: rules-root/<id>.md
    if "/" in rule.rel:
        err("R1", "not flat: expected rules-root/<id>.md, got %s" % rule.rel)

    # R2 — frontmatter parses
    if rule.malformed:
        err("R2", "malformed frontmatter")

    # R3 — required keys
    for key in REQUIRED_KEYS:
        if key not in rule.meta:
            err("R3", "missing required key: %s" % key)

    # R4 — id slug + equals filename base
    base = os.path.basename(rule.path)
    base = base[: -len(".markdown")] if base.endswith(".markdown") else base[:-3]
    rid_val = rid(rule)
    if not rid_val:
        err("R4", "missing id")
    else:
        if not ID_RE.match(rid_val):
            err("R4", "id is not a slug: %r" % rid_val)
        if rid_val != base:
            err("R4", "id %r != filename base %r" % (rid_val, base))

    # R5 / R6 — enums
    if status(rule) not in STATUSES:
        err("R5", "status not in %s: %r" % ("|".join(STATUSES), status(rule)))
    if modality(rule) not in MODALITIES:
        err("R6", "modality not in %s: %r" % ("|".join(MODALITIES), modality(rule)))

    # R7 — statement shape and phrasing
    stmt = _str(rule, "statement")
    if not stmt:
        err("R7", "missing statement")
    else:
        if len(stmt) > MAX_STATEMENT:
            err("R7", "statement is %d chars (max %d) — split it into two rules"
                % (len(stmt), MAX_STATEMENT))
        if "\n" in stmt:
            err("R7", "statement must be a single line")
        prefix_bad = {
            "forbid": lambda s: not s.startswith(("Never ", "Do not ", "Don't ")),
            "require": lambda s: s.startswith(("Never ", "Do not ", "Don't ", "May ", "Prefer ")),
            "prefer": lambda s: not s.startswith("Prefer "),
            "allow": lambda s: " may " not in " %s " % s,
        }.get(modality(rule))
        if prefix_bad and prefix_bad(stmt):
            warn("R7", "statement phrasing does not match modality %r: %r"
                 % (modality(rule), stmt[:60]))

    # R8 — list fields
    for key in ("paths", "triggers", "tags"):
        val = rule.meta.get(key)
        if val is None:
            continue
        if not isinstance(val, list) or not all(isinstance(v, str) and v for v in val):
            err("R8", "%s must be a list of non-empty strings" % key)
    for trig in triggers(rule):
        if trig not in KNOWN_TRIGGERS:
            warn("R8", "unknown trigger %r" % trig)

    # R9 — check resolves
    chk = check(rule)
    if not chk:
        err("R9", "missing check")
    elif chk.lower() not in ("manual", "review"):
        candidates = [os.path.join(repo_root, chk), os.path.join(os.getcwd(), chk)]
        if not any(os.path.exists(c) for c in candidates):
            err("R9", "check path does not exist: %r" % chk)

    # R10 — references resolve
    for key in ("overrides", "supersedes"):
        for ref in _list(rule, key):
            if ref not in all_ids:
                err("R10", "dangling %s reference: %r" % (key, ref))

    # R11 — superseded <-> named in an active rule's supersedes
    named = rid(rule) in superseded_by
    if status(rule) == "superseded" and not named:
        err("R11", "status is superseded but no active rule names it in supersedes")
    if status(rule) != "superseded" and named:
        err("R11", "named in an active rule's supersedes but status is %r" % status(rule))

    # R12 — updated >= date
    updated = _str(rule, "updated")
    if updated:
        if not DATE_RE.match(updated):
            err("R12", "updated is not YYYY-MM-DD: %r" % updated)
        elif DATE_RE.match(_str(rule, "date")) and updated < _str(rule, "date"):
            err("R12", "updated %s is before date %s" % (updated, _str(rule, "date")))

    # R13 — schema value
    if _str(rule, "schema") != SCHEMA_VALUE:
        err("R13", "schema must be exactly %r, got %r" % (SCHEMA_VALUE, _str(rule, "schema")))

    # R14 — unknown keys
    unknown = sorted(set(rule.meta) - KNOWN_KEYS)
    if unknown:
        warn("R14", "unknown top-level key(s): %s" % ", ".join(unknown))

    # R16 — body sections (only in validate mode; this is the one body read)
    if check_body:
        body = read_body(rule.path)
        missing = [h for h in REQUIRED_HEADINGS if h not in body]
        if missing:
            err("R16", "body missing section(s): %s" % ", ".join(missing))

    return issues


def validate(rules, repo_root, strict=False):
    all_ids = {rid(r) for r in rules if rid(r)}
    superseded_by = set()
    for r in rules:
        if status(r) == "active":
            superseded_by.update(_list(r, "supersedes"))

    seen, results = {}, []
    for rule in rules:
        issues = validate_rule(rule, all_ids, superseded_by, repo_root)
        key = rid(rule)
        if key:
            if key in seen:
                issues.append(("error", "R15", "duplicate id %r (also in %s)"
                               % (key, seen[key])))
            else:
                seen[key] = rule.rel
        results.append((rule, issues))
    return results


def find_conflicts(rules):
    """Pairs of live rules with overlapping scope and differing modality."""
    live = [r for r in rules if status(r) in ("active", "draft")]
    out = []
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            if modality(a) == modality(b) or not modality(a) or not modality(b):
                continue
            # An explicit override is a deliberate resolution, not a conflict.
            if rid(b) in _list(a, "overrides") or rid(a) in _list(b, "overrides"):
                continue
            if not scopes_overlap(a, b):
                continue
            winner, reason, verdict = resolve(a, b)
            level = "error" if verdict == "ambiguous" else "warning"
            out.append((level, a, b, winner, reason))
    return out


def find_dangling(rules):
    all_ids = {rid(r) for r in rules if rid(r)}
    by_id = {rid(r): r for r in rules if rid(r)}
    out = []
    for rule in rules:
        for key in ("overrides", "supersedes"):
            for ref in _list(rule, key):
                if ref not in all_ids:
                    out.append(("%s" % rid(rule), key, ref, "missing"))
                elif key == "overrides" and status(by_id[ref]) == "draft":
                    out.append((rid(rule), key, ref, "target is draft"))
    return out


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

SCAN_KEYS = ("id", "status", "modality", "scope", "check", "statement")


def _scan_row(rule):
    return {
        "id": rid(rule),
        "status": status(rule),
        "modality": modality(rule),
        "scope": scope_text(rule),
        "check": check(rule),
        "statement": _str(rule, "statement"),
        "file": rule.rel,
        "paths": paths(rule),
        "triggers": triggers(rule),
        "tags": _list(rule, "tags"),
        "sources": _list(rule, "sources"),
        "overrides": _list(rule, "overrides"),
        "supersedes": _list(rule, "supersedes"),
        "date": _str(rule, "date"),
        "updated": _str(rule, "updated"),
        "global": is_global(rule),
        "unverified": unverified(rule),
        "malformed": rule.malformed,
    }


def _sort_rows(rows):
    """Live rules first, most restrictive modality first, then id."""
    status_rank = {"active": 0, "draft": 1, "superseded": 2, "retired": 3}

    def key(r):
        return (
            status_rank.get(r["status"], 4),
            -MODALITY_RANK.get(r["modality"], -1),
            r["id"],
        )
    return sorted(rows, key=key)


def _print_table(rows, no_header=False):
    if not rows:
        return
    widths = {k: len(k) for k in SCAN_KEYS}
    for r in rows:
        for k in SCAN_KEYS:
            widths[k] = max(widths[k], len(r[k]))
    if not no_header:
        print("  ".join(k.ljust(widths[k]) for k in SCAN_KEYS))
        print("  ".join("-" * widths[k] for k in SCAN_KEYS))
    for r in rows:
        print("  ".join(r[k].ljust(widths[k]) for k in SCAN_KEYS))


def _print_index(rows, schema_link):
    """A whole .agents/rules/README.md, regenerated from frontmatter."""
    live = [r for r in rows if r["status"] in ("active", "draft")]
    out = [
        "# Agent rules",
        "",
        "Constraints in force on the agent, one rule per file. Generated from rule",
        "frontmatter by `scripts/scan_rules.py --index` — **do not hand-edit**; edit the",
        "rule files and regenerate.",
        "",
        "The schema is `agent-rules/v1`; the authoritative field list, precedence rule,",
        "and conformance checks live in [`%s`](%s)." % (schema_link, schema_link),
        "",
        "## In force",
        "",
        "| Rule | Modality | Scope | Statement |",
        "|---|---|---|---|",
    ]
    if not live:
        out.append("| _(none yet)_ | | | |")
    for r in live:
        scope = "always" if r["global"] else r["scope"]
        out.append("| [`%s`](%s) | `%s` | `%s` | %s |"
                   % (r["id"], r["file"], r["modality"], scope, r["statement"]))
    out += ["", "`always` means the rule has no `paths` and no `triggers` — it is global.", ""]

    history = [r for r in rows if r["status"] in ("superseded", "retired")]
    if history:
        out += ["## No longer in force", "", "| Rule | Status | Superseded by |", "|---|---|---|"]
        for r in history:
            superseded_by = [x["id"] for x in rows if r["id"] in x["supersedes"]]
            out.append("| `%s` | `%s` | %s |"
                       % (r["id"], r["status"], ", ".join(superseded_by) or "—"))
        out.append("")
    print("\n".join(out))


def _print_issues(results, strict):
    errors = warnings = 0
    for rule, issues in results:
        for level, code, msg in issues:
            if level == "error":
                errors += 1
            else:
                warnings += 1
            print("%s: %s [%s] %s: %s"
                  % (level.upper(), rule.rel, code, rid(rule) or "?", msg),
                  file=sys.stderr)
    print("validate: %d error(s), %d warning(s) across %d rule(s)"
          % (errors, warnings, len(results)), file=sys.stderr)
    return 1 if (errors or (strict and warnings)) else 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scan agent-rule frontmatter (fast retrieval / index / lint)."
    )
    parser.add_argument("--root", default=None,
                        help="Rules tree to scan (default: .agents/rules under the working dir)")
    parser.add_argument("--repo-root", default=None,
                        help="Repo root used to resolve `check` paths (default: cwd)")
    parser.add_argument("--status", help="Only rules with this status, e.g. active|draft|superseded|retired")
    parser.add_argument("--modality", help="Only rules with this modality: require|forbid|prefer|allow")
    parser.add_argument("--path", help="Only rules whose scope could govern this repo-relative path")
    parser.add_argument("--trigger", help="Only rules that govern this lifecycle trigger")
    parser.add_argument("--tag", help="Only rules carrying this tag")
    parser.add_argument("--since", metavar="YYYY-MM-DD", help="Only rules dated on/after this date")
    parser.add_argument("--until", metavar="YYYY-MM-DD", help="Only rules dated on/before this date")
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="Only rules dated exactly on this date")
    parser.add_argument("--unverified", action="store_true",
                        help="Only rules whose check is manual/review (advisory rules)")
    parser.add_argument("--checkable", action="store_true",
                        help="Only rules with a runnable check path")
    parser.add_argument("--all", action="store_true",
                        help="Also list Markdown files under the root that are not rules")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text table")
    parser.add_argument("--no-header", action="store_true", help="Omit the column header row")
    parser.add_argument("--validate", action="store_true",
                        help="Check conformance R1-R16 (reads bodies for R16)")
    parser.add_argument("--conflicts", action="store_true",
                        help="Report scope-overlapping rules with differing modality")
    parser.add_argument("--dangling", action="store_true",
                        help="Report overrides/supersedes references that do not resolve")
    parser.add_argument("--index", action="store_true",
                        help="Emit a full .agents/rules/README.md index as Markdown")
    parser.add_argument("--schema-link", default="../skills/writing-agent-rules/references/agent-rules-schema.md",
                        help="Path the generated index links as the rules schema "
                             "(default: the skill's bundled copy under .agents/skills/)")
    parser.add_argument("--strict", action="store_true",
                        help="With --validate: treat warnings as failures")
    args = parser.parse_args(argv)

    root = args.root or os.path.join(os.getcwd(), ".agents", "rules")
    if not os.path.isdir(root):
        parser.error("rules root not found: %s" % root)

    rules = _find_rules(root)
    stray = [r for r in rules if not _is_rule(r)]
    rules = [r for r in rules if _is_rule(r)]

    if args.date:
        args.since = args.since or args.date
        args.until = args.until or args.date

    rows = []
    for rule in rules:
        row = _scan_row(rule)
        if args.status and row["status"] != args.status:
            continue
        if args.modality and row["modality"] != args.modality:
            continue
        if args.tag and args.tag not in row["tags"]:
            continue
        if args.unverified and not row["unverified"]:
            continue
        if args.checkable and row["unverified"]:
            continue
        if args.trigger:
            if row["triggers"] and args.trigger not in row["triggers"]:
                continue
        if args.path:
            if row["paths"] and not any(glob_to_re(p).match(args.path) for p in row["paths"]):
                continue
        if args.since or args.until:
            if not row["date"]:
                continue
            if args.since and row["date"] < args.since:
                continue
            if args.until and row["date"] > args.until:
                continue
        rows.append(row)

    rows = _sort_rows(rows)

    exit_code = 0

    if args.validate:
        results = validate(rules, _repo_root(args, root), args.strict)
        exit_code = max(exit_code, _print_issues(results, args.strict))

    if args.conflicts:
        found = find_conflicts(rules)
        for level, a, b, winner, reason in found:
            if level == "error":
                exit_code = max(exit_code, 1)
            print("%s: %s (%s) vs %s (%s) — %s wins by %s"
                  % (level.upper(), rid(a), modality(a), rid(b), modality(b),
                     rid(winner), reason), file=sys.stderr)
        print("conflicts: %d" % len(found), file=sys.stderr)

    if args.dangling:
        found = find_dangling(rules)
        for owner, key, ref, why in found:
            exit_code = 1
            print("ERROR: %s: %s -> %s (%s)" % (owner, key, ref, why), file=sys.stderr)
        print("dangling: %d" % len(found), file=sys.stderr)

    if args.all:
        for r in stray:
            print("warning: not a rule (no id/schema frontmatter): %s" % r.rel,
                  file=sys.stderr)
            if not args.json:
                print(r.rel)

    # Lint modes report on stderr; the scan table is noise there.
    lint_mode = args.validate or args.conflicts or args.dangling
    if args.index:
        # An index always reflects the whole tree — a filtered subset is not an
        # index. Filters are ignored here on purpose.
        _print_index(_sort_rows([_scan_row(r) for r in rules]), args.schema_link)
    elif args.json:
        print(json.dumps({"rules": rows}, ensure_ascii=False, indent=2))
    elif not lint_mode:
        if args.no_header:
            for r in rows:
                print(r["id"])
        else:
            _print_table(rows, no_header=False)
            if any(r["scope"] == "always" for r in rows):
                print("\n`always` = no paths and no triggers pinned — the rule is global.",
                      file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

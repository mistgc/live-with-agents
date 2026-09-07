---
name: retrieving-project-notes
description: Use when the user asks to search, query, or retrieve project notes, or asks a question the repo's notes may answer — why the repo is in its current state, what feature/defect/decision a topic has seen, what was decided or rejected, what a past feature or defect did. Triggers on phrasing like "what did we decide about X", "find the note on Y", "did we ever reject Z", "what does the repo say about …", or a question about the current state of a feature or module. Retrieves by scanning note frontmatter first, then reading only the relevant notes. Complements the writing-project-notes skill.
---

# Retrieving Project Notes

## Overview

A **project note** is a durable record of *concluded* project knowledge, filed
by type. Notes live under `.agents/notes/` in five types on two semantic tracks
(see `docs/state-lifecycle.md`):

- **Current-truth** — `implemented`, `deprecated`, `fixed`: describe what the
  code *currently* is, kept in step with the code.
- **History** — `archived`: how the repo reached its current shape, AGENT
  recall only, **not** a statement about present code.
- **Terminal** — `rejected`: an explicitly declined proposal.

Each note has two retrieval surfaces:

1. A **filename** `yyyy-mm-dd-topic.md` — the date and topic, readable at a
   glance.
2. A **YAML frontmatter** block — normalized keys (`schema`, `type`, `date`,
   `topic`, `title`, `module`, `tags`, `sources`, `commits`, `updated`) for
   structured lookup.

Retrieval is **two-stage**: first a *cheap scan* that reads only frontmatter —
never note bodies — to produce a one-line-per-note table; then full reads of
only the notes the scan marks as relevant. The scan decides what is worth
reading; nothing is read twice.

## When to Use

- The user asks to **find or query a note**: "is there a note on…", "what did
  we record about…", "show me the notes for this module".
- A question might be **answered by concluded work**: a feature was
  implemented, deprecated, a defect fixed, a proposal rejected, a step
  archived — the note preserves why the repo is the way it is.
- Retrieving **by range**: all notes of a type, of a date window, or whose
  topic/title mentions something.
- Summarizing what the notes say about a goal, a module, or a decision.

**When not to use:** the user wants to *file* concluded work (use
`writing-project-notes`); the answer lives plainly in the code and no note is
likely to add intent (answer from the repo); the notes live in an Obsidian
vault (use the Obsidian note skills); or the user only wants the current code
to be searched with no interest in archived context.

## Match the track to the question

The single most important choice in retrieval is **which track answers the
question** — and a wrong pick silently answers "what is true now" from a
history note, or vice versa:

| Question looks like… | Track to scan | Because |
|---|---|---|
| "What does the repo currently have / is X live / how is X implemented now?" | **current-truth** (`implemented`, `deprecated`, `fixed`) | These are kept in step with the code; they state what is true now |
| "Why / how did the repo get to this state? what happened before? timeline?" | **history** (`archived`) | Snapshots of the path taken — the record of how it got here |
| "Was X ever proposed / considered / declined, and why?" | **terminal** (`rejected`), plus history | Declined proposals have no code to point at; the note is authoritative |
| "Is X currently broken / was it recently fixed?" | `fixed` | Repaired defects; read alongside code to confirm current state |

When the goal is *current state*, treat current-truth notes as authoritative
and **verify against the code** (they should match, but a stale note is
possible). When the goal is *history*, `archived` notes are the record and are
authoritative for the past — do not expect them to match present code.

When unsure, scan the **whole tree** and let the table's `type` column show you
which track each hit belongs to.

## The scan-first rule

**Scan before you read.** Reading the body of every note — or grepping every
body for keywords — is the slow path and pollutes context. The scan table is
built from frontmatter only, so it stays cheap at any note count. Judge
relevance from the *table rows*, not by re-reading.

The scan is deliberately loose: it is a *candidate finder*, not a verdict. A
filter may over- or under-match (substring title matches, notes whose topic the
filter never sees). That is fine — you decide relevance by reading the rows it
returns. **When unsure which range fits, scan wide** (few or no filters) and
let the table show you the candidates; the table is cheap, a wrong guess is
not.

## Retrieval workflow

1. **State the retrieval goal in one sentence.** Name the topic, the track /
   type(s), and the date window you care about. This drives the scan range and,
   later, relevance.

2. **Scan frontmatter.** Pick the range (below) and run the scanner:

   ```bash
   python scripts/scan_notes.py [--root PATH] [--type TYPE] [--since DATE --until DATE | --date DATE] [--title WORDS]
   ```

   The script prints one row per matching note — file, date, type, title, tags,
   module — newest first. It never reads a note body. `TYPE` is one of the five
   v2 types: `implemented` / `deprecated` / `fixed` / `rejected` / `archived`.

3. **Select candidates.** From the table, choose which notes are relevant to the
   goal — **0, 1, or many** (decision table below). Narrow with an extra filter
   only if the table is unwieldy.

4. **Read the selected notes fully.** Open each with the Read tool (they are
   small; several may be read in parallel). Read whole files — a frontmatter row
   is a pointer, not content. Note each hit's `type`: it tells you which track
   you are reading.

5. **Synthesize against the goal.** Answer the retrieval goal from the note
   content and cite each note by its path. Distinguish what a note states from
   what the code shows; if a note looks stale, check the code before trusting
   it — especially a current-truth note that should match the code but may not.

## Choosing the scan range

The range is expressed along three dimensions, in the user's own words:

| User says / retrieval goal | Scan dimension | Invocation |
|---|---|---|
| "the notes", "what have we got", no specific ask yet | (none — browse) | no flags; eyeball everything |
| "implemented features", "deprecated/removed", "fixed bugs", "rejected stuff", "history of X" | type | `--type implemented` · `--type deprecated` · `--type fixed` · `--type rejected` · `--type archived` |
| "what's currently live / in the code" | current-truth types | `--type implemented` (plus `--type deprecated` to see removed) |
| "how did we get here / what happened before" | history | `--type archived` |
| "recent", "this year", "last month", "since June", a named date | date | `--since 2026-06-01 --until 2026-09-30` or `--date 2026-09-06` |
| "about X", "the rag-eval note", a topic/name fragment | fuzzy title | `--title "rag eval"` (case-insensitive; every word must appear) |
| a module/area ("what touched services/rag") | module column | scan all, then pick rows whose `module` matches |
| any combination of the above | combined | `--type fixed --since 2026-08-01 --title auth` |

**Date semantics:** the note's date is the `yyyy-mm-dd` in its filename when
present (authoritative), else the frontmatter `date`. Relative dates ("last N
months", "this year") must be converted to concrete ISO dates.

## The scanner script

`scripts/scan_notes.py` reads the YAML frontmatter of every Markdown file in
the notes tree and prints a table. It is **stdlib-only Python** (no PyYAML) and
runs on Windows and macOS/Linux.

- **Default root:** `./.agents/notes` under the current directory — the harness
  convention. Run the script from the repo root, or pass `--root <notes-dir>`
  for any other tree.
- **What counts as a note:** a file matching the note filename convention
  (`yyyy-mm-dd-topic.md`), or any file carrying the `type:` frontmatter key.
  Other Markdown files are ignored unless `--all` is given.
- **Filters:** `--type`, `--since` / `--until` / `--date`, and fuzzy `--title`
  (every space-separated word must appear in the filename topic, `topic`, or
  `title`; add `--any-word` to loosen).
- **Output:** a fixed-width table (columns `file date type title tags module`)
  sorted newest first, or `--json` for machine-readable rows. `--no-header`
  prints bare file paths for piping into `xargs`/the Read tool.
- **Robustness:** notes with no date sort last; malformed frontmatter triggers a
  warning but the note is still listed.

The parser handles the normalized v2 schema — scalar keys plus flow/block
lists. Nested mappings such as `sources:` are surfaced as "key present" only;
`commits:` (a list) parses as a list. **The script never reads note bodies.**

Run `python scripts/scan_notes.py --help` for the full flag reference.

## Reading 0, 1, or many notes

| After the scan… | Do |
|---|---|
| No note matches, or the user only wants current-code facts | Answer from the repo alone; state that no note was found. Absence of a note is **not** evidence the work never happened. |
| One note is clearly the one | Read it in full and answer from it. |
| Several notes look relevant | Read them all and synthesize — the user's topic may span an implementation, a later deprecation, a fix, and a rejection that reversed an earlier plan. |
| Hits on *different tracks* | Read each, but answer current-state questions from current-truth notes and history questions from `archived` — do not mix them. |
| A row looks *almost* right (right type/topic, odd date) | Read it — the row is a candidate, the body is the verdict. |

## When a note may not tell the whole story

A note is a **distillation with a point of view** written when the work
concluded. When the retrieval goal is "what is the repo's current state", treat
current-truth notes as authoritative-but-verifiable: check the code when the
stakes warrant it. `archived` notes are deliberately out of sync — never use one
to infer present code. For questions of pure history ("what was decided, why,
in what order"), notes — especially `archived` — are authoritative.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Reading every note body before scanning | Run the scan first — it reads frontmatter only and tells you what to read |
| Grepping note bodies for keywords instead of scanning frontmatter | Body-grep reads everything; the scan table is built from the cheap surface |
| Answering from a frontmatter row alone | A row is a pointer; open the note to answer |
| Answering a current-state question from an `archived` note | `archived` is history, not present — use current-truth types (`implemented`/`deprecated`/`fixed`) for "what is true now" |
| Over-narrowing the scan by guessing the exact topic, then concluding "no note exists" | Scan wide when unsure; filter is a candidate finder, relevance is your read |
| Treating a missing note as proof the work never happened | Absence means no *record*; the work may be in progress or unrecorded — check the repo |
| Trusting a stale note over the code for current-state questions | Current-truth notes should match the code; `archived` never will — verify against the repo |
| Using the old three-type vocabulary (`--type archived` to mean implemented) | v2 splits into five types; `archived` is history, implemented work is `--type implemented` |
| Searching the wrong notes tree | Default is `./.agents/notes`; pass `--root` when the notes live elsewhere |
| Using the wrong skill to write instead of retrieve | Filing concluded work is `writing-project-notes`; this skill only reads |

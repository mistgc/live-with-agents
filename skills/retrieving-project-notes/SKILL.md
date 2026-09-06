---
name: retrieving-project-notes
description: Use when the user asks to search, query, or retrieve project notes, or asks a question that the repo's concluded-work notes may answer — why the repo is in its current state, what was decided or rejected on a topic, what a past feature or defect did. Triggers on phrasing like "what did we decide about X", "find the note on Y", "did we ever reject Z", or "what does the repo say about …". Retrieves by scanning note frontmatter first, then reading only the relevant notes. Complements the writing-project-notes skill
---

# Retrieving Project Notes

## Overview

A **project note** is a durable record of *concluded* work, filed by outcome type. Each note has two retrieval surfaces:

1. A **filename** `yyyy-mm-dd-topic.md` — the date and topic, readable at a glance.
2. A **YAML frontmatter** block — normalized keys (`type`, `date`, `topic`, `title`, `module`, `tags`, `sources`) for structured lookup.

Retrieval is **two-stage**: first a *cheap scan* that reads only frontmatter — never note bodies — to produce a one-line-per-note table; then full reads of only the notes the scan marks as relevant. The scan decides what is worth reading; nothing is read twice.

## When to Use

- The user asks to **find or query a note**: "is there a note on…", "what did we record about…", "show me the notes for this module".
- A question might be **answered by concluded work**: a feature was archived, a defect fixed, a proposal rejected — the note preserves why the repo is the way it is.
- Retrieving **by range**: all notes of a type (`archived` / `fixed` / `rejected`), of a date window, or whose topic/title mentions something.
- Summarizing what the notes say about a goal, a module, or a decision.

**When not to use:** the user wants to *file* concluded work (use `writing-project-notes`); the answer lives plainly in the code and no note is likely to add intent (answer from the repo); the notes live in an Obsidian vault (use the Obsidian note skills); or the user only wants the current code to be searched with no interest in archived context.

## The scan-first rule

**Scan before you read.** Reading the body of every note — or grepping every body for keywords — is the slow path and pollutes context. The scan table is built from frontmatter only, so it stays cheap at any note count. Judge relevance from the *table rows*, not by re-reading.

The scan is deliberately loose: it is a *candidate finder*, not a verdict. A filter may over- or under-match (substring title matches, notes whose topic the filter never sees). That is fine — you decide relevance by reading the rows it returns. **When unsure which range fits, scan wide** (few or no filters) and let the table show you the candidates; the table is cheap, a wrong guess is not.

## Retrieval workflow

1. **State the retrieval goal in one sentence.** Name the topic, the outcome type(s), and the date window you care about. This drives the scan range and, later, relevance.

2. **Scan frontmatter.** Pick the range (below) and run the scanner:

   ```bash
   python scripts/scan_notes.py [--root PATH] [--type TYPE] [--since DATE --until DATE | --date DATE] [--title WORDS]
   ```

   The script prints one row per matching note — file, date, type, title, tags, module — newest first. It never reads a note body.

3. **Select candidates.** From the table, choose which notes are relevant to the goal — **0, 1, or many** (decision table below). Narrow with an extra filter only if the table is unwieldy.

4. **Read the selected notes fully.** Open each with the Read tool (they are small; several may be read in parallel). Read whole files — a frontmatter row is a pointer, not content.

5. **Synthesize against the goal.** Answer the retrieval goal from the note content and cite each note by its path. Distinguish what a note states from what the code shows; if a note looks stale, check the code before trusting it.

## Choosing the scan range

The range is expressed along three dimensions, in the user's own words:

| User says / retrieval goal | Scan dimension | Invocation |
|---|---|---|
| "the notes", "what have we got", no specific ask yet | (none — browse) | no flags; eyeball everything |
| "archived/implemented/done work", "rejected/fixed stuff" | type | `--type archived` · `--type fixed` · `--type rejected` |
| "recent", "this year", "last month", "since June", a named date | date | `--since 2026-06-01 --until 2026-09-30` or `--date 2026-09-06` |
| "about X", "the rag-eval note", a topic/name fragment | fuzzy title | `--title "rag eval"` (case-insensitive; every word must appear) |
| a module/area ("what touched services/rag") | module column | scan all, then pick rows whose `module` matches |
| any combination of the above | combined | `--type fixed --since 2026-08-01 --title auth` |

**Date semantics:** the note's date is the `yyyy-mm-dd` in its filename when present (authoritative), else the frontmatter `date`. Relative dates ("last N months", "this year") must be converted to concrete ISO dates — today is `2026-09-06`.

## The scanner script

`scripts/scan_notes.py` reads the YAML frontmatter of every Markdown file in the notes tree and prints a table. It is **stdlib-only Python** (no PyYAML) and runs on Windows and macOS/Linux.

- **Default root:** `./.agents/notes` under the current directory — the harness convention. Run the script from the repo root, or pass `--root <notes-dir>` for any other tree (a custom location the repo names, an `AGENTS.md`-configured spot, etc.).
- **What counts as a note:** a file matching the note filename convention (`yyyy-mm-dd-topic.md`), or any file carrying the `type:` frontmatter key. Other Markdown files are ignored unless `--all` is given, so stray docs surface instead of vanishing.
- **Filters:** `--type`, `--since` / `--until` / `--date`, and fuzzy `--title` (every space-separated word must appear in the filename topic, `topic`, or `title`; add `--any-word` to loosen to any word).
- **Output:** a fixed-width table (columns `file date type title tags module`) sorted newest first, or `--json` for machine-readable rows (`tags` as an array). `--no-header` prints bare file paths for piping into `xargs`/the Read tool.
- **Robustness:** notes with no date sort last; a note with malformed frontmatter triggers a `warning` on stderr but is still listed with whatever parsed (so a broken key cannot hide a note).

The parser handles the normalized note schema — scalar keys plus flow (`[a, b]`) and block (`- item`) lists. Nested mappings such as `sources:` are surfaced as "key present" only; their leaf paths are not needed for a retrieval scan. **The script never reads note bodies** — that is the whole point of a fast scan.

Run `python scripts/scan_notes.py --help` for the full flag reference.

## Reading 0, 1, or many notes

| After the scan… | Do |
|---|---|
| No note matches, or the user only wants current-code facts | Answer from the repo alone; state that no note was found. Absence of a note is **not** evidence the work never happened — the work may simply be unfinished or unrecorded. Say so, and point to where the repo would show it. |
| One note is clearly the one | Read it in full and answer from it. |
| Several notes look relevant | Read them all and synthesize — the user's topic may span an original design, a later fix, and a rejection that reversed an earlier plan. |
| A row looks *almost* right (right type/topic, odd date) | Read it — the row is a candidate, the body is the verdict. |

## When a note may not tell the whole story

A note is a **distillation with a point of view** written when the work concluded. When the retrieval goal is "what is the repo's current state", treat the note as a pointer and verify against the code when the stakes warrant it — especially when the note's date is old, or when a later note or code change may have superseded its conclusion. For questions of pure history ("what was decided, and why"), the note is authoritative.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Reading every note body before scanning | Run the scan first — it reads frontmatter only and tells you what to read |
| Grepping note bodies for keywords instead of scanning frontmatter | Body-grep reads everything; the scan table is built from the cheap surface and picked by eye |
| Answering from a frontmatter row alone | A row is a pointer; open the note to answer |
| Over-narrowing the scan by guessing the exact topic, then concluding "no note exists" | Scan wide when unsure; filter is a candidate finder, relevance is your read of the table |
| Treating a missing note as proof the work never happened | Absence means no *record*; the work may be in progress or unrecorded — check the repo |
| Trusting a stale note over the code for current-state questions | Notes are frozen at their date; verify against the repo when currency matters |
| Searching the wrong notes tree | Default is `./.agents/notes`; pass `--root` when the repo's notes live elsewhere |
| Using the wrong skill to write instead of retrieve | Filing concluded work is `writing-project-notes`; this skill only reads |

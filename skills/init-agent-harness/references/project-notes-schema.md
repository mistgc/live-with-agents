# Project Notes Schema Specification

- **Status:** ready
- **Version:** `project-notes/v2`
- **Date:** 2026-09-07
- **Governing directory:** `.agents/notes/{implemented,deprecated,fixed,rejected,archived}/`
- **Consumers:** `writing-project-notes`, `retrieving-project-notes`, `scripts/scan_notes.py`, `init-agent-harness`
- **Companion:** [`docs/state-lifecycle.md`](./state-lifecycle.md) — defines the flow that produces these notes

## Purpose and scope

A **project note** is a durable, retrievable record of *concluded* project
knowledge. This document fixes the frontmatter schema and filename every note
must satisfy. "Fixed" here means:

1. **Stable and versioned** — every note carries a schema version; the schema
   evolves only by a documented version bump, never silently.
2. **Machine-checkable** — the constraints in [Conformance](#conformance) map to
   assertions a tool can run over the notes tree.
3. **Single source of truth** — writing and retrieval behavior must not
   contradict this document.

This schema governs a note's **frontmatter and filename**. Body structure
belongs to `writing-project-notes`, with one exception noted under
[Per-type body requirements](#per-type-body-requirements).

The five note types, their two semantic tracks, and the promotion gate that
produces them are defined in `state-lifecycle.md`; this document encodes them
as fields and constraints.

## Canonical schema

```markdown
---
schema: project-notes/v2
type: implemented
date: 2026-09-07
topic: rag-eval
title: RAG evaluation pipeline
module: services/rag
tags: [rag, evaluation]
sources:
  prd: .agents/local/prd/2026-07-20-rag-eval-prd.md
  spec: .agents/local/specs/2026-07-25-rag-eval-spec.md
commits:
  - a1b2c3d add rag evaluation harness
  - 9f8e7d6 wire evaluation into CI
---
```

### Field table

| Key | Required | Type | Constraints |
|---|---|---|---|
| `schema` | yes | string | Exactly `project-notes/v2`. |
| `type` | yes | enum | One of `implemented` \| `deprecated` \| `fixed` \| `rejected` \| `archived`. **Must equal the subfolder name** the note is filed under. |
| `date` | yes | date | ISO `YYYY-MM-DD`, the date the note was written. **Must equal the filename date prefix.** |
| `topic` | yes | slug | `[a-z0-9]+(-[a-z0-9]+)*`. **Must equal the filename suffix.** |
| `title` | yes | string | Human-readable one-liner, single line. Free case/punctuation — for reading, not matching. |
| `module` | optional | string | Repo-relative path of the code area touched (no leading `./`). Omit when no single area applies. |
| `tags` | optional | list | Flow `[a, b]` or block list of lowercase `[a-z0-9-]` identifiers. Omit when empty. |
| `sources` | optional | mapping | Allowed keys: `prd`, `quality_contract`, `spec`. Values are repo-relative paths. **Omit a key whose document does not exist** — absence records the absence; never fabricate a path. |
| `commits` | conditional | list | The change set: **one line per relevant commit**, each `"<hash> <subject>"`. Hash is 7–40 hex chars. **Required** for `implemented`, `deprecated`, `fixed`; absent for `rejected` (no code to cite); optional for `archived`. See [Change set](#change-set). |
| `updated` | optional | date | ISO `YYYY-MM-DD`. Last time this note was **maintained** to stay in step with the code — applies to current-truth notes only (`implemented`, `deprecated`, `fixed`). Omit when never revised. |

Unknown top-level keys are not part of v2, but they do **not** make a note
structurally non-conformant: readers must tolerate and ignore them, and a
conformance checker reports them as a lint warning — a signal to run the
[versioning policy](#versioning-and-migration), not a failure. There is no
free-form escape hatch: if a note needs more, that is a schema version
question, not a one-off field.

### Semantics per track

`type` carries two axes at once — *which track* the note belongs to, and *what
concluded*. The track determines whether the note is maintained:

| Track | Types | Maintained in step with code? |
|---|---|---|
| current-truth | `implemented`, `deprecated`, `fixed` | **yes** — updated in place, one note per live feature |
| history | `archived` | **no** — a frozen snapshot, never revised to match the code |
| terminal | `rejected` | no — decided once, then static |

| `type` | Meaning |
|---|---|
| `implemented` | The feature is live in the code right now. |
| `deprecated` | Was implemented, since removed or superseded. The removal commit is in the change set. |
| `fixed` | A reported defect is repaired in the code. |
| `rejected` | A proposal was explicitly declined. No code exists for it. |
| `archived` | A step in how the repo reached its current shape — for AGENT recall only, not a statement about present code. |

A current-truth note is the **present-tense snapshot** of one thing in the code;
when the code evolves, the note is updated in place (`updated:` is set) rather
than forked into a new file. Its evolution history is carried by `commits`, not
by one file per version.

## Change set

`commits` records **every commit relevant to this note's conclusion, one line
per change** — not merely the newest commit:

```yaml
commits:
  - a1b2c3d add rag evaluation harness
  - 9f8e7d6 wire evaluation into CI
  - 3c4d5e6 remove legacy scorer   # for a deprecated note: the removal commit
```

- Format per line: `<hash> <subject>`; hash 7–40 hex characters, then one space,
  then the commit subject.
- Required for `implemented`, `deprecated`, `fixed`: these conclude a change that
  exists in the repository, so the change must be committed. Uncommitted work has
  not passed the promotion gate — commit first, then file the note.
- `rejected` has no code change to cite, so `commits` is absent. (A decline that
  *did* land a revert commit may record it, but that is the exception.)
- `archived` may cite the commits that constitute the step it records; optional.

**Never fabricate a hash.** A note whose change set cannot be determined is
filed with `commits` absent and flagged for backfill, not invented.

## Filename convention

```
<date>-<topic>.md      e.g. 2026-09-07-rag-eval.md
```

- `date` equals frontmatter `date`; `topic` equals frontmatter `topic`.
- The filename date is authoritative for ordering; frontmatter `date` is the
  fallback for files that do not follow the convention (tolerated by readers,
  but not a conformant note).
- Never silently overwrite an existing note for the same topic: write a new dated
  note, or supersede explicitly only when the new note clearly replaces the old
  and the user wants the history replaced.

## Per-type body requirements

Body structure is the writing skill's concern, with one exception the schema
depends on: **`rejected` notes must be self-sufficient.** There is no code to
fall back on, so the note must carry the proposal and the decisive reason in its
own body, and the full proposal document is promoted out of the untracked
`.agents/local/` alongside it. `implemented`/`deprecated`/`fixed` notes are
distillations that may point back at their source docs, since the code itself is
the full record of *what* happened.

## Conformance

A note conforms to `project-notes/v2` iff every check below passes.

| # | Check |
|---|---|
| C1 | Path is `notes-root/<type>/<date>-<topic>.md` — three fixed segments. |
| C2 | Frontmatter parses as YAML. |
| C3 | Required keys present: `schema`, `type`, `date`, `topic`, `title`. |
| C4 | `type` ∈ {`implemented`, `deprecated`, `fixed`, `rejected`, `archived`} **and** equals the immediate subfolder name. |
| C5 | `date` matches `^\d{4}-\d{2}-\d{2}$` and equals the filename date prefix. |
| C6 | `topic` matches `^[a-z0-9]+(-[a-z0-9]+)*$` and equals the filename suffix. |
| C7 | `title` is a single line. |
| C8 | `tags` is a list of `[a-z0-9-]` identifiers, or absent. |
| C9 | Every present `sources` key ∈ {`prd`, `quality_contract`, `spec`} and its value is a path that exists on disk. |
| C10 | No top-level keys outside the schema (**warn** — tolerated, not fatal). |
| C11 | `schema` is exactly `project-notes/v2`. |
| C12 | `commits`, when present, is a list of lines matching `^[0-9a-f]{7,40} .+$`; it is **present** for `implemented`/`deprecated`/`fixed`. |
| C13 | `updated`, when present, matches `^\d{4}-\d{2}-\d{2}$` and the note's `type` is a current-truth type. |

C4 is load-bearing: a note whose `type` disagrees with its folder is mis-filed
and must be **moved**, never edited in place to fake conformance.

## Versioning

The schema version is `project-notes/<n>`. Current: **v2**.

- **Additive change** (a new optional key; a value old readers ignore): may keep
  the version when it cannot mislead an older reader. Bump if in doubt.
- **Breaking change** (rename, removal, or repurposing of a key; a new/changed
  `type` vocabulary; a tightened constraint existing notes could violate): new
  version, shipped with an explicit migration note, and this document updated
  **before** writers emit the new version.
- **Invariant across versions:** the folder layout, `type`↔folder equality
  (C4), and the filename convention are permanent. Retrieval must keep working
  across versions without reading bodies.
- Old notes never need rewriting to stay *readable*: readers tolerate missing and
  unknown keys. Migration is about *conformance*, not readability.

## Migration: v1 → v2 (one-time)

v1 used a three-type vocabulary (`archived` / `fixed` / `rejected`) in which
`archived` meant "implemented". v2 replaces it with five types, redefines
`archived` as the history track, and adds the change set. This is breaking.

> **This repository currently has no notes** — only the note-writing scaffolding — so
> the migration below applies to repositories that already adopted v1, and to
> notes written before this document existed.

Steps, in order:

1. **Retype and move v1 `archived` notes** → `implemented/`, setting
   `type: implemented`. Their content means "this was implemented"; under v2
   that is `implemented`, not `archived`. `archived/` starts empty as the
   history track.
   *(Alternative, if a repo wants its old `archived` notes treated as history
   rather than as live features: leave them in place and set only `schema:
   project-notes/v2`. Pick one and apply it uniformly — do not decide per note.)*
2. **Keep `fixed` and `rejected`** in place; only add `schema`.
3. **Set `schema: project-notes/v2`** on every migrated note.
4. **Backfill `commits`** for current-truth notes from `git log` (match by
   `module`, `topic`, and the entry points named in the body). Where the change
   set cannot be determined, leave `commits` absent and record the note in a
   migration report for backfill — **never fabricate a hash**.
5. **Re-verify C4–C6** (type↔folder, filename↔date/topic) after every move; a
   move that desynchronizes filename and frontmatter is a broken migration.
6. **Scaffold the new directories** — add `implemented/` and `deprecated/` (with
   `.gitkeep`) to the notes tree; they do not exist under v1.

After migration, run the conformance checks over the tree; remaining failures
should be only missing `commits` backfills.

## Out of scope for v2 (future extension candidates)

Each would be a *versioned* addition, not a one-off field:

- **`supersedes` / note-to-note relations** — only needed if the "one
  current-truth note per live feature, updated in place" assumption is ever
  replaced by appending a new note per evolution.
- **Author / agent attribution** — who concluded the work.
- **Verification status** — whether a current-truth note's conclusion has been
  re-checked against the code recently.
- **Non-outcome project knowledge** — durable facts, conventions, and decisions
  that are not records of a single concluded item. A different note family with
  its own version (e.g. `project-knowledge/v1`), not an extension of
  `project-notes`.

## Consumers of this spec

| Consumer | Obligation |
|---|---|
| `writing-project-notes` skill | Emit only conformant v2 notes; file by `type`; distill source docs; record the change set; omit absent sources; make `rejected` notes self-sufficient. |
| `retrieving-project-notes` skill + `scan_notes.py` | Read the frontmatter fields; treat C4 as the folder↔type invariant; filter on the five-type vocabulary; tolerate unknown keys. |
| `init-agent-harness` | Scaffold all five directories and reference this schema as the notes contract. |

Changes to the skills or scanner that alter note structure are changes to this
schema and must go through the versioning policy above.

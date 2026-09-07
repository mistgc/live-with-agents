---
name: writing-project-notes
description: Use when a requirement or proposal has concluded and the repo should keep a retrievable record of it — after a feature is implemented in the code (implemented), after a feature is removed or superseded (deprecated), after a reported defect is fixed (fixed), after a proposed design or implementation was explicitly declined (rejected), or when a step in how the repo reached its current shape should be snapshotted for AGENT recall (archived). Triggers when asked to write/archive/save a project note or record this feature/bug/rejection/history, or at the end of an implement / fix / deprecate / decide cycle. Collects the surrounding context, locates the requirement's PRD, quality contract, and SPEC documents, distills them into the note body, records the change set of relevant commits, and writes one Markdown note with YAML frontmatter into the repo's notes directory.
---

# Writing Project Notes

## Overview

A **project note** is a durable, retrievable record of *concluded* project
knowledge. Once a requirement's documents have been implemented in the code (or
a defect fixed, a proposal declined, a feature removed, a step worth keeping
happened), the working conversation would otherwise evaporate — later sessions
would re-derive the intent from scratch. A note distills what happened so a
future agent can reconstruct *why the repo is the way it is* without replaying
the history.

Notes live under `.agents/notes/`, split into **five types on two semantic
tracks** (see `docs/state-lifecycle.md`):

| `type` | Directory | Track | Meaning | Syncs with code? |
|---|---|---|---|---|
| `implemented` | `notes/implemented/` | current-truth | The feature is live in the code right now | yes |
| `deprecated` | `notes/deprecated/` | current-truth | Was implemented, since removed / superseded | yes |
| `fixed` | `notes/fixed/` | current-truth | A reported defect is repaired | yes |
| `rejected` | `notes/rejected/` | terminal | A proposal was explicitly declined | no |
| `archived` | `notes/archived/` | history | A step in how the repo got here — AGENT recall only | no |

The **track decides whether a note is maintained**: current-truth notes are kept
in step with the code, history/terminal notes are frozen. This distinction
governs when each type is written and whether a note is later updated.

Each note has two retrieval surfaces:

1. A **filename** `yyyy-mm-dd-topic.md` — chronological and keyword-searchable.
2. A **YAML frontmatter** block with normalized keys (`schema`, `type`, `date`,
   `topic`, `title`, `module`, `tags`, `sources`, `commits`, `updated`) for
   structured lookup.

The note body is a **distillation, not a copy**: it summarizes the PRD /
quality-contract / SPEC documents and the actual code outcome, and points at
its sources. It never replaces the source documents. **The schema version is
`project-notes/v2`** — every note carries `schema: project-notes/v2`, and the
frontmatter must conform to `docs/project-notes-schema.md`.

## Note types (auto-classified)

The type is **not supplied by the user** — it is determined by comparing the
collected context with the current state of the code:

| Type | Conclusion condition | Written when |
|---|---|---|
| `implemented` | The requirement (per its PRD / contract / SPEC) is now in the code, **and still is**. | Feature built and live. |
| `deprecated` | The code no longer contains the feature that an `implemented` note (or old `archived` note) described. | Feature removed / superseded — record the removal commit. |
| `fixed` | A reported defect is repaired in the code. | Bug verified fixed. |
| `rejected` | A proposed design or implementation was explicitly declined. | Explicit "no" — never absence of implementation. |
| `archived` | A step worth remembering happened — implemented / deprecated / fixed / rejected, **or a pure history milestone**. | Any conclusion, or a notable turning point. |

`implemented`/`deprecated`/`fixed` are written only when the outcome is
**visible in the code** — never from a claim alone. `rejected` requires
explicit evidence of the decline (a user decision, a closed/rejected PR, a
revert). `archived` snapshots how the repo reached its current shape — it is
**not** kept in sync with the code afterwards, and is **not** to be used to
infer the current state of the code (that is what the current-truth types are
for).

If the conclusion of the work sits in a prior session, reconstruct the class
from the repo: `git log` for the landing commit, the presence/absence of the
modules named in the docs, and any notes already filed.

## When to Use

- A feature that went through PRD / quality-contract / SPEC documents has just
  been **implemented** — file it under `implemented` before the detail fades.
- A feature was **removed or superseded** in the code — file the removal under
  `deprecated`, recording the removal commit.
- A **bug was fixed** — file the defect + root cause + fix under `fixed`.
- A design or implementation was **explicitly declined** — file the proposal +
  reason under `rejected`.
- A milestone worth remembering happened, or the user asks to snapshot history —
  file under `archived`.
- The user explicitly asks to write / archive / save a project note for a
  context, requirement, or feature — with or without naming the type.

**When not to use:** the work is still in progress (nothing has concluded —
wait); the feature was implemented with no surrounding documents or
conversation worth preserving (nothing to distill — a note would duplicate the
code); the user only wants a summary *now* with no intent to store it; or the
deliverable is a new PRD/SPEC/quality contract (write that instead — this skill
records, it does not author requirements).

## Where the notes live

A note's class determines its folder:

```
<repo>/.agents/notes/
├── implemented/   # feature live in the code
├── deprecated/    # feature removed / superseded
├── fixed/         # resolved defects
├── rejected/      # declined proposals
└── archived/      # history: how the repo got here (AGENT recall)
```

- **Repo runs the `.agents/notes/` convention** (set up by
  `init-agent-harness`) → file into the matching subfolder.
- **An AGENTS.md or the user names a different notes location** → file there,
  keeping the five-subfolder split (or the user's existing split).
- **No convention exists** → default to `.agents/notes/…` and create it,
  mirroring the harness. If creating directories would surprise the user (e.g.
  they want notes only in `docs/`), ask before writing.

**Naming:** `yyyy-mm-dd-topic.md`, where the date is the ISO date the note is
written and `topic` is a short dash-joined slug of the requirement (e.g.
`2026-09-07-rag-eval.md`). Never overwrite an existing note silently: if a note
for the same topic already exists, write a new dated one rather than clobbering
history, unless the new note clearly supersedes the old one and the user wants
it replaced.

## Steps

1. **Collect context.** Gather what makes the requirement identifiable: the goal
   and scope, whether it was a feature, a defect, or a proposal, the
   module/entry points it touched, any decisions and their reasons, and
   how/when it concluded. If invoked retroactively with no live conversation,
   mine `git log` and recent notes for the feature's commits and build the
   context from them.

2. **Locate the requirement's documents.** Find the documents that correspond to
   this context — every one may be absent, and that is fine:
   - **PRD** — what the requirement wanted and why.
   - **Quality contract** — the module's preconditions / postconditions /
     invariants (produced by the `writing-quality-contract` skill).
   - **SPEC** — how it was to be built.
   Search likely homes: `.agents/local/` (`prd/`, `specs/`, plus wherever
   contracts were stored), `docs/`, the repo's `notes/` folders, and any paths
   already named in the conversation. Match by topic slug, date window, and by
   module/function names appearing both in the docs and the context. **Do not
   invent a document** — if a PRD, contract, or SPEC cannot be found, state its
   absence in the note's `sources` rather than fabricating one.

3. **Collect the change set.** Run `git log` over the module/paths the work
   touched and identify **every commit relevant to this conclusion — one per
   line**, not just the newest:
   - `implemented` — the commit(s) that built the feature.
   - `deprecated` — the commit(s) that removed / superseded it.
   - `fixed` — the commit(s) that repaired the defect.
   - `archived` — the commit(s) that constitute the milestone (optional).
   Format each as `<hash> <subject>` (hash 7–40 hex, then the subject). **Never
   fabricate a hash** — if the change set cannot be determined, leave `commits`
   absent and say so.

4. **Classify against the code.** Decide the type (decision table above).
   Verify the outcome in the repo: grep for the named entry points/modules;
   confirm the feature still exists (`implemented`) or no longer exists
   (`deprecated`); confirm the fix exists (`git log -S` or `git log -- <path>`);
   confirm the decline. Reconcile any mismatch — if the docs describe a feature
   the code does not have, it is **deprecated** (removed) or **not concluded**
   (never built) — say so instead of forcing a classification.

5. **Check for an existing note.** Skim `.agents/notes/` filenames for the same
   topic. A current-truth feature keeps **one** `implemented` note; if the code
   evolved, update that note in place rather than forking it. If a feature moved
   to `deprecated`, the old `implemented` note may be left as-is (history) or
   marked — prefer writing the new `deprecated` note and, if the feature is now
   gone, not keeping a live `implemented` claim for it.

6. **Distill into the note body.** Combine the PRD, quality contract, and SPEC
   with the actual code outcome into the template below. Keep it a summary; the
   source documents stay authoritative. **`rejected` notes must be
   self-sufficient** — with no code to fall back on, record the proposal and the
   decisive reason in the body, and promote the full proposal document out of
   `.agents/local/` alongside the note.

7. **Write and verify.** Save to `<folder>/<date>-<topic>.md`. Re-read it:
   frontmatter `type` equals the subfolder, every required key is present,
   `sources` paths point at files that exist (or are marked absent), `commits`
   lines are real `<hash> <subject>` entries, and the body names the
   module/entry points a future agent would grep for.

## Note schema

The canonical schema is `docs/project-notes-schema.md`. Frontmatter keys in
brief:

```yaml
---
schema: project-notes/v2
type: implemented          # implemented|deprecated|fixed|rejected|archived — must equal the subfolder
date: 2026-09-07            # ISO date written; equals the filename date
topic: rag-eval            # slug that names the filename
title: RAG evaluation pipeline   # human-readable one-liner
module: services/rag       # code area touched (repo-relative)
tags: [rag, evaluation]    # search keywords
sources:                   # the requirement documents this note distills
  prd: .agents/local/prd/2026-07-20-rag-eval-prd.md
  spec: .agents/local/specs/2026-07-25-rag-eval-spec.md
commits:                   # change set: one line per relevant commit
  - a1b2c3d add rag evaluation harness
  - 9f8e7d6 wire evaluation into CI
updated: 2026-09-07         # optional; last maintenance for current-truth notes
---
```

- `type` must equal the subfolder it is filed into.
- `date` = filename date; `topic` = filename suffix.
- `commits` is **required for `implemented`/`deprecated`/`fixed`**; absent for
  `rejected` (no code to cite); optional for `archived`.
- `updated` is for current-truth notes maintained in place after creation.
- Unknown keys are tolerated by readers but not part of v2.

## Template

```markdown
---
<frontmatter per the schema above>
---

# <Title> — <Implemented | Deprecated | Fixed | Rejected | Archived>

## Outcome
One or two lines: what the repo now reflects, and why this note is classified
as it is. For `deprecated`, name the removal. For `rejected`, state the
proposal and the decisive reason.

## Context
The requirement in a few lines — what was wanted and by whom, what problem it
solved. Link any source documents that survive.

## Source documents
| Document | Where it lives | Role in this work |
|---|---|---|
| PRD | <path or "none"> | <what it specified> |
| Quality contract | <path or "none"> | <preconditions / postconditions / invariants> |
| SPEC | <path or "none"> | <how it was to be built> |

## What actually happened
How the code, fix, removal, or decision differs from — or matches — the
documents. For `implemented`/`deprecated`/`fixed`, name the module and entry
points and the change set commits.

## Worth remembering
The non-obvious bits a future session would otherwise re-derive: design
deviations from the SPEC, contract clauses that surprised implementers, root
cause of the defect, why the rejected option was refused. Reference code by
`file:line` or function name.
```

Keep `## Worth remembering` genuinely selective — the note's recall value is
the deviation and the *why*, not a re-statement of what the code already shows.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing a note while the work is still in progress | Only file when the outcome is visible in the code (`implemented`/`deprecated`/`fixed`), or on explicit decline (`rejected`), or a real milestone (`archived`) |
| Letting the user or a prompt pick the type | The type is **auto-classified** by comparing context with the code (decision table above) |
| Using `archived` to mean "implemented" | Under v2, `archived` is the history track — implemented work goes in `implemented/` |
| Confusing current-truth vs history types | `implemented`/`deprecated`/`fixed` describe present code and must sync; `archived` is a frozen snapshot, never used to infer current state |
| Classifying from a claim without checking the code | Grep for the named modules/entry points, check `git log` — reconcile mismatches before writing |
| Recording only the newest commit | `commits` is a change set — every relevant commit, one per line |
| Fabricating a hash | Never invent a commit; leave `commits` absent and flag for backfill |
| Copying the PRD/SPEC into the note | Distill — the note is a pointer + summary, the source docs stay authoritative |
| Fabricating a missing PRD/contract/SPEC | State absence in `sources`; never invent a document |
| Writing a `rejected` note that is not self-sufficient | No code backs a rejection — record proposal + decisive reason, promote the full proposal doc |
| `type` and destination folder disagreeing | Frontmatter `type` must equal the subfolder it's filed into |
| Filename with no date, or topic that doesn't match the frontmatter | `yyyy-mm-dd-topic.md` with `topic` matching the frontmatter `topic` |
| Silently overwriting an older note for the same topic | Write a new dated note (supersede explicitly if needed), don't clobber history |
| Forking a current-truth note on every code change | Keep one `implemented` note per live feature, update in place, set `updated:` |
| Inconsistent YAML keys across notes | Every note uses the v2 schema — identical keys make cross-note retrieval reliable |

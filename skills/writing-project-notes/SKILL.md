---
name: writing-project-notes
description: Use when a requirement or proposal has concluded and the repo should keep a queryable record of it — after a feature described by PRD, quality-contract, and SPEC documents is implemented in the code (archived), after a reported defect is fixed in the code (fixed), or after a proposed design or implementation was explicitly declined (rejected). Triggers when asked to write/archive/save a project note or record this feature/bug/rejection, or at the end of an implement / fix / decide cycle. Collects the surrounding context, locates the requirement's PRD, quality contract, and SPEC documents, classifies the outcome against the current code, and writes one Markdown note with YAML frontmatter into the repo's notes directory.
---

# Writing Project Notes

## Overview

A **project note** is a durable, queryable record of *concluded* work. Once a requirement's documents have been implemented in the code (or a defect fixed, or a design declined), the working conversation would otherwise evaporate — later sessions would have to re-derive the intent from scratch. A note distills what happened so a future agent can reconstruct *why the repo is the way it is* without replaying the history.

Each note has **two query surfaces**:

1. A **filename** `yyyy-mm-dd-topic.md` — chronological and keyword-searchable, so an agent can scan a directory listing and pick a note by topic alone.
2. A **YAML frontmatter** block with normalized keys (`type`, `topic`, `module`, `tags`, `sources`) — so an agent can grep or structure-query across many notes (e.g. all `type: rejected` decisions) fast.

The note itself is a **distillation, not a copy** — it summarizes the PRD / quality-contract / SPEC documents and the actual code outcome, and highlights the decisions worth remembering. It never replaces the source documents; it points at them.

## Note types (auto-classified)

Every note is classified into exactly one of three outcome types. **The type is not supplied by the user — it is determined by comparing the collected context with the current state of the code:**

| Type | Meaning | Conclusion condition |
|---|---|---|
| `archived` | The requirement (as captured in its PRD / quality contract / SPEC) is now **implemented in the code**. The repo has the feature; the note preserves the intent behind it. | Docs exist for a feature/requirement AND the code contains the described implementation. |
| `fixed` | A **reported defect** is now **repaired in the code**. | Context concerns a bug/defect AND the code contains the fix (the faulty behavior is gone). |
| `rejected` | A proposed **design or implementation was explicitly declined**. The note records the proposal and the decisive reason it was refused, so it is not re-proposed later. | The conversation or docs record an explicit "no" (never built, or built and rolled back). |

`archived` and `fixed` are written only when the outcome is **visible in the code** — never from a claim alone. If the feature is only designed/reviewed but not yet implemented, or the bug is only reported but not yet fixed, the work is **not concluded**: do not write an `archived`/`fixed` note yet. `rejected` requires explicit evidence of the decline (a user decision, a closed issue/PR, a revert) — not just the absence of implementation.

If the conclusion of the work sits in a prior session, reconstruct the class from the repo: `git log` for the landing commit, the presence of the module/functions named in the docs, and any notes already filed.

## When to Use

- A feature that went through PRD / quality-contract / SPEC documents has just been **implemented** — file the intent under `archived` before the conversation detail fades.
- A **bug was fixed** — file the defect + root cause + fix under `fixed`.
- A design or implementation was **explicitly declined** — file the proposal + reason under `rejected`.
- The user explicitly asks to write / archive / save a project note for a context, requirement, or feature — with or without naming the type.

**When not to use:** the work is still in progress (nothing has concluded — wait); the feature was implemented with no surrounding documents or conversation worth preserving (nothing to distill — a note would duplicate the code); the user only wants a summary *now* with no intent to store it; or the deliverable is a new PRD/SPEC/quality contract (write that instead — this skill records, it does not author requirements).

## Where the notes live

A note's class determines its folder. Follow the repo's **agent-document harness** when one is present:

```
<repo>/.agents/notes/
├── archived/     # implemented / user-reviewed work
├── fixed/        # resolved defects
└── rejected/     # declined proposals
```

- **Repo runs the `.agents/notes/` convention** (set up by the init-agent-harness / `templates/project-structure-with-agents`) → file the note into the matching subfolder.
- **An AGENTS.md or the user names a different notes location** → file there, keeping the `archived/`/`fixed/`/`rejected/` subfolder split (or the user's existing split).
- **No convention exists** → default to `.agents/notes/…` and create it, mirroring the harness. If creating directories would surprise the user (e.g. they want notes only in `docs/`), ask before writing.

**Naming:** `yyyy-mm-dd-topic.md`, where the date is the ISO date the note is written and `topic` is a short dash-joined slug of the requirement (e.g. `2026-09-06-rag-eval.md`). Never overwrite an existing note silently: if a note for the same topic already exists, write a new dated one rather than clobbering history, unless the new note clearly supersedes the old one and the user wants it replaced.

## Steps

1. **Collect context.** Gather what makes the requirement identifiable: the goal and scope, whether it was a feature, a defect, or a proposal, the module/entry points it touched, any decisions and their reasons, and how/when it concluded. If invoked retroactively with no live conversation, mine `git log` and recent notes for the feature's commits and build the context from them.

2. **Locate the requirement's documents.** Find the documents that correspond to this context — every one may be absent, and that is fine:
   - **PRD** — what the requirement wanted and why.
   - **Quality contract** — the module's preconditions / postconditions / invariants (produced by the `create-quality-contract` skill).
   - **SPEC** — how it was to be built.
   Search likely homes: `.agents/local/` (`prd/`, `specs/`, plus wherever contracts were stored), `docs/`, the repo's `notes/` folders, and any paths already named in the conversation. Match by topic slug, date window, and by module/function names appearing both in the docs and the context. **Do not invent a document** — if a PRD, contract, or SPEC cannot be found, state its absence in the note's `sources` rather than fabricating one.

3. **Classify against the code.** Decide `archived` / `fixed` / `rejected` (decision table above). Verify the outcome in the repo: grep for the named entry points/modules, confirm the fix exists (`git log -S` or `git log -- <path>`), confirm the decline (commit that removed it, a closed/rejected PR or issue, or an explicit user decision in the conversation). Reconcile any mismatch — if the docs describe a feature the code does not have, the requirement is **not** concluded; say so instead of forcing a classification.

4. **Check for an existing note.** Skim `.agents/notes/` filenames for the same topic. If one exists with a *different* class (e.g. previously `rejected`, now actually built), the new note supersedes it — write the new one; optionally note the flip in the body.

5. **Distill into the note body.** Combine the PRD, quality contract, and SPEC with the actual code outcome into the template below. Keep it a summary: the source documents stay authoritative for full detail. Frontmatter `type` **must equal** the subfolder it is filed into.

6. **Write and verify.** Save to `<folder>/<date>-<topic>.md`. Re-read it: filename and `type` match the folder, every key in the schema below is present, `sources` paths point at files that exist (or are marked absent), the body names the module/entry points a future agent would grep for, and the classification matches the code.

## Note schema

Every note is Markdown whose first line is a YAML frontmatter block. The keys are **normalized and mandatory** so agents can rely on them for queries — omit `sources` keys whose documents don't exist.

```yaml
---
type: archived             # archived | fixed | rejected — must equal the subfolder
date: 2026-09-06           # ISO date the note was written (equals the filename date)
topic: rag-eval            # slug that names the filename — short, dash-joined
title: RAG evaluation pipeline   # human-readable one-liner
module: services/rag       # code area the work touched
tags: [rag, evaluation]    # search keywords
sources:                   # the requirement documents this note concludes
  prd: .agents/local/prd/2026-07-20-rag-eval-prd.md
  quality_contract: .agents/local/specs/2026-07-22-rag-eval-contract.md
  spec: .agents/local/specs/2026-07-25-rag-eval-spec.md
outcome: implemented       # implemented | fixed | declined — one-word confirmation
---
```

`type` drives the folder, `date` drives sort order, and `topic` + `title` + `tags` + `module` drive keyword lookup. Agents query notes by scanning filenames, or by grepping frontmatter (`type: rejected`, `module: services/rag`, a tag, a source path).

## Template

```markdown
---
<frontmatter per the schema above>
---

# <Title> — <Archived | Fixed | Rejected>

## Outcome
One or two lines: what the repo now reflects, and why this note is classified as it is.

## Context
The requirement in a few lines — what was wanted and by whom, what problem it solved.
Link any source documents that survive.

## Source documents
| Document | Where it lives | Role in this work |
|---|---|---|
| PRD | <path or "none"> | <what it specified> |
| Quality contract | <path or "none"> | <preconditions / postconditions / invariants it pinned down> |
| SPEC | <path or "none"> | <how it was to be built> |

## What actually happened
How the code, fix, or decision differs from — or matches — the documents. For `archived`/`fixed`,
name the module and entry points that now exist. For `rejected`, state the proposal and the
decisive reason it was declined.

## Worth remembering
The non-obvious bits a future session would otherwise re-derive: design deviations from the
SPEC, contract clauses that surprised implementers, root cause of the defect, why the rejected
option was refused. Reference code by `file:line` or function name.
```

Keep `## Worth remembering` genuinely selective — the note's recall value is the deviation and the *why*, not a re-statement of what the code already shows.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing a note while the work is still in progress | Only file `archived`/`fixed` when the outcome is visible in the code; `rejected` only on explicit decline |
| Letting the user or a prompt pick the type | The type is **auto-classified** by comparing context with the code (decision table above) |
| Classifying `archived` from a claim without checking the code | Grep for the named modules/entry points, check `git log` — reconcile mismatches before writing |
| Marking something `rejected` merely because it wasn't implemented | `rejected` requires explicit evidence the proposal was declined |
| Copying the PRD/SPEC into the note | Distill — the note is a pointer + summary, the source docs stay authoritative |
| Fabricating a missing PRD/contract/SPEC | State absence in `sources`; never invent a document |
| `type` and destination folder disagreeing | Frontmatter `type` must equal the `archived`/`fixed`/`rejected` subfolder it's filed into |
| Filename with no date, or topic that doesn't match the frontmatter | `yyyy-mm-dd-topic.md` with `topic` matching the frontmatter `topic` |
| Silently overwriting an older note for the same topic | Write a new dated note (supersede explicitly if needed), don't clobber history |
| Inconsistent YAML keys across notes | Every note uses the normalized schema — identical keys make cross-note queries reliable |

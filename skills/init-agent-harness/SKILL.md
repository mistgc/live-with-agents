---
name: init-agent-harness
description: MANUAL-ONLY skill. Do not auto-invoke. Use ONLY when the user directly asks to run this skill — e.g. to set up or refresh a project's AGENTS.md with output-constraint rules, adding a .agents harness so agents store generated docs (plan/spec/prd/reports) under git-ignored .agents/local, file concluded work as typed notes (implemented/deprecated/fixed/rejected/archived) under .agents/notes, and consult those notes when answering repo questions. It also writes a README under .agents/notes explaining that folder and pointing at the two governing reference docs (state-lifecycle.md, project-notes-schema.md) by relative path into the skill's bundled references directory, and the AGENTS.md rules it writes tell future agents to read that README when filing or consulting notes.
disable-auto-invoke: true
---

# Init Agent Harness

## Overview

A repo's AGENTS.md should tell future agents three things about documents:

1. **Store** every document the agent generates (plan/spec/prd/reports) under the git-ignored `.agents/local/` — keep working docs out of git history unless the user explicitly asks to track one.
2. **File** concluded work as typed notes under `.agents/notes/`, one directory per type — `implemented/` for features live in the code, `deprecated/` for removed/superseded features, `fixed/` for resolved defects, `rejected/` for declined proposals, `archived/` for history snapshots — so later sessions can reconstruct intent without re-deriving it.
3. **Consult** those notes when asked to search the repo or explain its usage, combining the relevant note with the repo — and answering from the repo alone when no note applies.

This skill encodes those three rules into a project's `AGENTS.md` and makes sure the `.agents/` harness and gitignore support them.

Rules 2 and 3 rest on two authoritative reference documents, which this skill bundles under its own `references/` directory:

- `references/state-lifecycle.md` — where notes come from: the promotion gate, the five types on their two tracks (current-truth / history / terminal).
- `references/project-notes-schema.md` — the note schema (`project-notes/v2`): frontmatter fields, the filename rule, conformance checks.

Rather than copy them into the project's `docs/`, the skill writes a short `.agents/notes/README.md` that orients a reader who lands in the notes folder and links both docs by relative path into that `references/` directory (through the skill's install location, `.agents/skills/init-agent-harness/`). The AGENTS.md section written by this skill points at that README, so the AGENT reaches the docs whenever it files, retrieves, or classifies a note.

## When to Use

**Manual-only — never auto-invoke.** This skill changes a project's governing agent rules, so it runs only when the user explicitly asks. Do not trigger it unprompted during other work, and do not chain it from other skills.

- The user directly asks to run this skill, or to "add output-constraint rules" to a project's AGENTS.md.
- The user asks to bootstrap the agent-document workflow / `.agents/` harness in a repo.

When **not** to use: the user wants planning docs deliberately tracked in git; the project already encodes these exact rules; or the task merely resembles this one (e.g. writing an AGENTS.md) without the user asking for the output-constraint setup.

## Steps

1. **Locate the target file.** The harness lives in the repo root: `AGENTS.md` alongside `.agents/`. If `AGENTS.md` doesn't exist, create it. If it exists, read it first and merge rather than overwrite unrelated content.

2. **Ensure the `.agents/` scaffold exists.** Create only what's missing — never duplicate or destroy existing content:
   ```
   .agents/
   ├── local/          # git-ignored working docs
   │   ├── plans/
   │   ├── prd/
   │   ├── specs/
   │   └── reports/
   ├── notes/          # concluded work, typed and split into five directories
   │   ├── README.md    # orients a reader in this folder (written in Step 3)
   │   ├── implemented/ # features live in the code (syncs with code)
   │   ├── deprecated/  # removed / superseded features (syncs with code)
   │   ├── fixed/      # resolved defects (syncs with code)
   │   ├── rejected/   # declined proposals
   │   └── archived/   # history: how the repo got here (AGENT recall only)
   ├── rules/
   └── skills/
   ```
   This is the reference shape. When a repo already runs a different variant of this harness, adapt to the existing folders (e.g. existing `notes/` subfolders, extra `local/` categories) rather than copying the reference verbatim. Keep empty folders present with a `.gitkeep` per level.

3. **Write the notes README.** Rules 2 and 3 rest on two authoritative documents, which this skill bundles under its own `references/` directory. In this revision **no copy is placed in the project's `docs/`** — the docs are reached through the README written here, so do not create or overwrite anything under `docs/`. Write a short `README.md` into the repo's `.agents/notes/`, so anyone who lands in the notes folder is oriented and can reach them. It explains what `.agents/notes` is and links both bundled docs by **relative path into the skill's install location** — installed, this skill sits at `.agents/skills/init-agent-harness/`, so from `.agents/notes/` the links are `../skills/init-agent-harness/references/<doc>` (the docs' skill-relative path `references/<doc>`, anchored by that install path). Use this body (adjust only if the repo's style clearly differs):

   ```markdown
   # Project notes

   Concluded project knowledge: one note per conclusion, filed by type.

   Unlike `.agents/local/` (in-flight working docs, git-ignored), this directory is
   **tracked by git**. A note is written only once its work has *concluded* — a
   feature implemented in the code, a defect fixed, a proposal explicitly declined
   — so a note records an outcome, never an in-progress plan.

   ## Types and where they are filed

   | Directory | `type` | Holds |
   |---|---|---|
   | `implemented/` | `implemented` | Features live in the code right now |
   | `deprecated/` | `deprecated` | Features removed or superseded |
   | `fixed/` | `fixed` | Repaired defects |
   | `rejected/` | `rejected` | Proposals explicitly declined |
   | `archived/` | `archived` | History snapshots — for agent recall only |

   ## Where notes come from

   Knowledge crosses from the untracked `.agents/local/` into a note only when its
   conclusion is confirmed — the **promotion gate**. The gate, the five types on
   their two tracks, and which types stay in sync with the code are defined in
   [`../skills/init-agent-harness/references/state-lifecycle.md`](../skills/init-agent-harness/references/state-lifecycle.md).

   ## Note structure

   Every note carries YAML frontmatter and follows the `<date>-<topic>.md` filename
   rule. The authoritative field list, filename convention, and conformance checks
   live in [`../skills/init-agent-harness/references/project-notes-schema.md`](../skills/init-agent-harness/references/project-notes-schema.md).
   ```

   The README is tracked by git like the rest of `.agents/notes/`, so it is **not** placed under the git-ignored `.agents/local/`.

4. **Make `.agents/local` untracked.** Confirm the project's `.gitignore` ignores local content while keeping the scaffold committed. A bare `.agents/local/*` + `!.agents/local/.gitkeep` is **not enough**: git won't descend into an excluded directory, so the nested `.gitkeep` files under `plans/`, `prd/`, etc. stay ignored and those folders silently vanish from version control. Use the recursive form with a keep per level:
   ```
   /.agents/local/**
   !/.agents/local/.gitkeep
   !/.agents/local/*/
   !/.agents/local/*/.gitkeep
   ```
   Real documents under `.agents/local/**` are ignored; every level of the folder structure stays tracked. Without this, generated documents silently land in git — or the local folder structure is never committed.

5. **Write the three rules into AGENTS.md** as a section (create it now if the file was empty). Append below, adjusting heading to the file's existing structure. Idempotency: if a rule with the same intent already exists, replace it rather than adding a duplicate section. The block points note semantics at `.agents/notes/README.md` (written in Step 3), which links the two authoritative docs, so it stays short here instead of restating the schema.

   ```markdown
   ## Agent document workflow

   ### Generated documents go under .agents/local
   The documents generated by the AGENT (including plan documents, spec documents, prd documents, reports, etc.) must all be placed in the corresponding folders under `.agents/local` (which is ignored by git). Unless the user explicitly requests that a generated document be tracked by git.
   Name each generated document `<datetime>-<topic>.md`, e.g. `2026-09-05-rag-eval-spec.md` — a leading date, the topic, joined by `-`.

   ### The note model is defined under .agents/notes/ — read it when it matters
   `.agents/notes/README.md` explains the note model and links its two authoritative documents — `state-lifecycle.md` (promotion gate, five types on two tracks) and `project-notes-schema.md` (frontmatter fields, filename rule, conformance). When the AGENT files, retrieves, or classifies a note — or answers from one and the type↔track distinction or a field matters — it reads that README (and the doc it points to) instead of relying on this short summary.

   ### File concluded work as typed notes under .agents/notes
   When a requirement's documents have been reviewed by the user or fully implemented in the code, combine the corresponding PRD and SPEC documents with the current code implementation, and write a note document in the matching folder under `.agents/notes` — `implemented` for a feature live in the code, `deprecated` for a feature removed or superseded, `fixed` for a resolved defect, `rejected` for a declined proposal, `archived` for a history snapshot. Name each note `<date>-<topic>.md`, per the schema's filename rule.

   ### Consult notes when answering
   When a user wants to search for something or find the usage of the repo, the AGENT can read the filenames of the notes located under `.agents/notes/` and use them to determine which note it should read. Then it combines the content of that note with the repo to answer the user. When the question is about the repo's current state, prefer the `implemented` / `deprecated` / `fixed` notes (they track the code); when it is about how the repo got here, consult `archived`. But if no note should be read, the AGENT answers the user using only the repo.
   ```

6. **Encode the filename convention.** Generated working documents under `.agents/local/` follow `<datetime>-<topic>.md` — a leading date (ISO, e.g. `2026-09-05`), then the topic, joined by `-`, e.g. `2026-09-05-rag-eval-spec.md`. Concluded-work notes follow the schema's own filename rule — `<date>-<topic>.md`, the date equal to the frontmatter `date` (see the schema doc linked from `.agents/notes/README.md`) — the same shape, with the schema doc authoritative for notes. Without a date prefix, working docs of the same topic collide and notes can't be ordered by when the work was done.

7. **Verify.** Re-read the final AGENTS.md; confirm all three rules are present and readable, and that its note-model rule points at `.agents/notes/README.md` — no copy is installed under `docs/` any more, so no rule should reference a `docs/` path. Confirm `.agents/notes/README.md` exists and its two relative links resolve to the skill's bundled copies under `.agents/skills/init-agent-harness/references/`. Confirm `.agents/local` content is ignored (`git check-ignore .agents/local/<any doc>` reports it) and the scaffold folders exist. Show the resulting section to the user.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Auto-invoking the skill when an agent task merely involves AGENTS.md docs | Manual-only — never auto-invoke. See When to Use |
| Generated docs default to tracked paths (`docs/`) | Rule 1 must name `.agents/local` explicitly as the default location |
| `.agents/local` isn't git-ignored, so plan/spec files get committed | Ignore local contents while keeping the structure — see Step 4 |
| The gitignore rule keeps `.agents/local` folders from ever being committed | The `.agents/local/*` + one `.gitkeep` pattern can't keep nested folders; use the recursive `**` form in Step 4 |
| A note is filed before the work is concluded | Implemented/deprecated/fixed/rejected/archived notes fire only after review, code implementation, removal, or explicit decision |
| Re-running duplicates the AGENTS.md section | Merge/replace by rule intent — never append blindly |
| AGENTS.md rules point at `docs/state-lifecycle.md` / `docs/project-notes-schema.md` as if the docs were installed there | No copy goes to the project's `docs/` any more — the rules point at `.agents/notes/README.md`, which links the skill's bundled `references/` copies |
| The notes README's links don't resolve | They must point into the skill's bundled copies at `.agents/skills/init-agent-harness/references/` — Step 7 checks they resolve |
| The notes README lands under `.agents/local/` (git-ignored) or links with the wrong depth | It belongs at `.agents/notes/README.md`, linking `../skills/init-agent-harness/references/<doc>` — the skill-relative `references/<doc>` anchored at the skill's `.agents/skills/` install path |
| Editing the wrong AGENTS.md in a multi-repo workspace | Operate on the repo root that owns the `.agents/` harness |
| Working in a subfolder of a larger git repo where the `.agents/` gitignore won't take effect | Skip gitignore changes (not your repo root) and create only the scaffold + AGENTS.md |

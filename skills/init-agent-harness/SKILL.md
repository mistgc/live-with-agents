---
name: init-agent-harness
description: MANUAL-ONLY skill. Do not auto-invoke. Use ONLY when the user directly asks to run this skill — e.g. to set up or refresh a project's AGENTS.md with output-constraint rules, adding a .agents harness so agents store generated docs (plan/spec/prd/reports) under git-ignored .agents/local, file concluded work as typed notes (implemented/deprecated/fixed/rejected/archived) under .agents/notes, and consult those notes when answering repo questions. It also writes a README under .agents/notes explaining that folder and pointing at the two governing reference docs (state-lifecycle.md, project-notes-schema.md) by relative path into the skill's bundled references directory, and the AGENTS.md rules it writes tell future agents to read that README when filing or consulting notes. It additionally scaffolds a .agents/rules region for scoped agent-behavior constraints, writes its .agents/rules/README.md linking the rules schema bundled in the writing-agent-rules skill, and points AGENTS.md at it, while the rule files themselves are authored by that skill, which also regenerates the rules README as its index. It audits the project against a fixed conformance checklist first — a project that already conforms is reported and left unchanged rather than re-initialized — and where requirements fail it reports each gap by location, asks the user whether to change it, and proposes a tiered migration plan to approve before anything is written.
disable-auto-invoke: true
---

# Init Agent Harness

## Overview

A repo's AGENTS.md should tell future agents three things about documents:

1. **Store** every document the agent generates (plan/spec/prd/reports) under the git-ignored `.agents/local/` — keep working docs out of git history unless the user explicitly asks to track one.
2. **File** concluded work as typed notes under `.agents/notes/`, one directory per type — `implemented/` for features live in the code, `deprecated/` for removed/superseded features, `fixed/` for resolved defects, `rejected/` for declined proposals, `archived/` for history snapshots — so later sessions can reconstruct intent without re-deriving it.
3. **Consult** those notes when asked to search the repo or explain its usage, combining the relevant note with the repo — and answering from the repo alone when no note applies.

This skill encodes those three rules — together with the note-model pointer and the constraints region described below — as the **five AGENTS.md rules** the [conformance checklist](#conformance-requirements) verifies, and makes sure the `.agents/` harness and gitignore support them.

Beyond documents, the harness carries a **constraints** region: `.agents/rules/` holds scoped, durable rules on agent behavior — one rule per flat `<id>.md` file, schema `agent-rules/v1`. This skill scaffolds that directory, writes its `.agents/rules/README.md` (Step 3), and points `AGENTS.md` at it. That README links the rules schema at `../skills/writing-agent-rules/references/agent-rules-schema.md` — the bundled copy owned by the `writing-agent-rules` skill, which also authors the rule files and regenerates the README as its index. This skill installs no copy of the rules schema, exactly as it installs none of its own note docs into the project.

Rules 2 and 3 rest on two authoritative reference documents, which this skill bundles under its own `references/` directory:

- `references/state-lifecycle.md` — where notes come from: the promotion gate, the five types on their two tracks (current-truth / history / terminal).
- `references/project-notes-schema.md` — the note schema (`project-notes/v2`): frontmatter fields, the filename rule, conformance checks.

Rather than copy them into the project's `docs/`, the skill writes a short `.agents/notes/README.md` that orients a reader who lands in the notes folder and links both docs by relative path into that `references/` directory (through the skill's install location, `.agents/skills/init-agent-harness/`). The AGENTS.md section written by this skill points at that README, so the AGENT reaches the docs whenever it files, retrieves, or classifies a note.

**Audit before writing.** This is not a one-shot scaffold. The skill first scores the project against a fixed set of [conformance requirements](#conformance-requirements), then:

- **Already conforms → nothing to do.** Report what was checked and leave every file untouched. Re-initializing a conformant project is a defect, not a refresh.
- **Partly conforms → targeted repair.** Report each failing requirement **by location**, and propose a migration plan tiered by risk for the user to approve. Only the approved gaps are changed.

This matters because harnesses drift in place: a repo bootstrapped by an older revision of this skill may still have `AGENTS.md` pointing at `docs/` copies, or have the notes region but no rules region. A blanket re-run would duplicate rules and overwrite hand-edited content; the audit makes the work proportional to what actually fails.

## When to Use

**Manual-only — never auto-invoke.** This skill changes a project's governing agent rules, so it runs only when the user explicitly asks. Do not trigger it unprompted during other work, and do not chain it from other skills.

- The user directly asks to run this skill, or to "add output-constraint rules" to a project's AGENTS.md.
- The user asks to bootstrap the agent-document workflow / `.agents/` harness in a repo.
- The user asks whether a project's harness is **set up, up to date, or conformant** — the audit alone is a valid run, and may legitimately end in "already conformant, nothing to do".
- The user asks to **migrate an older harness** — e.g. one whose `AGENTS.md` still points at `docs/` copies of the note docs, or that predates the `.agents/rules/` region.

When **not** to use: the user wants planning docs deliberately tracked in git; the repo runs a deliberately different harness variant and the user does not want it changed; or the task merely resembles this one (e.g. writing an AGENTS.md) without the user asking for the output-constraint setup.

## Conformance requirements

"Already done" is defined by this checklist, not by a vibe. Audit each row
against the **actual files** — a directory that merely exists is not a pass, and
a verdict must name the path that decided it. A row is `n/a` only when the repo
has deliberately chosen a different variant (Step 1d says how to record that).

| # | Requirement | Where it lives | Passes when |
|---|---|---|---|
| H1 | **Root identified** | repo root | The harness sits beside `.agents/` at the root returned by `git rev-parse --show-toplevel` — not in a subfolder of a larger repo. |
| H2 | **AGENTS.md exists** | `<root>/AGENTS.md` | The file exists and is plain Markdown. |
| H3 | **The five rules are present, by intent** | `<root>/AGENTS.md` | It carries rules equivalent to (a) generated docs go under `.agents/local`, (b) the note model is defined under `.agents/notes/` and its README must be read when it matters, (c) concluded work is filed as typed notes, (d) notes are consulted when answering, (e) `.agents/rules/` constrains the agent. Match **intent**, not heading text — a reworded rule that means the same is a pass. |
| H4 | **`local/` scaffold** | `.agents/local/` | `plans/`, `prd/`, `specs/`, `reports/` each exist with a `.gitkeep`. |
| H5 | **`local/` is ignored but resolvable** | `.gitignore` | A real doc under `.agents/local/**` is ignored (`git check-ignore` reports it) **and** every scaffold level is tracked (`git ls-files .agents/local` lists the `.gitkeep`s). The bare `.agents/local/*` form fails this row for nested levels. |
| H6 | **`notes/` scaffold** | `.agents/notes/` | All five type directories exist — `implemented/`, `deprecated/`, `fixed/`, `rejected/`, `archived/`. |
| H7 | **Notes README and its links** | `.agents/notes/README.md` | The file exists and both relative links resolve to `.agents/skills/init-agent-harness/references/state-lifecycle.md` and `.../project-notes-schema.md`. |
| H8 | **Rules README and its link** | `.agents/rules/README.md` | The file exists and its schema link resolves to `.agents/skills/writing-agent-rules/references/agent-rules-schema.md`. |
| H9 | **Filename conventions stated** | `<root>/AGENTS.md` | The rules encode `<datetime>-<topic>.md` for `.agents/local/` working docs and `<date>-<topic>.md` for notes. |
| H10 | **Authoring skills installed** | the skills dir (`skills/` or `.agents/skills/`) | `writing-project-notes`, `retrieving-project-notes`, and `writing-agent-rules` are present — H7/H8's links and all authoring depend on them. |
| H11 | **No legacy `docs/` wiring** | `<root>/AGENTS.md`, `docs/` | No rule points at a `docs/` copy of the note or rules docs. Stale copies under `docs/` from an older revision are **reported**, never deleted without asking (see tier 3 in Step 1d). |

Rows H1–H11 are the whole contract. If a repo satisfies all of them, the correct
output of this skill is a report and **zero writes**.

## Steps

1. **Audit, then decide. Never write before this gate.**

   **a. Locate the harness root.** Run `git rev-parse --show-toplevel`; the harness lives beside `.agents/` at that root. If you are in a subfolder of a larger repo, the root is the repo root that owns `.agents/` — and if `.gitignore` changes would not take effect there, that is a gap to report, not to fix silently (see the Common Mistakes table).

   **b. Score every requirement** in [Conformance requirements](#conformance-requirements) as `present`, `divergent`, `missing`, or `n/a`, by reading the actual files. Record the path that decided each verdict, and quote the offending line for any `divergent` row (a rule pointing at `docs/`, a broken relative link, a non-recursive gitignore).

   **c. If every row is `present` or `n/a` — stop.** Tell the user the project already conforms, list what you checked, and make **no changes**: no AGENTS.md rewrite, no re-created folders, no "refresh" for its own sake. Note that `writing-project-notes` and `writing-agent-rules` remain available for filing notes and adding rules — that is normal use of the harness, not a reason to re-run this skill.

   **d. Otherwise, report the gaps by location and propose a migration plan — then ask.** For each failing row give the id, the deciding path, what currently holds, and the proposed change. Tier the plan cheapest-and-safest first, and present it as a checklist the user can trim:

   | Tier | Kinds of change | Default |
   |---|---|---|
   | **1 · Additive** | Create a missing directory, README, or `.gitkeep`; add a missing AGENTS.md rule | Propose |
   | **2 · Corrective** | Rewrite a divergent rule, repair a broken relative link, fix the recursive gitignore form, add the rules region to a notes-only harness | Propose with the before/after shown |
   | **3 · Destructive** | Delete stale `docs/` copies, remove or replace a superseded rule, restructure a harness variant the repo already runs | **Ask explicitly — never the default** |

   State plainly what is **preserved** (unrelated AGENTS.md content, existing notes, existing rules, extra `local/` categories, any hand-edited rule text) and what is **out of scope**. Then **wait for approval**: execute only the approved rows, in tier order, and re-run the audit afterwards. If the user declines, change nothing and say so.

   A project with no harness at all is the degenerate case — every row fails, so the plan is the full scaffold, and Steps 2–7 are that plan's execution.

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
   ├── rules/          # scoped agent-behavior constraints, one rule per file
   │   └── README.md   # orients a reader in this folder (written in Step 3)
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

   **Write the rules README in the same step.** Write `.agents/rules/README.md` so anyone landing in the rules folder is oriented, and link the rules schema by **relative path into the `writing-agent-rules` skill's install location** — from `.agents/rules/` that is `../skills/writing-agent-rules/references/agent-rules-schema.md` (the schema's skill-relative path `references/agent-rules-schema.md`, anchored by that skill's `.agents/skills/writing-agent-rules/` install path). This skill installs **no copy** of the rules schema — it only links that skill's bundled copy, exactly as the notes README links this skill's bundled note docs. The rules README is also the **generated index** of the rules in force, so use the canonical body below verbatim; it is what `writing-agent-rules`' generator emits for an empty rules tree, so regenerating after rules are filed produces an identical document rather than clobbering different prose. With no rules filed yet, the table reads `_(none yet)_`.

   ````markdown
   # Agent rules

   Constraints in force on the agent: durable, scoped rules on AGENT behavior,
   one rule per flat `<id>.md` file.

   Unlike `.agents/notes/` (concluded knowledge) and `.agents/local/` (in-flight
   working documents), this directory holds *standing constraints* — what the
   AGENT must do, must not do, should prefer, or may do, within an explicit scope.
   Rules are authored with the `writing-agent-rules` skill; never hand-write a rule
   file or hand-edit this index.

   This file is **generated from rule frontmatter**. Regenerate it after adding or
   changing a rule, instead of editing it:

   ```sh
   python .agents/skills/writing-agent-rules/scripts/scan_rules.py --index > .agents/rules/README.md
   ```

   The schema is `agent-rules/v1`; the authoritative field list, precedence rule
   and conformance checks (R1–R16) live in
   [`../skills/writing-agent-rules/references/agent-rules-schema.md`](../skills/writing-agent-rules/references/agent-rules-schema.md).

   ## In force

   | Rule | Modality | Scope | Statement |
   |---|---|---|---|
   | _(none yet)_ | | | |

   `always` means the rule has no `paths` and no `triggers` — it is global.
   ````

   If the `writing-agent-rules` skill is already installed, prefer running its generator so the body stays canonical:

   ```sh
   python .agents/skills/writing-agent-rules/scripts/scan_rules.py --index > .agents/rules/README.md
   ```

4. **Make `.agents/local` untracked.** Confirm the project's `.gitignore` ignores local content while keeping the scaffold committed. A bare `.agents/local/*` + `!.agents/local/.gitkeep` is **not enough**: git won't descend into an excluded directory, so the nested `.gitkeep` files under `plans/`, `prd/`, etc. stay ignored and those folders silently vanish from version control. Use the recursive form with a keep per level:
   ```
   /.agents/local/**
   !/.agents/local/.gitkeep
   !/.agents/local/*/
   !/.agents/local/*/.gitkeep
   ```
   Real documents under `.agents/local/**` are ignored; every level of the folder structure stays tracked. Without this, generated documents silently land in git — or the local folder structure is never committed.

5. **Write the five rules into AGENTS.md** as a section (create it now if the file was empty). Append below, adjusting heading to the file's existing structure. Idempotency: if a rule with the same intent already exists, replace it rather than adding a duplicate section. The block points note semantics at `.agents/notes/README.md` (written in Step 3), which links the two authoritative docs, so it stays short here instead of restating the schema.

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

   ### Rules under .agents/rules constrain what the AGENT may do
   `.agents/rules/` holds durable, scoped constraints on AGENT behavior — one rule per flat `<id>.md` file, schema `agent-rules/v1`. When acting in an area a rule covers, read that rule; treat `require` and `forbid` rules as binding within their `paths` / `triggers` scope, and `prefer` as a default the AGENT may deviate from only with a stated reason. `.agents/rules/README.md` is the generated index of the rules in force — if it is missing or says none are filed, no rules exist yet and the AGENT proceeds from the repo and the AGENTS.md rules alone. Author or change a rule with the `writing-agent-rules` skill; never hand-write a rule file or hand-edit the index.
   ```

6. **Encode the filename convention.** Generated working documents under `.agents/local/` follow `<datetime>-<topic>.md` — a leading date (ISO, e.g. `2026-09-05`), then the topic, joined by `-`, e.g. `2026-09-05-rag-eval-spec.md`. Concluded-work notes follow the schema's own filename rule — `<date>-<topic>.md`, the date equal to the frontmatter `date` (see the schema doc linked from `.agents/notes/README.md`) — the same shape, with the schema doc authoritative for notes. Without a date prefix, working docs of the same topic collide and notes can't be ordered by when the work was done.

7. **Verify by re-running the audit.** Re-score every row of [Conformance requirements](#conformance-requirements) — the same checklist Step 1 used, so the work is verified against the gate that authorised it, not against a fresh opinion. Confirm all five rules are present in AGENTS.md and readable, and that its note-model rule points at `.agents/notes/README.md` — no copy is installed under `docs/` any more, so no rule should reference a `docs/` path unless H11 was explicitly accepted as `n/a`. Confirm the rules rule points at `.agents/rules/`, that the directory exists, and that `.agents/rules/README.md` exists with its schema link resolving to `.agents/skills/writing-agent-rules/references/agent-rules-schema.md` (if that skill is not installed, the link cannot resolve — install it or tell the user the rules region is unwired). Confirm `.agents/notes/README.md` exists and its two relative links resolve to the skill's bundled copies under `.agents/skills/init-agent-harness/references/`. Confirm `.agents/local` content is ignored (`git check-ignore .agents/local/<any doc>` reports it) while the scaffold stays tracked. Report any row still failing as an unfinished migration — do not silently drop it. Show the resulting AGENTS.md section to the user.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Re-initializing a project that already conforms | Step 1c — report and stop. A conformant repo gets zero writes; a "refresh" that rewrites files is a defect |
| Auditing by directory listing instead of reading files | A folder can exist while its README's links are broken or a rule still points at `docs/`. Every verdict must name the path that decided it |
| Treating a reworded rule as missing and adding a second one | Match H3 by **intent**; replace the existing rule in place rather than appending a near-duplicate |
| Fixing everything the audit found without asking | Step 1d — report gaps by location, tier the plan, and wait for approval; execute only approved rows |
| Silently deleting stale `docs/` copies or a superseded rule | Tier 3 is destructive — always ask first, and default to reporting rather than removing |
| Presenting gaps without a migration plan or an order | Each gap needs its location, what holds now, the proposed change, its tier, and what is preserved |
| Claiming success after a partial migration | Step 7 re-runs the audit; a row still failing is reported as unfinished, never dropped |
| Auto-invoking the skill when an agent task merely involves AGENTS.md docs | Manual-only — never auto-invoke. See When to Use |
| Generated docs default to tracked paths (`docs/`) | Rule 1 must name `.agents/local` explicitly as the default location |
| `.agents/local` isn't git-ignored, so plan/spec files get committed | Ignore local contents while keeping the structure — see Step 4 |
| The gitignore rule keeps `.agents/local` folders from ever being committed | The `.agents/local/*` + one `.gitkeep` pattern can't keep nested folders; use the recursive `**` form in Step 4 |
| A note is filed before the work is concluded | Implemented/deprecated/fixed/rejected/archived notes fire only after review, code implementation, removal, or explicit decision |
| Re-running duplicates the AGENTS.md section | Merge/replace by rule intent — never append blindly |
| AGENTS.md rules point at `docs/state-lifecycle.md` / `docs/project-notes-schema.md` as if the docs were installed there | No copy goes to the project's `docs/` any more — the rules point at `.agents/notes/README.md`, which links the skill's bundled `references/` copies |
| The notes README's links don't resolve | They must point into the skill's bundled copies at `.agents/skills/init-agent-harness/references/` — Step 7 checks they resolve |
| The notes README lands under `.agents/local/` (git-ignored) or links with the wrong depth | It belongs at `.agents/notes/README.md`, linking `../skills/init-agent-harness/references/<doc>` — the skill-relative `references/<doc>` anchored at the skill's `.agents/skills/` install path |
| `.agents/rules/` is scaffolded but nothing points at it | The AGENTS.md rules section must carry the rules rule, pointing at `.agents/rules/` and at the `writing-agent-rules` skill |
| `.agents/rules/README.md` is left unwritten | Step 3 writes it — it orients a reader in the rules folder and is the generated index of the rules in force |
| A rule *file* is hand-written from this skill | This skill writes the rules README and scaffold only — rule authoring belongs to `writing-agent-rules` |
| The rules README's schema link points at a `docs/` copy or has the wrong depth | It must link `../skills/writing-agent-rules/references/agent-rules-schema.md` — the bundled copy in the `writing-agent-rules` install, never an installed `docs/` copy |
| A rules README is authored with different prose from the generator's | Use the canonical body in Step 3 verbatim, or run the `writing-agent-rules` generator — a regenerated index must reproduce the bootstrapped one, not clobber it |
| The rules region is wired but `writing-agent-rules` is not installed | Its schema link cannot resolve — install that skill, or tell the user the rules region is unwired |
| Editing the wrong AGENTS.md in a multi-repo workspace | Operate on the repo root that owns the `.agents/` harness |
| Working in a subfolder of a larger git repo where the `.agents/` gitignore won't take effect | Skip gitignore changes (not your repo root) and create only the scaffold + AGENTS.md |

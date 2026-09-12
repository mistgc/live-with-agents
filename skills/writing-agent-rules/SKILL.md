---
name: writing-agent-rules
description: Use when the user wants to constrain agent behavior with a durable rule — "add a rule that…", "never do X", "always do Y", "make the agent stop doing Z", "write this constraint down", or when a recurring failure should be pinned so it cannot recur. Turns a stated constraint into one conformant rule file at .agents/rules/<id>.md, classified by modality (require/forbid/prefer/allow), given an explicit scope and a check, and wired into the rules index. Also use when asked to review, tighten, supersede, or retire an existing rule. Not for capabilities (skills) or records of concluded work (project notes).
---

# Writing Agent Rules

## Overview

An **agent rule** is a durable, scoped constraint on how an agent acts: "never
commit a generated document", "file every implemented note with its commit set",
"prefer a new dated note over rewriting an old one". Rules live under
`.agents/rules/`, one rule per file, and stay in force until they are superseded
or retired.

A rule is **not** a skill and **not** a note:

| Artifact | Question it answers | Force | Shape |
|---|---|---|---|
| Skill | "how do I do X?" | invoked on demand | a procedure; may be long |
| **Rule** | **"what must / must not I do?"** | **in force while `active`, inside its scope** | **one sentence + rationale + a check** |
| Note | "what concluded?" | none — a record | a distillation |

**Boundary test before writing anything:** if the constraint needs steps to
follow, it is a skill (write the skill; the rule may point at it). If it records
something that already happened, it is a note (`writing-project-notes`). If it
requires, forbids, prefers, or permits one thing, it is a rule — continue.

The authoritative schema is `docs/agent-rules-schema.md` (`agent-rules/v1`).
Every rule carries `schema: agent-rules/v1` and conforms to it.

### The four properties a rule must have

The schema exists to force these, because the failure mode of agent rule files
is unscoped slogans nobody can verify or retire:

1. **One clause** — a single normative sentence, in frontmatter as `statement:`.
   If it cannot be stated in one line, it is not a rule.
2. **A modality** — `require` / `forbid` / `prefer` / `allow`. Polarity and
   strength are explicit, so `prefer` (a default you may deviate from with a
   reason) is never confused with `forbid`.
3. **An explicit scope** — `paths` and/or `triggers`. Absence means *global*, so
   an unscoped rule is a deliberate statement, not an oversight.
4. **A check** — a script path, or `manual`/`review`. Saying "this one is
   judgment" is required; leaving it blank is not allowed.

## When to Use

- The user states a constraint: "add a rule that…", "never do X", "always do Y".
- The user asks to write down / formalize a constraint the agent keeps breaking,
  or that was just decided in conversation.
- A recurring failure should be pinned so it cannot recur.
- The user asks to **review, tighten, supersede, or retire** an existing rule.

**When not to use:** the request is a capability, not a constraint (write or use
a skill instead); the work concluded and needs recording (use
`writing-project-notes`); the user wants a one-off instruction for this task
only (just follow it — a rule is durable and global); or the "rule" is really
several steps of procedure (that is a skill). **Never invent a rule the user did
not ask for** — unprompted rules are governance the user did not consent to.

## Where the rules live

```
<repo>/.agents/rules/
├── <id>.md            # one file per rule, flat; id == filename base
├── <id>.md
└── README.md          # index: active rules, generated from frontmatter
```

- **Repo runs the `.agents/rules/` convention** → write there.
- **An AGENTS.md or the user names a different rules location** → write there,
  keeping the `<id>.md` flat layout.
- **No convention exists** → default to `.agents/rules/` and create it, then tell
  the user that AGENTS.md should point at `.agents/rules/README.md` so future
  agents find it. If creating the directory would surprise the user, ask first.

The rules README is both the orientation doc for the folder and the **index** of
the rules in force, generated from frontmatter by `scripts/scan_rules.py --index`
— never hand-maintained, or it drifts. `init-agent-harness` writes the same
canonical body when it bootstraps the harness, so regenerating after rules are
filed reproduces that document with the table filled in rather than clobbering
different prose.

## Steps

1. **Capture the constraint in the user's own words**, verbatim. Then find its
   provenance: what failure, incident, or decision produced it? A rule with no
   traceable failure is usually a preference — consider `prefer` or `allow`
   rather than `forbid`, or ask whether it is really wanted.

2. **Run the boundary test** (above). If it is a skill or a note, say so and
   stop. If it is several clauses, split it into several rules — one per file.

3. **Classify `modality`.** Judge, and say why:
   - `forbid` / `require` — a violation genuinely must block the action.
   - `prefer` — the right default, but a reasoned deviation is fine.
   - `allow` — this is carving an exception out of another rule (see Step 7).
   When the user's phrasing is ambiguous between hard and soft, **ask** — the
   difference is exactly "blocks the action" vs "allowed with a reason".

4. **Force an explicit scope.** Ask which paths and/or triggers it governs, or
   state the default out loud: **no `paths` and no `triggers` means global.** Do
   not let the scope stay implicit, and do not write `paths: ["**/*"]` to mean
   "global" — omit the key and let the index render `always`. Quote globs that
   begin with `*`.

5. **Establish a `check`.** Look for an existing script that already enforces
   this. If none exists, either offer to write one (name it under `scripts/`) or
   record `manual`/`review` **and** write the review procedure into the body's
   `## Check` section. Never leave the check implicit.

6. **Check for conflicts and duplicates before writing.** Run
   `python scripts/scan_rules.py --validate` and `--conflicts`. Then:
   - **An existing rule on the same topic** → do not duplicate. Wording fixes are
     in-place edits; a change to the normative content or `modality` requires a
     **new `id`** with `supersedes: [old-id]` (Step 9).
   - **A genuine conflict** with a live rule → resolve it explicitly with a
     narrower scope or an `overrides` entry. An equal-specificity conflict
     between different modalities is reported as a lint **error**, not resolved
     for you — the rule set is ambiguous until you say which wins.

7. **Express exceptions as `allow` rules**, never as an inline free-text list. An
   `allow` rule names the rule it carves out in `overrides`, and carries its own
   rationale, scope, and check. Its scope must actually overlap its target's, or
   it is unreachable (a lint).

8. **Write the rule** from the template below, then the **confirm rule text with
   the user before saving** when the rule is `require`/`forbid` — a hard rule
   changes governance, and the exact `statement` is the thing being agreed to.

9. **Supersede, never delete.** To replace a rule: write the successor with a new
   `id` and `supersedes: [old-id]`, then set the old rule's `status: superseded`
   and add `updated:`. To withdraw one: `status: retired`. The files stay — the
   audit trail ("which rule was in force then") depends on it.

10. **Verify.** Re-read the file: `id` equals the filename, `statement` is one
    line and matches `modality`, `check` resolves, body has `## Rationale`,
    `## Check`, `## Exceptions`. Run
    `python scripts/scan_rules.py --validate` and report the rule's scope, its
    precedence position, and any lint. Regenerate the rules README index.

## The schema in brief

The canonical schema is `docs/agent-rules-schema.md`.

```yaml
---
schema: agent-rules/v1
id: no-generated-docs-in-git         # slug; must equal the filename base
statement: Never add a generated working document to git; keep it under .agents/local
status: active                        # draft | active | superseded | retired
modality: forbid                      # require | forbid | prefer | allow
paths: ["**/*"]                       # optional globs; absent = any path
triggers: [file-write, git-commit]    # optional events; absent = any trigger
check: scripts/check-local-docs.sh    # required: a path, or manual/review
tags: [documents, git]                # optional
sources: [.agents/notes/implemented/2026-09-07-agent-harness.md]  # optional
overrides: []                         # optional; ids this rule wins over
supersedes: []                        # optional; ids this rule replaces
date: 2026-09-12
updated: 2026-09-12                   # optional; >= date
---
```

Every value is a **scalar or a list** — no nested mappings — so the stdlib
frontmatter scanner can filter on any field. Render only the keys a rule
actually needs; omit empty optional keys.

**Statement phrasing must match `modality`** (a lint if it does not):

| `modality` | Phrasing | Example |
|---|---|---|
| `require` | imperative verb | `File every implemented note with its full commit set` |
| `forbid` | `Never …` / `Do not …` | `Never add a generated working document to git` |
| `prefer` | `Prefer …` | `Prefer a new dated note over rewriting an existing one` |
| `allow` | `… may …` | `A generated document may be committed when the user asks` |

Avoid `:` and ` #` inside `statement` — the frontmatter reader splits on the
first `:` and strips a trailing ` #` comment.

### Precedence

When two live rules disagree, the first step that separates them wins:
**explicit `overrides`** → **narrower scope** (specificity is intent, so this
resolves quietly) → **otherwise the pair is ambiguous**. Two rules of equal
specificity with different modalities have no principled winner, so the validator
reports an **error** and requires an explicit `overrides` or a narrower scope.
The conservative reading `forbid` > `require` > `prefer` > `allow` is a reporting
aid only — never rely on it. A rule the user wrote must never be quietly
overridden by another.

## Template

```markdown
---
<frontmatter per the schema above>
---

# <statement as a title, or a short name>

## Rationale
Why this constraint exists and what fails without it. Name the concrete failure
that motivated it — this is what lets a future agent apply the rule to cases it
never anticipated.

## Scope
When the rule applies and when it does not, in plain language. Restate `paths`
and `triggers`; say "global" when both are absent.

## Check
The exact command to verify compliance, or the manual/review procedure when
frontmatter `check` is `manual`. State what a failure means.

## Exceptions
Known carve-outs, each naming the `allow` rule that grants it. `None.` is valid.

## Examples
- Compliant: <a case that satisfies the rule>
- Violation: <a case that breaks it>
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Writing a procedure as a rule | If it needs steps, write a skill; the rule points at it |
| Inventing rules the user did not ask for | Author only on request or on an articulated constraint — rules are durable governance |
| Leaving scope implicit | Absence means **global** — make that a deliberate choice, and omit the key rather than writing `["**/*"]` |
| Everything classified `forbid` | `prefer` (default, deviable with a reason) and `allow` (explicit permission) are not weaker rules — they are the correct ones |
| Blank or implicit check | `check` is required; `manual`/`review` is a valid answer, silence is not |
| Inline `exceptions:` free text | A carve-out is an `allow` rule with `overrides: [rule-id]`, so it is scoped, checked, and auditable |
| Duplicating a rule that already exists | Same topic → edit wording in place, or supersede with a new `id` |
| Editing `statement` or `modality` in place | Normative change = new `id` + `supersedes`; in-place edits are wording only |
| Deleting a retired rule | Retire or supersede it and keep the file — the audit trail depends on it |
| A `statement` that needs two sentences | It is two rules, or it is a skill — split it or say so |
| Nested `scope:` mapping in frontmatter | Flat `paths:` / `triggers:` lists only — nested mappings are unparseable for the scanner |
| `:` or ` #` inside `statement` | The frontmatter reader truncates it — rephrase |
| Hand-maintaining the rules README | Regenerate the index from frontmatter; hand-edited indexes drift |
| Writing a hard rule without confirming the text | For `require`/`forbid`, get the exact `statement` agreed before saving |

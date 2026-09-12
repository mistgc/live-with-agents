# Agent Rules Schema Specification

- **Status:** ready
- **Version:** `agent-rules/v1`
- **Date:** 2026-09-12
- **Governing directory:** `.agents/rules/`
- **Consumers:** `writing-agent-rules`, `scripts/scan_rules.py`, `init-agent-harness`
- **Companion:** [`docs/project-notes-schema.md`](./project-notes-schema.md) — the sibling note schema; this document deliberately reuses its conventions (frontmatter, conformance table, versioning policy)

## Purpose and scope

An **agent rule** is a durable, scoped constraint on how an agent acts. This
document fixes the frontmatter schema, the filename, and the *resolution
semantics* every rule must satisfy. "Fixed" here means:

1. **Stable and versioned** — every rule carries a schema version; the schema
   evolves only by a documented version bump, never silently.
2. **Machine-checkable** — the constraints in [Conformance](#conformance) map to
   assertions a tool can run over the rules tree.
3. **Unambiguous in force** — where two rules disagree, [Precedence](#precedence)
   determines the winner deterministically, and lint reports the ambiguity.
4. **Single source of truth** — agent behavior must not contradict this document.

This schema governs a rule's **frontmatter, filename, and scope**. Body
structure belongs to `writing-agent-rules`, with the exceptions listed under
[Per-rule body requirements](#per-rule-body-requirements).

A rule is **not** a skill and **not** a note. The boundary is fixed:

| Artifact | Question it answers | Force | Shape | Location |
|---|---|---|---|---|
| Skill | "how do I do X?" | invoked on demand | procedure; may be long | `skills/<name>/SKILL.md` |
| **Rule** | **"what must / must not I do?"** | **in force while `active`, within its scope** | **one sentence + rationale + check** | **`.agents/rules/<id>.md`** |
| Note | "what concluded, and why is the repo like this?" | none — a record | distillation | `.agents/notes/<type>/<date>-<topic>.md` |

**Test:** if it needs steps to follow, it is a skill (a rule may *point at* one).
If it records something that already happened, it is a note. If it forbids,
requires, prefers, or permits one thing, it is a rule.

## Canonical schema

```markdown
---
schema: agent-rules/v1
id: no-generated-docs-in-git
statement: Never add a generated working document to git; keep it under the git-ignored .agents/local
status: active
modality: forbid
paths: ["**/*"]
triggers: [file-write, git-commit]
check: scripts/check-local-docs.sh
tags: [documents, git]
sources: [.agents/notes/implemented/2026-09-07-agent-harness.md]
date: 2026-09-12
---
```

### Field table

| Key | Required | Type | Constraints |
|---|---|---|---|
| `schema` | yes | string | Exactly `agent-rules/v1`. |
| `id` | yes | slug | `[a-z0-9]+(-[a-z0-9]+)*`. **Must equal the filename base.** The stable handle used by `overrides`, `supersedes`, and prose references. |
| `statement` | yes | string | The normative clause, **one line**, ≤ 200 chars. Its modal verb must match `modality` (see [Statement phrasing](#statement-phrasing)). |
| `status` | yes | enum | One of `draft` \| `active` \| `superseded` \| `retired`. |
| `modality` | yes | enum | One of `require` \| `forbid` \| `prefer` \| `allow`. |
| `check` | yes | string | `manual`, `review`, or a **repo-relative path that exists on disk**. Required even when manual — a rule that cannot be checked is a slogan, and saying so explicitly is the point. |
| `paths` | optional | list | Glob list (POSIX, repo-relative) the rule governs: `*`, `**`, `?`. **Absent = any path.** Quote globs that begin with `*` (`["**/*.md"]`). |
| `triggers` | optional | list | Lifecycle events the rule governs (see [Triggers](#triggers)). **Absent = any trigger.** |
| `overrides` | optional | list | Rule ids this rule takes precedence over. Every entry must resolve to an existing rule. |
| `supersedes` | optional | list | Rule ids this rule replaces. Every entry must resolve, and the named rules must carry `status: superseded`. |
| `tags` | optional | list | Lowercase `[a-z0-9-]` identifiers for grouping. Omit when empty. |
| `sources` | optional | list | Repo-relative paths recording provenance (the incident, note, or doc this rule came from). Each must exist. |
| `date` | yes | date | ISO `YYYY-MM-DD`, the date the rule was authored. |
| `updated` | optional | date | ISO `YYYY-MM-DD`, last wording/clarification edit. Must be ≥ `date`. |

Every field is a **scalar or a list** — there are no nested mappings. This is
load-bearing, not stylistic: it keeps the whole rule parseable by the
stdlib-only frontmatter scanner, so `paths`, `triggers`, `modality`, and
`status` stay *filterable* ([see the scanner](#the-scanner)).

Unknown top-level keys are not part of v1, but they do **not** make a rule
non-conformant: readers must tolerate and ignore them, and a validator reports
them as a lint warning — a signal to run the
[versioning policy](#versioning), not a failure. There is no free-form escape
hatch: if a rule needs more, that is a schema version question, not a one-off
field.

## Modality

`modality` carries *polarity* and *strength* in one value, so a machine reading
only frontmatter knows what kind of constraint it is:

| `modality` | Meaning | Deviation |
|---|---|---|
| `require` | Obligation — the action must happen. | Not permitted. |
| `forbid` | Prohibition — the action must not happen. | Not permitted. |
| `prefer` | Default behavior. | Permitted **with a stated reason**. |
| `allow` | Explicit permission — normally used to carve an exception out of a `forbid`/`require` rule. | N/A — this *is* the permission. |

`require` and `forbid` are the **hard** modalities: a violation blocks the action
until the user resolves it. `prefer` is **soft**: the agent may deviate but must
say why. `allow` grants permission and is the only way to carve out an exception
(see [Exceptions](#exceptions)).

### Statement phrasing

`statement` must be phrased consistently with `modality`, so the clause reads
correctly in an index without its frontmatter:

| `modality` | Phrasing | Example |
|---|---|---|
| `require` | imperative verb | `File every implemented note with its full commit set` |
| `forbid` | `Never …` / `Do not …` | `Never add a generated working document to git` |
| `prefer` | `Prefer …` | `Prefer a new dated note over rewriting an existing one` |
| `allow` | `… may …` | `A generated document may be committed when the user asks` |

Avoid `:` and ` #` inside `statement` — the stdlib frontmatter reader splits on
the first `:` and strips a trailing ` #` comment.

## Scope

A rule is in force only where its scope matches. Scope is the product of two
independent dimensions, and **absence means unrestricted, not empty**:

- **`paths`** — globs matched against repo-relative POSIX paths. No negation:
  express a carve-out as an `allow` rule, never as a `!pattern`.
- **`triggers`** — lifecycle events.

A rule with neither `paths` nor `triggers` is **global**. Globality is a real
decision, so indices and scan tables render it explicitly as `always` — silence
must never look like narrowness.

### Triggers

An open vocabulary; unknown triggers are a lint warning, not a failure:

| Trigger | Fires when the agent… |
|---|---|
| `file-write` | creates or edits a file |
| `file-delete` | deletes a file |
| `git-commit` | stages or commits |
| `git-push` | pushes |
| `shell` | runs a shell command |
| `plan` | produces a plan |
| `answer` | answers the user |
| `note-write` | files a project note |
| `rule-write` | authors a rule |
| `skill-invoke` | invokes a skill |

## Precedence

Rule sets conflict. Resolution is **deterministic and ordered** — the first step
that separates two matching rules decides:

1. **Explicit override wins.** If A lists B in `overrides` and both match, A wins.
   This is the only way to state that a conflict is *intended*.
2. **Narrower scope wins.** A rule that restricts `paths` or `triggers` beats one
   that leaves them unrestricted; if both restrict, the more specific glob wins
   (more literal characters, fewer wildcards). Specificity is a deliberate signal,
   so this resolves without complaint (reported as a warning, at most).
3. **Otherwise the pair is ambiguous.** Two rules of equal specificity with
   different modalities have no principled winner: the ordering is a coin flip
   the author must break. The validator reports it as an **error**, and requires
   an explicit `overrides` or a narrower scope. For *reporting only*, the
   conservative reading is `forbid` > `require` > `prefer` > `allow` — ambiguity
   resolves against the action rather than silently in its favour — but this is
   a diagnostic aid, never a legitimate resolution.

Because differing modalities always differ in strength, step 3 is where every
unmarked equal-specificity conflict lands: there is no "silent tiebreak" that
lets an ambiguous pair pass. That is deliberate — a rule the author wrote must
never be quietly overridden by another.

Cross-rule lints report: **ambiguity** (equal specificity, differing modality, no
explicit override — an error), **scope-resolved overlap** (a warning, since the
narrower rule silently wins), **unreachable `allow`** (an `allow` rule whose
`overrides` target is missing or whose scope does not overlap its target), and
**draft dependency** (an active rule referencing a `draft` rule).

## Exceptions

An exception is **not** a field. It is a first-class `allow` rule that names the
rule it carves out in `overrides`:

```markdown
---
schema: agent-rules/v1
id: allow-tracked-doc-on-request
statement: A generated document may be committed when the user explicitly asks for it to be tracked
status: active
modality: allow
triggers: [git-commit]
check: manual
overrides: [no-generated-docs-in-git]
date: 2026-09-12
---
```

Why not an inline `exceptions:` string: a carve-out carries its own rationale,
scope, and check, and `--modality allow` then enumerates **every escape hatch in
the system**. An inline free-text exception list can be neither checked nor
audited, and silently grows into a second, invisible rule set. Keeping
exceptions as rules also means precedence step 1 resolves them deliberately
rather than by accident.

## Filename convention

```
<id>.md      e.g. no-generated-docs-in-git.md
```

- The file's parent directory is the rules root; the tree is **flat**.
- `id` equals the filename base. There is **no date prefix** — a deliberate
  divergence from notes. A note is dated because it records *when* something
  concluded; a rule is a living current-truth constraint, so a date prefix would
  falsely imply a snapshot. Lifetime is carried by `status` and `updated`.
- A rule is **never deleted**. Withdraw it with `status: retired`, or replace it
  with `status: superseded` plus a successor naming it in `supersedes`. The
  audit trail ("which rule was in force then") depends on this.

## Per-rule body requirements

Body structure belongs to `writing-agent-rules`, with these sections the schema
depends on — all three are **required**, since a rule without them cannot be
reviewed, checked, or safely applied:

- `## Rationale` — why the constraint exists and what fails without it. This is
  the highest-leverage section for agent compliance: an agent that knows the
  *why* generalizes correctly to cases the rule never anticipated.
- `## Check` — how compliance is verified. If frontmatter `check` is a path, say
  how to run it and what a failure means; if `manual`/`review`, state the
  procedure.
- `## Exceptions` — the known carve-outs, each naming the `allow` rule that
  grants it. `None.` is a valid and common answer.

Recommended: `## Scope` (plain-language restatement of `paths`/`triggers`) and
`## Examples` (one compliant and one violating case).

## Conformance

A rule conforms to `agent-rules/v1` iff every check below passes.

| # | Check |
|---|---|
| R1 | Path is `rules-root/<id>.md` — the file's parent is the rules root. |
| R2 | Frontmatter parses as YAML. |
| R3 | Required keys present: `schema`, `id`, `statement`, `status`, `modality`, `check`, `date`. |
| R4 | `id` matches `^[a-z0-9]+(-[a-z0-9]+)*$` **and** equals the filename base. |
| R5 | `status` ∈ {`draft`, `active`, `superseded`, `retired`}. |
| R6 | `modality` ∈ {`require`, `forbid`, `prefer`, `allow`}. |
| R7 | `statement` is a single non-empty line ≤ 200 chars; its phrasing matches `modality` (**warn**). |
| R8 | `paths` / `triggers` / `tags`, when present, are lists of non-empty strings. |
| R9 | `check` is `manual`, `review`, or a repo-relative path that exists on disk. |
| R10 | Every `overrides` / `supersedes` entry resolves to an existing rule id. |
| R11 | `status: superseded` ⟺ some `active` rule lists this id in `supersedes`. |
| R12 | `updated`, when present, matches `^\d{4}-\d{2}-\d{2}$` and is ≥ `date`. |
| R13 | `schema` is exactly `agent-rules/v1`. |
| R14 | No top-level keys outside the schema (**warn** — tolerated, not fatal). |
| R15 | `id` is unique within the rules tree. |
| R16 | Body contains `## Rationale`, `## Check`, and `## Exceptions` headings. |

R1–R15 are checkable from frontmatter alone; R16 is the one check that requires
reading a body, and it runs only in explicit validation mode.

## Lifecycle

- **`draft` → `active`** — on user confirmation. A `draft` rule is not in force
  and must not be cited as a constraint.
- **`active` → `superseded`** — a successor rule (new `id`) replaces it and names
  it in `supersedes`. The old file stays.
- **`active` → `retired`** — withdrawn with no successor, because the failure
  mode it guarded no longer exists. The file stays.
- **In-place edits** are for wording and clarification only. A change to
  `statement`'s normative content or to `modality` requires a **new `id`** plus
  `supersedes`, so "which rule was in force when X happened" stays answerable.

## Versioning

The schema version is `agent-rules/<n>`. Current: **v1**.

- **Additive change** (a new optional key; a value old readers ignore): may keep
  the version when it cannot mislead an older reader. Bump if in doubt.
- **Breaking change** (rename, removal, or repurposing of a key; a new/changed
  `modality` or `status` vocabulary; a change to precedence order; a tightened
  constraint existing rules could violate): new version, shipped with an
  explicit migration note, and this document updated **before** writers emit the
  new version.
- **Invariant across versions:** the flat `<id>.md` layout, `id`↔filename
  equality (R4), and frontmatter-only filterability are permanent. Precedence
  may be *extended* with new steps appended, never reordered.

## Out of scope for v1 (future extension candidates)

Each would be a *versioned* addition, not a one-off field:

- **Rule sets / composition** — grouping or importing rules (`ruleset:`,
  `includes:`). Flat files plus `tags` cover v1.
- **Per-tool adapters** — emitting `.cursor/rules/*.mdc`,
  `.github/copilot-instructions.md`, or similar from the canonical rules. A
  generator, not a schema field.
- **Enforcement wiring** — hooking `check` into a pre-tool hook. Harness work
  that consumes this schema.
- **Violation telemetry** — recording when a rule was breached, which would let
  rules be retired on evidence rather than judgment.
- **Non-constraint project knowledge** — durable facts and conventions that are
  not prohibitions or obligations. A different document family, not an extension
  of `agent-rules`.

## Design decisions

Recorded so a future reader does not relitigate them:

1. **`statement` lives in frontmatter, not only in the body.** Rules are tiny and
   the clause *is* the payload; a frontmatter-only scan can then tell an agent
   what every rule requires without opening a file. Corollary: if a rule cannot
   be stated in one line, it is a skill wearing a rule's clothes.
2. **Everything is a scalar or a list.** A nested `scope:` mapping would degrade
   to "key present" in the stdlib reader and make scope unfilterable.
3. **`check` is required, even when `manual`.** Mirrors `writing-quality-contract`,
   where every clause must map to a check or it is unverified prose.
4. **Exceptions are `allow` rules, not a field.** Auditable, scoped, and
   precedence-resolved rather than silently appended.

## Consumers of this spec

| Consumer | Obligation |
|---|---|
| `writing-agent-rules` skill | Emit only conformant v1 rules; classify `modality`; force an explicit scope; require a `check`; detect conflicts and supersede rather than duplicate; write the mandated body sections. |
| `scripts/scan_rules.py` | Read frontmatter only in scan mode; filter on `status`/`modality`/`paths`/`triggers`; validate R1–R16 and report cross-rule lints. |
| `init-agent-harness` | Scaffold `.agents/rules/`, write its README, and point AGENTS.md at it. |

Changes to the skill or scanner that alter rule structure are changes to this
schema and must go through the versioning policy above.

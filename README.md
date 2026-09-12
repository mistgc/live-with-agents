# Live with Agents

A personal collection of reusable **agent Skills** for working and living with coding agents. The repo is a mix of:

- **Skills** (`skills/`) — self-authored capabilities that teach agents how to do something, written as `SKILL.md`.
- **Curated third-party skill sets** (`awesome-skills/`) — vendored as git submodules.

## Repository layout

```
.
├── skills/                          # Self-authored agent skills
│   ├── init-agent-harness/          # Bootstrap a project's agent-document workflow
│   ├── document-translator/         # Markdown EN/ZH document translator skill
│   ├── conventional-commit/         # Write Conventional Commits messages (prompt + workflow)
│   ├── writing-quality-contract/     # Write a module's quality contract (pre/post/invariants)
│   ├── writing-project-notes/       # File concluded work as typed notes (implemented/deprecated/fixed/rejected/archived)
│   ├── retrieving-project-notes/    # Retrieve notes: scan frontmatter, then read only the relevant ones
│   ├── writing-agent-rules/         # Turn a stated constraint into a scoped, checkable rule
│   └── devfeat/                     # (placeholder) guided feature development
├── awesome-skills/                  # Curated third-party skill collections (submodules)
│   └── obsidian-skills/             #   Obsidian skills by kepano (github.com/kepano/obsidian-skills)
├── docs/                            # Reference docs (state-lifecycle, project-notes-schema, agent-rules-schema)
├── .agents/                         # This repo's own harness: notes/, rules/, git-ignored local/, skills/ symlinks
└── scripts/                         # (empty) helper scripts
```

## Skills

### `skills/init-agent-harness`

A **manual-only** skill (never auto-invoked) that sets up a project's `AGENTS.md` with *output-constraint* rules and a `.agents/` harness. It encodes three rules for how agents should treat documents:

1. **Store** every generated document (plan/spec/PRD/reports) under the git-ignored `.agents/local/`.
2. **File** concluded work as typed notes under `.agents/notes/` — `implemented/` (features live in the code), `deprecated/` (removed/superseded), `fixed/` (resolved defects), `rejected/` (declined proposals), `archived/` (history snapshots).
3. **Consult** those notes when searching the repo or answering questions, falling back to the repo alone when no note applies.

It also establishes the `<datetime>-<topic>.md` filename convention for generated working docs and the recursive `.gitignore` rules needed to keep `.agents/local` structure tracked while ignoring its contents.

The skill treats `docs/state-lifecycle.md` and `docs/project-notes-schema.md` as the authoritative references behind the note rules, bundling its own copies under `skills/init-agent-harness/references/`. Rather than copy those into the target repo's `docs/`, it writes a `.agents/notes/README.md` that orients a reader in the notes folder and links both docs by relative path, and the AGENTS.md note rules point at that README so future agents reach the docs whenever they file, retrieve, or classify a note.

### `skills/document-translator`

Translates a Markdown document into a language-suffixed sibling file in the same directory, keeping the filename `<title>` unchanged. The default target flips with the source language: a Chinese doc becomes `<title>.en.md`, an English doc becomes `<title>.zh.md`; the user may override the target (e.g. `<title>.ja.md` for Japanese). Code blocks, links, frontmatter, and other identifiers are preserved verbatim — only prose is translated.

### `skills/conventional-commit`

Guides an agent through writing a [Conventional Commits](https://www.conventionalcommits.org/) message: it inspects `git status` / `git diff`, stages the change, and constructs a `type(scope): description` message from the allowed type set (`feat`, `fix`, `docs`, `refactor`, …), with an optional body and footer (e.g. `BREAKING CHANGE:` or issue references), then runs the commit.

### `skills/writing-quality-contract`

A **quality-contract** skill that agents can auto-invoke when a module's behavior carries implicit assumptions worth pinning down — before implementing a non-trivial operation or stateful module, or when refactoring code whose interface rules are unclear. It writes a precise, verifiable statement of those assumptions in three buckets:

1. **Preconditions** — what the caller must guarantee before calling.
2. **Postconditions** — what the module guarantees on return.
3. **Invariants** — what holds across the module's whole lifetime.

Each clause is a predicate precise enough to turn into an `assert` with zero further decisions, and every clause maps to a runnable check (assert or test). The skill authors the contract only — where the document is saved follows the surrounding context, not a hard-coded path.

### `skills/writing-project-notes`

Files **concluded** work as durable, retrievable notes, complementing `init-agent-harness`'s note workflow. It collects the surrounding context, locates the requirement's PRD, quality-contract, and SPEC documents, and **auto-classifies** the outcome against the current code into one of five types on two tracks:

1. **`implemented`** — a feature is live in the code (current-truth; syncs with code).
2. **`deprecated`** — a feature was removed or superseded (current-truth; records the removal commit).
3. **`fixed`** — a reported defect is now repaired in the code (current-truth).
4. **`rejected`** — a proposed design or implementation was explicitly declined.
5. **`archived`** — a step in how the repo reached its current shape, for AGENT recall only (history; not kept in sync).

Each note is a Markdown file with normalized YAML frontmatter (`schema`, `type`, `date`, `topic`, `title`, `module`, `tags`, `sources`, `commits`) and a `yyyy-mm-dd-topic.md` filename, filed under the repo's `.agents/notes/{implemented,deprecated,fixed,rejected,archived}/` so future sessions can retrieve by filename or grep the frontmatter. The schema is versioned (`project-notes/v2`, see `docs/project-notes-schema.md`).

### `skills/retrieving-project-notes`

Retrieves project notes **fast-first**: it scans only the YAML frontmatter of every note in the tree (a stdlib-only `scan_notes.py` that prints a one-line-per-note table — file, date, type, title, tags, module — newest first) and then reads in full only the notes whose scan rows look relevant to the retrieval goal. The scan range is narrowed by **note type** (the five v2 types, incl. the current-truth vs history split), **date window**, or a **fuzzy topic/title match**; the script never reads note bodies. Retrieval ends with a synthesis that cites each note by path, and answers from the repo alone when no note is relevant.

### `skills/writing-agent-rules`

Turns a stated constraint into a durable, scoped **rule** on agent behavior — one flat file per rule at `.agents/rules/<id>.md`. It fixes the constraint as a single normative sentence in frontmatter (`statement:`), classified by **modality**: `require` / `forbid` (binding), `prefer` (a default deviable only with a stated reason), and `allow` (an explicit carve-out). It then forces the two things rule files usually omit — an **explicit scope** (`paths` / `triggers`, where absence means *global*, rendered `always`) and a **check** (a script path, or `manual`/`review`; silence is not an option).

Rules are keyed by a stable `id` and never deleted: a rule is **superseded** by a successor naming it in `supersedes`, or **retired**. A carve-out is itself an `allow` rule naming what it overrides, so every escape hatch is scoped, checked, and enumerable. Conflicts between live rules resolve deterministically — explicit `overrides`, then narrower scope — and an equal-specificity conflict between different modalities is reported as an **error** rather than silently decided.

The schema is versioned (`agent-rules/v1`, see `docs/agent-rules-schema.md`, bundled under the skill's `references/`), with conformance checks R1–R16 and a stdlib-only `scripts/scan_rules.py` that scans frontmatter, validates the tree, reports conflicts and dangling references, and regenerates the `.agents/rules/README.md` index. `init-agent-harness` scaffolds the rules directory and points `AGENTS.md` at it; this skill authors the rules.

## Third-party collections

### `awesome-skills/obsidian-skills` (git submodule)

Vendored from [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) for working with Obsidian vaults: Obsidian Flavored Markdown, Bases, JSON Canvas, vault CLI operations, and web-content extraction via Defuddle.

## Getting started

Clone with submodules:

```sh
git clone --recurse-submodules git@github.com:mistgc/live-with-agents.git
# or, if already cloned:
git submodule update --init --recursive
```

To reuse a skill in your own agent project, copy its folder (e.g. `skills/init-agent-harness/`) into your project's skills directory — most follow the [Agent Skills specification](https://agentskills.io/specification) and work across skills-compatible agents.

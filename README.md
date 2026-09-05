# Live with Agents

A personal collection of reusable **agent Skills** and **harness implementations** for working and living with coding agents. The repo is a mix of:

- **Skills** (`skills/`) — self-authored capabilities that teach agents how to do something, written as `SKILL.md`.
- **Harness implementations** (`templates/`) — reusable scaffolding that wires an agent into a project (rules, notes, output-constraint workflows).
- **Curated third-party skill sets** (`awesome-skills/`) — vendored as git submodules.

## Repository layout

```
.
├── skills/                          # Self-authored agent skills
│   ├── init-agent-harness/          # Bootstrap a project's agent-document workflow
│   ├── lwa-translator/              # Markdown EN⇄ZH document translator skill
│   └── devfeat/                     # (placeholder) guided feature development
├── templates/
│   └── project-structure-with-agents/   # Harness scaffold for a repo that works with agents
│       └── .agents/                     #   local/, notes/, rules/, skills/ skeleton
├── awesome-skills/                  # Curated third-party skill collections (submodules)
│   └── obsidian-skills/             #   Obsidian skills by kepano (github.com/kepano/obsidian-skills)
├── docs/                            # (empty) documentation
└── scripts/                         # (empty) helper scripts
```

## Skills

### `skills/init-agent-harness`

A **manual-only** skill (never auto-invoked) that sets up a project's `AGENTS.md` with *output-constraint* rules and a `.agents/` harness. It encodes three rules for how agents should treat documents:

1. **Store** every generated document (plan/spec/PRD/reports) under the git-ignored `.agents/local/`.
2. **Archive** concluded work as outcome-classified notes under `.agents/notes/` — `archived/` (implemented/user-reviewed), `fixed/` (resolved defects), `rejected/` (declined proposals).
3. **Consult** those notes when searching the repo or answering questions, falling back to the repo alone when no note applies.

It also establishes the `<datetime>-<topic>.md` filename convention and the recursive `.gitignore` rules needed to keep `.agents/local` structure tracked while ignoring its contents.

### `skills/lwa-translator`

Translates a Markdown document into a language-suffixed sibling file in the same directory, keeping the filename `<title>` unchanged. The default target flips with the source language: a Chinese doc becomes `<title>.en.md`, an English doc becomes `<title>.zh.md`; the user may override the target (e.g. `<title>.ja.md` for Japanese). Code blocks, links, frontmatter, and other identifiers are preserved verbatim — only prose is translated.

## Harness templates

### `templates/project-structure-with-agents`

The reference scaffold for a repository that works with agents. Provides the `.agents/` skeleton (with `.gitkeep` per level):

```
.agents/
├── local/          # git-ignored working docs (plans/, prd/, specs/, reports/)
├── notes/          # concluded work, classified by outcome (archived/, fixed/, rejected/)
├── rules/          # repo-specific agent rules
└── skills/         # repo-scoped skills
```

It ships with a `conventional-commit` skill that guides agents through writing Conventional Commits messages. The `init-agent-harness` skill copies from this template instead of hand-creating folders.

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

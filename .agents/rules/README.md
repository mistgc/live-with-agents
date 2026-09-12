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

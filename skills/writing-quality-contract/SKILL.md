---
name: writing-quality-contract
description: Use when a module's behavior carries implicit assumptions worth pinning down — before implementing a non-trivial operation or stateful module (contract-first), when refactoring or reverse-engineering existing code whose interface rules are unclear, or when asked to write a quality contract. Produces explicit, verifiable clauses — preconditions, postconditions, invariants — precise enough to be checked by asserts/tests. Skip for trivial helpers, or when the user only wants a spec/design doc.
---

# Write Quality Contract

## Overview

A **quality contract** states a module's implicit assumptions as explicit, verifiable rules in three buckets:

1. **Preconditions** — what the *caller* must guarantee before calling.
2. **Postconditions** — what the *module* guarantees when it returns.
3. **Invariants** — what holds across the module's whole lifetime.

Each clause is a **precise predicate** — named terms, no vague words — so a reviewer or a tool (assert / test) can check it with zero further decisions. The contract is its own artifact, distinct from a design doc, spec, or PRD.

## When to Use

- **Before implementing** a non-trivial operation or stateful module — write its contract first so the code implements stated rules rather than guesses.
- **Refactoring or reverse-engineering** existing code whose interface rules or hidden state assumptions are unclear — extract them into an explicit contract for review / safe change.
- The user explicitly asks to write / create / draft a quality contract, or to turn a module's hidden assumptions into preconditions / postconditions / invariants.

**When not to use:** the operation is trivial (a one-liner with an obvious contract — writing it adds noise); the deliverable is a design doc, spec, or PRD (write that instead); a code review without a contract output; or only a chat-level discussion of one function.

## Where the contract lives

This skill authors the contract only — it does **not** mandate a storage location. Save the resulting document wherever the context calls for: the project's conventions for contracts or docs, the surrounding agent harness, or the user's explicit choice. Ask if the destination isn't obvious.

## Steps

1. **Scope the module.** Name the module and list its **public entry points** (functions/methods/commands) plus the **state it owns** (fields, files, DB rows). The contract covers exactly this surface and nothing else — out-of-scope behavior is not the module's contract. State the module's one-line purpose, to be written at the top of the contract.

2. **Derive clauses per entry point.** For each public entry point write **Requires**, **Ensures**, and — only if the operation can error — **Failure**:
   - **Requires** names only caller-supplied inputs and pre-call state the caller controls. Breach means the *caller's* bug.
   - **Ensures** states what the module guarantees on normal return — outputs, state changes; may reference inputs/old state to express a relation.
   - **Failure** states what still holds when it aborts/raises (rolled back? partial writes? nothing?), if it can fail.

3. **Write module invariants.** Conditions true at rest and across *every* operation — before, during, and after each call. Put these at module level, not per call. Classic kinds: resource invariants, aggregate sums, structural validity, immutability.

4. **Make every clause verifiable.** Rewrite each clause as a precise boolean predicate: every term named and quantified, no vague words. **Test of precision:** a reviewer can turn the clause into an `assert` with zero new decisions. A clause that fits none of the three buckets (a quality goal, a UX preference, a design note) does **not** belong in the contract — record it elsewhere.

   | Banned | Fix |
   |---|---|
   | `correct`, `proper`, `works` | state what *correct* means (which output, which state) |
   | `valid input` | name the exact accepted set / range / format |
   | `fast`, `efficient`, `never corrupts` | a perf note outside the contract; name the real invariant instead |
   | "must not break existing behavior" | enumerate the behaviors that must survive |

5. **Turn clauses into checks.** For each clause make sure a runnable check exists or is added:
   - **Requires** → boundary assert, or a caller-side test that a violation is the caller's fault.
   - **Ensures** → assert on return, or a unit test asserting the post-state.
   - **Invariant** → checked before+after each public operation, or one test per invariant.
   Then cross-check: for **new** code, implement to satisfy the contract; for **existing** code, run each clause against the implementation and mark pass/fail — a failing clause means a bug in the code *or* a wrong contract; resolve which before finalizing.

6. **Write the contract** from this template:

   ```markdown
   # <module> — Quality Contract

   - Date: <yyyy-mm-dd> · Module: <module> · Scope: <entry points + owned state>
   - Purpose: <one line>

   ## Entry points

   ### `<public operation>`
   - **Requires:** <predicate over caller inputs / pre-call state>
   - **Ensures:** <predicate over outputs / post-call state>
   - **Failure:** <guarantees when it fails> *(only if it can fail)*

   ## Invariants
   - <always-true predicate>

   ## Checks
   | # | Clause | Checked by |
   |---|---|---|
   | 1 | Requires · `<op>` | assert at caller boundary / test ... |
   ```

   Example clause set for a money-transfer operation `transfer(from, to, amount)`:
   - **Requires:** `from` and `to` are distinct open accounts; `amount` is an integer ≥ 0 and ≤ `balance(from)`.
   - **Ensures:** `balance(from) = old(from) − amount`; `balance(to) = old(to) + amount`.
   - **Invariant:** the sum of `balance(a)` over all accounts is unchanged by every operation; `balance(a) ≥ 0` for every account `a`.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Turning a simple feature task into a full contract | This is a judgment skill, not a pipeline — the contract earns its keep when the interface or state rules are non-trivial. For trivial work, say so and skip the ceremony |
| Contract drifts into prose / a spec | Keep it clause-per-bucket predicates; non-contract notes go elsewhere |
| Hard-coding a storage directory | Storage is context-dependent — follow the project's conventions or ask |
| Preconditions promising module behavior, or postconditions demanding caller debt | Requires = caller's job; Ensures = module's job; split responsibilities |
| Vague predicates that need a second question to check | Run the assert test (Step 4); name every term |
| Invariants written per-call instead of module-level | Invariants hold across the lifetime — one section at module level |
| Clauses never turned into checks | Step 5: every clause must map to an assert or test, else it's unverified prose |
| Failing to check existing code against the contract | Run each clause pass/fail against the implementation; reconcile before finalizing |

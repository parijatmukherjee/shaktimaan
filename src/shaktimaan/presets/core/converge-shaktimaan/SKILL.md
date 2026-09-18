---
name: "converge-shaktimaan"
description: "Assess the current codebase against the feature's spec, plan, and tasks, then append any remaining unbuilt work as new tasks to tasks.md so implement can complete it."
compatibility: "Requires .shaktimaan/ scaffolding (run `shaktimaan init` first)"
user-invocable: true
disable-model-invocation: false
model: sonnet
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before convergence)**:

- Check if `.shaktimaan/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_converge` key
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.shaktimaan/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `readme.sync` → `/readme-sync`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):

    ```text
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Goal.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:<command>` or `$<command>`). Emitting the block alone does not run the hook.

- If no hooks are registered or `.shaktimaan/extensions.yml` does not exist, skip silently

## Goal

Close the gap between what a feature's specification, plan, and tasks call for and what the
codebase currently implements. Read `spec.md`, `plan.md`, and `tasks.md` as the **sole
source of intent** (with the constitution as governing constraints), assess the current
state of the code, determine which requirements, acceptance criteria, plan decisions, and
existing tasks are unmet, incomplete, or only partially satisfied, and **append each piece
of remaining work as a new, traceable task** at the bottom of `tasks.md` so that
`/implement-shaktimaan` can complete it. This command MUST run only after
`/implement-shaktimaan` has run on the current `tasks.md`, and after `/tasks-shaktimaan` has produced a complete `tasks.md`.

This is **not** a diff tool and does **not** track changes. It assesses the present state
of the code relative to the feature's artifacts — no git, no branch comparison, no history.

## Operating Constraints

**APPEND-ONLY, NEVER REWRITE**: The command's only writes are appending a new
`## Phase N: Convergence` section to `tasks.md`, and (Step 7a) appending or updating this
feature's own bullet(s) in the requirements-status file (from `.shaktimaan/config.yml`'s
`requirements_status_file`)'s `## Deferred / Gap follow-ups` section, if that file exists.
It MUST NOT:

- modify `spec.md` or `plan.md` in any way;
- rewrite, renumber, reorder, or delete any existing task (including tasks from a prior
  Convergence phase);
- modify, create, or delete any application code — completing the appended tasks is the
  job of `/implement-shaktimaan`.

When the codebase already satisfies everything, the command MUST leave `tasks.md`
**byte-for-byte unchanged** (no empty Convergence header) and report a clean result.

**Constitution Authority**: The project constitution (`.shaktimaan/memory/constitution.md`) is
**non-negotiable**. Code that violates a MUST principle is the highest-severity finding and
produces a corresponding remediation task. If the constitution is an unfilled template,
skip constitution checks gracefully rather than failing.

## Execution Steps

### 1. Initialize Convergence Context

Run `.shaktimaan/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks` once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS. Derive absolute paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- CONSTITUTION = `.shaktimaan/memory/constitution.md` (if present)
If `spec.md`, `plan.md`, or `tasks.md` is missing, STOP with a clear, actionable message naming the
prerequisite command to run (`/specify-shaktimaan` for a missing spec, `/plan-shaktimaan` for a missing plan,
`/tasks-shaktimaan` for missing tasks). Do not produce partial output.
For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From spec.md:**

- Functional Requirements (FR-###)
- Success Criteria (SC-###) — include only items requiring buildable work; exclude
  post-launch outcome metrics and business KPIs
- User Stories and their Acceptance Scenarios
- Edge Cases (if present)

**From plan.md:**

- Architecture/stack choices and technical decisions
- Data Model references
- Phases and named touch-points (files/components the plan says will be created or edited)
- Technical constraints

**From tasks.md:**

- Task IDs (to compute the next ID and next phase number)
- Descriptions, phase grouping, and referenced file paths

**From constitution (if not an unfilled template):**

- Principle names and MUST/SHOULD normative statements

### 3. Build the Intent Inventory

Create an internal model (do not echo raw artifacts):

- **Requirements inventory**: one stable key per FR-### / SC-### / user-story acceptance
  scenario (e.g. `US1/AC2`), plus the plan decisions and constitution principles that
  impose buildable obligations.
- **Code-scope map**: from the file paths named in `plan.md` and `tasks.md`, plus a keyword
  search for the concepts each requirement describes, derive the set of source files and
  components in scope for assessment. Bound the assessment to these — do **not** infer
  scope beyond what the artifacts define.

### 4. Assess the Codebase and Classify Findings

For each item in the intent inventory, inspect the current code in scope and produce a
`Finding` only where there is a gap. Classify every finding by **gap type**:

- **`missing`**: the required work is absent from the code entirely.
- **`partial`**: the work exists but does not yet fully satisfy the requirement /
  acceptance criterion / plan decision.
- **`contradicts`**: the code does something that conflicts with stated intent or a
  constitution MUST principle.
- **`unrequested`**: the code contains work not called for by the spec, plan, or tasks
  (surfaced for awareness — converge does **not** delete code, it only appends a task to
  review/justify or remove it).

Each `Finding` records: a stable id, the `source-ref` it traces to, the `gap-type`, a
severity, and a short human-readable description with the evidence (the file/area observed).

**Edge cases:**

- **Little or no code yet**: treat the entire specified scope as `missing` remaining work
  rather than failing.
- **Nothing remains**: produce zero findings and follow the converged branch in Step 7.

### 4a. Verify Test Coverage

Independently verify test coverage — do **not** rely on whether a coverage-related task (e.g.
"close coverage gap", "run coverage") is checked off in `tasks.md`; a checked box does not by
itself prove the number is real.

- The constitution's Principle VIII sets this project's threshold explicitly: **100% line and
  branch coverage**, per stack's standard coverage tool, enforced as a CI gate — not an
  advisory number to be "close to" or "mostly at". Treat anything below 100% as a gap; there is
  no partial-credit threshold to negotiate. (A future amendment to Principle VIII, or a
  different threshold stated in `plan.md`/`tasks.md` for a non-constitution reason, supersedes
  this default — always read the constitution fresh rather than hardcoding 100% blindly.)
- Actually run each in-scope package's coverage command (e.g. `pnpm -r test -- --coverage`, or
  whatever `plan.md`/`tasks.md` specifies) — do not infer the result from a prior run, a task
  checkbox, or code review alone.
- Parse the resulting report for line/branch coverage per package in scope.
- For any package below 100% (or the applicable threshold from the bullet above): produce a
  Finding (`gap-type: partial`, `source-ref`: Constitution VIII or the relevant NFR) naming the
  actual percentage and the specific uncovered files/lines from the report.
- For any coverage exclusion found in code or config (ignore comments, blanket directory
  excludes): confirm it carries the one-sentence justification the constitution requires. An
  exclusion with no justification, or a blanket directory-level exclusion, is itself a Finding
  (`gap-type: contradicts`).
- If the coverage command fails to run at all (missing deps, broken config, script not found):
  that failure is a Finding in its own right (`gap-type: missing`) — coverage must be verified,
  not assumed passing.
- Severity for every coverage Finding follows Step 5's rule below: CRITICAL when the coverage
  requirement is a constitution MUST principle.

### 5. Assign Severity

- **CRITICAL**: violates a constitution MUST principle, or a `missing`/`contradicts` gap
  that blocks baseline functionality of a P1 user story.
- **HIGH**: a `missing` or `partial` gap on a core functional requirement or acceptance
  criterion.
- **MEDIUM**: a `partial` gap on a secondary requirement, or an `unrequested` addition with
  unclear justification.
- **LOW**: minor partial gaps, polish, or low-risk `unrequested` additions.

### 6. Present the In-Session Findings Summary

Before appending anything, output a compact, severity-graded summary (no file writes yet):

## Convergence Findings

| ID | Gap Type | Severity | Source | Evidence | Remaining Work |
|----|----------|----------|--------|----------|----------------|
| F1 | missing  | HIGH     | FR-008 | Example: no append-only guard detected in path/to/module.py when writing tasks.md | Add append-only enforcement |

**Summary metrics:**

- Requirements / acceptance criteria checked
- Plan decisions checked
- Constitution principles checked (or "skipped — template")
- Test coverage: command(s) run, measured percentage per package, and pass/fail against the
  required threshold (or "skipped — no coverage requirement found")
- Findings by gap type (missing / partial / contradicts / unrequested)
- Findings by severity

### 7. Append Convergence Tasks (or report converged)

**If there are one or more actionable findings** (`tasks_appended` outcome):

Append to the **end** of `tasks.md`, per the append contract:

1. Scan all existing task IDs; let `M` be the maximum. Determine the next phase number `N`
   (highest existing phase + 1).
2. Write a single new section header `## Phase N: Convergence`.
3. Emit one checklist item per actionable finding, ordered CRITICAL/HIGH first, assigning
   zero-padded IDs `T{M+1:03d}, T{M+2:03d}, …`:

   ```markdown
   - [ ] T042 <imperative description> per <source-ref> (<gap-type>)
   ```

   `<source-ref>` traces the task to its origin: e.g. `FR-003`, `SC-002`,
   `US1/AC2`, `plan: storage decision`, `Constitution II`.

   `<gap-type>` is one of `missing`, `partial`, `contradicts`, `unrequested`.

   Constitution-violation tasks MUST be emitted first and described as
   `CRITICAL`.
4. Never reuse or renumber existing IDs. If a prior Convergence phase exists, add a new,
   separately-numbered one below it — do not touch the old one.

**If there are no actionable findings** (`converged` outcome):

- Do **not** modify `tasks.md` at all — no empty phase header.
- Report: **"✅ Converged — the implementation satisfies the spec, plan, and tasks."**
- Include the summary counts of what was checked.

### 7a. Flag Requirement Gaps for Future Specs

The tasks appended in Step 7 close gaps **within this feature's own scope**. Separately, check
for requirement gaps that fall **outside** this feature's scope — i.e., an FR-/NFR- ID this
feature's spec cites (per the requirements-status file — from `.shaktimaan/config.yml`'s
`requirements_status_file` — if present) that this convergence run confirms is only partially
or intentionally not fully satisfied by design (explicitly narrowed, deferred, or scoped down —
not simply closed by the tasks just appended).

- If the requirements-status file does not exist, skip this step silently — it's created by the
  `requirements-sync-shaktimaan` skill, not by this command.
- If it exists, ensure it has a `## Deferred / Gap follow-ups` section (create it, after the main
  table and any "Not yet referenced" section, if missing).
- For each such ID, add or update one bullet: `- FR-xxx: <what remains unaddressed and why> (surfaced by convergence on specs/<NNN>-<slug>)`.
- Never remove another feature's bullet from this section — only add or update the one(s)
  matching this feature's convergence run. Removal happens only when `/specify-shaktimaan` folds an
  entry into a new feature's scope (that skill's own responsibility).
- This is the only file this command writes to outside `tasks.md`. It does not touch that file's
  Status column or main table — those remain owned by `requirements-sync-shaktimaan`.

### 8. Provide Next Actions (Handoff)

- On `tasks_appended`: state how many tasks were appended under which phase, and recommend
  running `/implement-shaktimaan` to complete them; note that a follow-up converge
  run will find fewer or no remaining items.
- On `converged`: recommend proceeding to review / opening a PR. No further implement pass
  is needed for this feature's specified scope.
- If Step 7a recorded any `## Deferred / Gap follow-ups` bullets, state how many and note that the
  next `/specify-shaktimaan` run will surface them for consideration when scoping the next feature.

### 9. Check for extension hooks

After producing the result, check if `.shaktimaan/extensions.yml` exists in the project root.

- If it exists, read it and look for entries under the `hooks.after_converge` key
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.shaktimaan/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- Report the convergence outcome (`converged` or `tasks_appended`) in-session before listing
  any hooks, so users can decide whether to run optional follow-up commands.
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `readme.sync` → `/readme-sync`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):

    ```text
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

  - **Mandatory hook** (`optional: false`):

    ```text
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:<command>` or `$<command>`). Emitting the block alone does not run the hook.

- If no hooks are registered or `.shaktimaan/extensions.yml` does not exist, skip silently

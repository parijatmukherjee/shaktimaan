---
name: "requirements-sync-shaktimaan"
description: "Use when a spec-kit-shaped feature spec (specs/NNN-slug/) is created or updated, or when asked for this project's requirements delivery status, to trace specs back to requirement IDs and keep the requirements-status file current"
model: sonnet
---

# Reconciling specs against the requirements file

This project's requirements (`requirements_file`, from `.shaktimaan/config.yml`) are the
**immutable-per-version requirement source**. The `specs/<NNN>-<slug>/spec.md`, `plan.md`,
`tasks.md` files are the **delivery mechanism** for a given slice of those requirements. This
skill keeps the two connected without letting either drift silently out of sync.

## When a new or updated spec appears

1. Read `.shaktimaan/config.yml` for `requirements_file` and `requirements_status_file`.
2. Read `specs/<NNN>-<slug>/spec.md` (and `plan.md` if present).
3. Search `requirements_file` for every requirement ID that spec's described behavior implements
   or partially implements. Be specific — cite IDs, don't summarize.
4. **If the spec describes behavior with no matching requirement:** stop and flag it to the
   user. Either it's a legitimate new requirement — use `update-requirements-shaktimaan` to propose
   adding it before treating it as in scope — or it's scope creep relative to the requirements
   file — surface that explicitly rather than quietly implementing it. Do not invent a
   requirement mapping just to make the spec look covered.
5. Update `requirements_status_file` (create it on first use — see format below). Add or update
   one row per requirement ID the spec touches.
6. Use `feature-tracker-shaktimaan` to roll this up: find the feature area(s) that own the
   requirement IDs just touched, and move that area's status forward if warranted (e.g. Not
   Started → In Progress the first time a spec targets it). Don't mark an area Delivered from
   this step alone.

## requirements_status_file format

Create lazily — only rows for IDs some spec has actually touched. Table columns:

| ID | Requirement (short) | Status | Spec | Notes |
|---|---|---|---|---|

- **Status** is one of: `Not Started`, `In Progress`, `Done`, `Blocked`.
- **Spec** links to `specs/<NNN>-<slug>/spec.md` (relative path).
- **Notes** captures anything a reviewer needs (partial coverage, deviation from the wording and
  why, follow-up needed).
- One requirement ID may span multiple specs (list them comma-separated) if a large requirement
  is delivered incrementally.

### `## Deferred / Gap follow-ups` section

A separate section, after the main table, owned jointly by `converge-shaktimaan` (which appends
to it) and `specify-shaktimaan` (which reads it and removes an entry once folded into a new
feature's scope). Format: one bullet per gap, `- <ID>: <what remains unaddressed and why>
(surfaced by convergence on specs/<NNN>-<slug>)`. This skill doesn't write to this section
directly, but when reconciling a spec that folded in a previously deferred ID, confirm the
corresponding bullet was removed — if it wasn't, remove it as part of the sync.

## What this skill does NOT do

- It does not edit `requirements_file` — that file's content changes only via
  `update-requirements-shaktimaan`, with explicit user confirmation for new requirements.
- It does not mark something `Done` from the spec alone — only mark `Done` once told the
  implementation is merged/verified.
- It does not update `feature_tracker_file` directly — that's owned by
  `feature-tracker-shaktimaan` (invoke it as step 6 above).

## When asked for "requirements status" or "what's left"

For a quick, feature-area-level answer, read `feature_tracker_file` instead — it's always
present and doesn't require any spec work to exist yet. For per-requirement detail, read
`requirements_status_file` if present, cross-reference against `requirements_file`, and report:
covered-by-some-spec vs. not yet referenced, grouped by Priority. If the status file doesn't
exist yet, say so — it means no spec work has been reconciled yet, not that everything is done.

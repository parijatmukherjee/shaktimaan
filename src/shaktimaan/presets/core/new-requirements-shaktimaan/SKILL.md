---
name: "new-requirements-shaktimaan"
description: "Use when bootstrapping a project's requirements from scratch — the first time this project defines its requirements file. Interactively elicits requirements via clarifying questions, writes a versioned structured requirements file, and seeds the feature-tracker file's initial feature-area breakdown."
model: sonnet
---

# Bootstrapping requirements from scratch

This is the **first-time creation** flow — for ongoing edits after `requirements_file` exists,
use `update-requirements-shaktimaan` instead.

## Steps

1. Read `.shaktimaan/config.yml` for `project_name`, `requirements_file`, and
   `feature_tracker_file`. If the config file doesn't exist, **STOP** and tell the user to run
   `shaktimaan init` first.
2. Check whether `requirements_file` already exists. If it does, **STOP** and tell the user to
   use `update-requirements-shaktimaan` for edits instead — this flow only runs once, to create it.
3. Take the user's freeform description of what they want to build — however much or little
   detail they gave.
4. Ask clarifying questions where the input is ambiguous or underspecified: actor/user types,
   MVP vs. later scope, anything with multiple reasonable interpretations. Don't over-ask — only
   ask what materially changes scope or structure. Present them together, then wait for answers.
5. Organize the elicited requirements into capability areas (feature areas) — group related
   behaviors together (e.g. "user identity and access," "core workflow"). Use the same structure
   `update-requirements-shaktimaan` and `feature-tracker-shaktimaan` expect going forward: functional
   and non-functional requirements as separate ID namespaces (`FR-xxx`, `NFR-xxx`), sequential
   within each area's number block, each tagged **MVP** / **Phase 2** / **Later** priority.
6. Write `requirements_file`:
   - A short overview section (what the project is, 2-3 sentences, using `project_name`).
   - Priority definitions (MVP / Phase 2 / Later — the same three tiers `update-requirements-shaktimaan`
     expects).
   - One functional-requirement table per capability area.
   - A non-functional-requirements section, same area-grouped structure.
   - A version header, starting at **v1.0.0** — this is the first version;
     `update-requirements-shaktimaan` owns bumping it from here on.
   - A Changelog section with one entry: "v1.0.0 — initial requirements."
7. Write `feature_tracker_file` — the initial feature-area status snapshot: one row per
   capability area from steps 5/6, all starting at status **Not Started**, plus a Summary table
   and a per-area detail section for each. This is the same file `feature-tracker-shaktimaan`
   maintains going forward; this command only creates its first version.
8. Report both file paths and a short summary of the capability areas created.

## What this skill does NOT do

- Does not run if `requirements_file` already exists — that's `update-requirements-shaktimaan`'s job
  (editing, adding, reconciling, version-bumping).
- Does not create `specs/` directories or run any spec-kit-shaped command — that starts with
  `prioritise-next-shaktimaan` or `specify-shaktimaan` once requirements exist.
- Does not write `.shaktimaan/memory/constitution.md` — that's `constitution-shaktimaan`'s job.

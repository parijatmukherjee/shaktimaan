---
name: "update-requirements-shaktimaan"
description: "Use when adding, editing, removing, or reconciling requirements or acceptance scenarios in this project's requirements file, or when bumping its version"
model: sonnet
---

# Updating the requirements file

`requirements_file` (from `.shaktimaan/config.yml`) is the **single consolidated requirements
source** for this project. Do not recreate separate functional/non-functional/roadmap files
unless the project explicitly wants that structure — consolidation into one file is the default
this skill assumes.

## Before editing

1. Read the target section fully — don't pattern-match on one row. Requirement tables are
   typically grouped by capability area, with IDs sequential within that area's number block.
2. Check whether an existing requirement already covers the request. If it's a refinement,
   prefer tightening existing wording over adding a near-duplicate ID.

## ID rules

- Functional and non-functional requirement IDs are separate namespaces; never reuse a number
  across them or across sections.
- New requirement in an existing section → next unused sequential number in that section's
  block.
- **Never renumber or reuse a retired ID.** If a requirement is removed, strike it from the
  table and note the retirement + reason in the Changelog — the ID stays retired, not
  reassigned. Implementation code, tests, and specs may reference these IDs directly.
- Every requirement row needs a **Priority**: MVP / Phase 2 / Later, using whatever definitions
  are already stated near the top of the doc — don't invent new priority labels.

## Don't invent requirements unilaterally

If you're reconciling a spec or an implementation detail that implies behavior not covered by
any existing requirement, **stop and propose it to the user** before adding it — name the
proposed ID, section, wording, and priority, and let them confirm or adjust. Don't skip the
confirmation step just because the gap seems obvious.

## Acceptance-scenario coverage

Any new MVP or Phase 2 requirement that describes observable system behavior should get a
matching acceptance scenario, in Given/When/Then style:

```
**<SCENARIO-ID> — <short title>** `[<requirement IDs it verifies>]`
- Given <precondition>
- When <action>
- Then <observable, testable outcome>
```

Tag it with every requirement ID it verifies. Put it in the existing subsection for that
capability area (add a new one only if no existing area fits). `Later`-priority requirements may
skip this if there's nothing concretely testable yet, but note that explicitly rather than
silently omitting it.

## Versioning and changelog

The doc carries its own version, independent of the project's own release version. On any
change that adds, removes, or materially changes a requirement:

1. Bump the version (minor version for added/changed requirements; patch version only for pure
   wording/typo fixes that change no meaning).
2. Add a **Changelog** entry at the top describing what changed and why — follow the existing
   entry's format.
3. Do not edit past changelog entries to reflect new changes — append a new entry.

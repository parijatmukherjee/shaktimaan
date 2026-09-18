---
name: "prioritise-next-shaktimaan"
description: "Use when asked which feature to spec next, to prioritize the backlog, or for a ready-to-paste feature description for specify-shaktimaan — reads the project's requirements file, feature tracker, constitution, and any prior research, cross-references specs/ and the requirements-status file, and recommends the smallest slice that is a complete, production-deployable increment."
model: sonnet
---

# Prioritizing the next spec

This is a **read-only recommendation** skill — it doesn't write to any requirements, tracker, or
spec file. It answers "what should `specify-shaktimaan` build next?" by combining six sources of
truth, each owned elsewhere:

| Source | What it gives you |
|---|---|
| `requirements_file` (from `.shaktimaan/config.yml`) | Requirement IDs, Priority (MVP/Phase 2/Later), and the full requirement text |
| `feature_tracker_file` (from `.shaktimaan/config.yml`) | Feature-area status (Not Started/In Progress/Delivered/Blocked) + any "Recommended build order" section |
| `.shaktimaan/memory/constitution.md` | Governing principles that can reorder priority (if `constitution-shaktimaan` has been run) |
| `specs/` | Which slices already have a spec started or complete |
| `specs/*/research.md` | Technical findings/constraints from prior `plan-shaktimaan` runs that may affect what's feasible next |
| `requirements_status_file` (from `.shaktimaan/config.yml`) | Per-ID delivery status + any "Deferred / Gap follow-ups" section |

## Steps

1. Read `.shaktimaan/config.yml` for `requirements_file`, `feature_tracker_file`, and
   `requirements_status_file`. If any is unset, tell the user this project hasn't configured
   requirements tracking and stop — this skill has nothing to prioritize against without it.
2. Read `.shaktimaan/memory/constitution.md` if it exists. Note any principle that bears on
   prioritization order — e.g. a "security first" or "mobile first" principle, or explicit
   sequencing guidance. If the file doesn't exist, skip silently: not every project runs
   `constitution-shaktimaan` before this, and that's fine.
3. Read `feature_tracker_file` in full — its status summary and any "Recommended build order"
   section. This is the primary ranking signal; don't re-derive priority from scratch.
4. Read `requirements_file` in full — Priority tags, the full requirement text, and any
   acceptance-scenario section. The tracker tells you *which* area ranks first; this file is
   what steps 8 and 9 below actually test candidates against.
5. Read `requirements_status_file` if it exists, specifically any "Deferred / Gap follow-ups"
   section — requirement IDs a prior spec touched but didn't fully deliver. A gap that fits
   inside the next candidate feature area should be surfaced as something to fold in.
6. List `specs/` to see what already has a directory — don't recommend a slice that's already
   been speced. A tracker status of "In Progress" only means *some* spec exists for that area,
   not that the whole area is covered — check the spec's own completion state rather than
   skipping the area outright.
7. Read any `specs/*/research.md` files found in step 6. These carry technical findings or
   constraints discovered during a prior feature's planning — e.g. "library X doesn't support Y,"
   or a dependency that turned out to be harder than expected. If one bears on a candidate area
   for this recommendation (makes it easier, harder, or reveals a new dependency), factor it in.
8. Rank remaining candidates:
   - Prefer **Not Started** feature areas over **In Progress** ones.
   - Within Not Started areas, use the tracker's build-order signal first, then MVP-priority
     requirement count as a tiebreaker.
   - If a constitution principle from step 2 clearly favors one candidate over another (e.g. a
     security-first principle and a security-related area is in contention), let it move that
     area up — but say so explicitly in the recommendation rather than silently reordering.
   - An area marked **Blocked** is never the recommendation — surface the blocker instead and
     move to the next candidate.
   - If every Not Started area is blocked, say so explicitly rather than picking one anyway.
9. **Size the slice to the smallest unit that is still a complete, production-deployable
   increment.** Once step 8 picks a candidate feature area, do not default to speccing that
   area's entire requirement set in one spec. Using the requirement text read in step 4, find the
   smallest subset of its requirement IDs that clears all three bars below — this is a size
   *ceiling*, not a target:
   - **Deployable as-is**: shipping to production with only this subset built leaves no broken,
     half-wired, or misleading surface.
   - **Independently verifiable**: the subset maps to at least one acceptance scenario that can
     pass **end-to-end** on its own.
   - **No forward dependency on undelivered work**: nothing in the subset requires a requirement
     ID that lives in a Not Started or Blocked area to actually function (see step 10).
   - If no subset of the top-ranked area clears all three bars, say so and either scope the
     whole area or fall through to the next candidate from step 8.
10. Cross-check dependency shape: read the requirement text for the sized subset's IDs for
    references to other areas. If a dependency is itself Not Started or Blocked, either fold its
    minimum slice into this one or name the dependency order explicitly in the recommendation.
11. Produce a single recommendation (not a ranked list):
    - **Feature area(s)** and the exact requirement IDs in scope.
    - **Why this one now** — cite the build-order/priority signal, any constitution principle
      that influenced the choice, and why this subset is the smallest slice that still clears
      the three deployability bars.
    - **Any relevant prior research** from step 7 that affects how this slice should be scoped.
    - **What's explicitly left out and why**.
    - **Any Deferred / Gap follow-ups to fold in**, if step 5 found ones that plausibly fit.
    - **A ready-to-paste feature description** — 2-4 plain-language WHAT/WHY sentences, no
      implementation detail, so the user can hand it straight to `specify-shaktimaan`.

## What this skill does NOT do

- Does not run `specify-shaktimaan` itself, or create/modify any file under `specs/` or the
  requirements files — recommendation only.
- Does not re-litigate the tracker's status calls — if it looks stale, say so and suggest
  `feature-tracker-shaktimaan` rather than overriding it silently.
- Does not invent requirement IDs or requirement text — every claim traces back to
  `requirements_file`.
- Does not treat the constitution as an override of MVP-priority — it's a tiebreaker/signal
  among Not-Started candidates, not a reason to jump ahead of a Blocked or already-In-Progress
  area's own status.

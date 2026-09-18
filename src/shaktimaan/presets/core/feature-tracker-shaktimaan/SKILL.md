---
name: "feature-tracker-shaktimaan"
description: "Use when a feature area's delivery status changes in the feature-tracker file (Not Started / In Progress / Delivered / Blocked) — typically when spec work starts or completes for a feature area, or when asked for the current build/status snapshot of this project's features."
model: sonnet
---

# Updating the feature tracker

`feature_tracker_file` (from `.shaktimaan/config.yml`) is a **live status snapshot** over the
feature areas defined in `requirements_file`. It answers one question the requirements file
deliberately doesn't: *what's actually built right now?*

This is a different artifact from `requirements_status_file` (owned by
`requirements-sync-shaktimaan`) — know which one to touch:

| | Feature tracker | Requirements-status file |
|---|---|---|
| Granularity | Whole feature area | Individual requirement ID |
| Exists | Always (created up front) | Lazily, only once spec work begins |
| Source of truth for | "Is this feature area usable yet, and in what order should we build the rest?" | "Which spec delivers this requirement, and is it done?" |
| Updated by | This skill | `requirements-sync-shaktimaan` |

Update **both** when a spec both touches new requirement IDs and moves a whole feature area's
status — run `requirements-sync-shaktimaan` for the per-ID table, then this skill for the
feature-area rollup. They should never disagree about whether something is done.

## What never changes here

- Don't restate or edit requirement text — that lives only in `requirements_file`.
- Don't invent a new feature area or renumber the existing ones — they should mirror
  `requirements_file`'s own section structure exactly. If that file adds or removes a section,
  reconcile this file's summary and detail sections in the same change.
- The tracker carries no independent version number (unlike `requirements_file`) — it's a living
  snapshot, not a frozen per-version spec. Edit in place; no changelog entry needed.

## When to update a feature area's status

- **Not Started → In Progress**: a `specs/<NNN>-<slug>/` spec is created (or an existing one is
  picked up) whose requirement IDs fall in that feature area's range.
- **In Progress → Delivered (MVP)**: every MVP-priority requirement in that feature area is
  implemented and passing its acceptance scenario(s). Verify, don't infer from "the code looks
  done" — a spec being written, or tasks being marked done, is not by itself delivery.
- **Delivered (MVP) → Delivered (Full)**: the remaining Phase 2 / Later requirements in that
  area are also implemented and passing acceptance.
- **→ Blocked**: work on the area can't proceed. Note the blocker inline in that area's detail
  entry.
- Never mark an area "Delivered" from a spec or a task list alone — only once told (or having
  verified) the implementation is merged and its acceptance scenarios pass.

## How to update

1. Open `feature_tracker_file`.
2. Update the **Status** cell in the summary table row for the affected feature area(s).
3. Update the matching **Status** line in that area's detail section. Keep the two in sync.
4. If status moved because of specific spec work, it's fine to note which spec in the detail
   entry, but don't turn this into a second copy of `requirements_status_file`.
5. Leave any "Recommended build order" section alone unless the user asks to re-sequence it.

## When asked for "what's done" or "what's left"

Read `feature_tracker_file` directly and report by status group, MVP-priority areas first. If
finer per-requirement detail is needed, cross-reference `requirements_status_file` if it exists.

---
name: "readme-shaktimaan"
description: "Use when README.md needs to reflect current project state — typically as the before_commit_push extension hook, or when explicitly asked to refresh the README — keeps a standard GitHub front-door README (badges, setup instructions, feature-status table) in sync with the project's manifest and the feature-tracker file."
model: haiku
---

# Keeping README.md current

`README.md` is the **GitHub front door**. Keep it smaller than any fuller project documentation
— condense, don't copy.

## What README.md contains, in order

1. **Title + one-line description** — from the project's manifest file (`package.json`,
   `pyproject.toml`, etc. — whichever this project uses).
2. **Badges row**:
   - **Build** — the real CI status badge for this project's CI workflow, if one exists. Derive
     `<owner>/<repo>` from `git remote get-url origin` — never hardcode it.
   - **Code quality** — a **static** badge naming whatever formatting/lint tooling is actually
     configured. Do **not** fabricate a live quality/coverage score badge for a service that
     isn't actually integrated with this repo.
3. **Overview** — 2-3 sentences condensed from the project's fuller documentation, if one
   exists. Paraphrase for a GitHub skimmer; don't paste that text verbatim.
4. **Setup / run instructions** — derived from the project's actual build/run/test scripts. Keep
   this in sync with whatever scripts actually exist.
5. **Feature status** — if `feature_tracker_file` (from `.shaktimaan/config.yml`) exists, a
   condensed table: just Feature Area and Status columns. Sort Delivered first, then In
   Progress, then Not Started, with any Blocked area called out. Link to the full file rather
   than reproducing it.
6. **Links** — to any fuller project documentation and the requirements file, if they exist.

## Steps

1. Read `.shaktimaan/config.yml` for `project_name` and `feature_tracker_file`.
2. Read the project's manifest file for name/description/scripts.
3. If `feature_tracker_file` is set and exists, read its status summary table.
4. Run `git remote get-url origin` to derive `<owner>/<repo>` for the CI badge URL.
5. If `README.md` doesn't exist, create it with the full structure above. If it exists, update
   only the sections this skill owns — badges, overview, setup instructions, and the
   feature-status table — in place. Leave any other human-written content untouched.
6. Keep it terse. This is a landing page, not documentation.

## What this skill does NOT do

- Does not duplicate fuller project documentation — condenses it, never copies it verbatim.
- Does not fabricate a live code-quality or coverage badge for a service that isn't actually
  integrated with this repo.
- Does not modify `feature_tracker_file` or any other requirements file — read-only there.

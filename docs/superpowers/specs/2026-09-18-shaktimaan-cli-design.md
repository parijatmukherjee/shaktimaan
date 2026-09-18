# Shaktimaan CLI — design

**Status:** approved, pending implementation plan
**Date:** 2026-09-18

## What this is

A personal, reusable Spec-Driven Development (SDD) toolkit: a Python CLI
(`shaktimaan`) that scaffolds a `specify → clarify → plan → tasks → analyze
→ checklist → implement → converge` workflow into any project, as Claude
Code skills. Same workflow shape as [github/spec-kit](https://github.com/github/spec-kit)
(MIT), clean-room implementation, own command names, own extras.

Not in scope for v1: any AI agent other than Claude Code. Spec-kit supports
several (Codex, Gemini, Copilot, ...); shaktimaan targets Claude Code only
until there's a second consumer that needs something else.

## Command set

All commands are Claude Code skills, one directory per command
(`.claude/skills/<name>/SKILL.md`), installed into the target project by
`shaktimaan init`.

**Core — from spec-kit's workflow, renamed:**

| Command | Purpose |
|---|---|
| `specify-shaktimaan` | Create/update the feature spec from a natural-language description |
| `clarify-shaktimaan` | Ask up to 5 targeted clarification questions on an underspecified spec, encode answers back into it |
| `plan-shaktimaan` | Run the implementation-planning workflow to produce design artifacts (plan.md, data-model.md, contracts/, etc.) |
| `tasks-shaktimaan` | Generate a dependency-ordered tasks.md from the available design artifacts |
| `analyze-shaktimaan` | Non-destructive cross-artifact consistency check across spec.md/plan.md/tasks.md |
| `checklist-shaktimaan` | Generate a custom requirements-quality checklist for the current feature |
| `implement-shaktimaan` | Execute tasks.md phase-by-phase, TDD-first, with progress tracking |
| `converge-shaktimaan` | Assess the built code against spec/plan/tasks; append any remaining gap as new tasks |
| `taskstoissues-shaktimaan` | Convert tasks.md into dependency-ordered GitHub issues |
| `constitution-shaktimaan` | Create/update the project constitution (governing principles) |

**Original additions, folded in as core:**

| Command | Purpose |
|---|---|
| `commit-push-shaktimaan` | Stage-by-name, commit, push, with a configurable git identity and commit-message convention (no forced co-author trailer) |
| `prioritise-next-shaktimaan` | Read the requirements bundle + build-order + existing specs, recommend the smallest production-deployable next slice |

**Requirements-tracking bundle (always included — see Open question below):**

| Command | Purpose |
|---|---|
| `requirements-sync-shaktimaan` | Trace a spec's requirement IDs against the PRD, keep a per-ID delivery-status file current |
| `feature-tracker-shaktimaan` | Roll per-ID status up into a feature-area-level status snapshot |
| `requirements-shaktimaan` | Add/edit/reconcile requirements in the single consolidated PRD file |
| `readme-shaktimaan` | Keep the target project's README.md (badges, setup instructions, feature-status table) current — typically wired as a `before_commit_push` hook |

16 commands total.

## Configurability (what makes this reusable, not tied to one project)

Every path or identity that was hardcoded in the original source material
becomes an `init`-time prompt, written to a per-project config file the
installed skills read at runtime:

| Config key | Prompted at init |
|---|---|
| `requirements_file` | path to the project's PRD |
| `feature_tracker_file` | path to the feature-tracker file |
| `requirements_status_file` | path to the per-ID status file |
| `git_user_name` / `git_user_email` | the commit identity `commit-push-shaktimaan` verifies before committing |
| `project_name` | used in generated template headers |

Config lands in `.shaktimaan/config.yml` in the target project (see below).
Skills read it at run time rather than baking values into rendered
templates, so changing a path later is a one-line config edit, not a
re-render.

## Target-project layout after `shaktimaan init`

Mirrors spec-kit's own install shape, renamed:

```
.claude/skills/<command>-shaktimaan/SKILL.md   # 16 command skills
.shaktimaan/
  config.yml            # per-project config (table above)
  extensions.yml         # before_/after_ hook registrations (same mechanism as .specify/extensions.yml today)
  scripts/                # bash helpers each command shells out to (prereq checks, feature numbering, etc.)
  templates/              # spec/plan/tasks/checklist templates, post-substitution
  memory/constitution.md  # project constitution, if constitution-shaktimaan has been run
```

`.shaktimaan/` replaces `.specify/` as the project-level scaffolding
directory — consistent with fully disconnecting from spec-kit naming.

## Packaging

- Distribution name: `shaktimaan-cli` (PyPI-style, avoids a bare generic
  name; mirrors `specify-cli`'s own naming split from its `specify`
  command).
- Invoked command: `shaktimaan`.
- Install: `uv tool install shaktimaan-cli` (same ergonomics as
  `specify-cli` today).
- `shaktimaan init [DIR]`: prompts for the config table above (or takes
  flags for non-interactive use), renders/copies the 16 skill directories
  and `.shaktimaan/` scaffolding into `DIR` (defaults to `.`).
- `shaktimaan init` is the only command needed for v1. Spec-kit's own
  `upgrade`/`check` equivalents are explicitly deferred — not needed until
  shaktimaan has a second consuming project and an actual upgrade to ship.

## Repo layout (this repo)

```
pyproject.toml
src/shaktimaan/
  cli.py                 # Typer/argparse entry point, `init` command
  config.py               # config prompt + .shaktimaan/config.yml read/write
  render.py                # template placeholder substitution
  presets/
    core/                  # the 16 command templates (SKILL.md + frontmatter), as Jinja-ish templates with {{PLACEHOLDER}} tokens
    scripts/                # bash helpers copied verbatim into .shaktimaan/scripts/
tests/
LICENSE
README.md
docs/superpowers/specs/    # this design doc and future ones
```

## Provenance / licensing

Clean-room implementation — ported from the *shape* of spec-kit's
workflow (command names, artifact types, hook mechanism), not from its
source code. No MIT-attribution obligation is triggered because nothing is
copied; README credits spec-kit as inspiration regardless, as a courtesy.
Shaktimaan's own LICENSE (MIT, copyright Parijat Mukherjee) already
committed.

## Open question carried forward (resolved, noted for the record)

The requirements-tracking bundle was considered as an opt-in extension
(since it assumes an FR-/NFR-/UAT-xxx-style PRD, which not every future
project will use) but the decision was **always included** — simplicity
over per-project flexibility for something that's cheap to ignore if a
project doesn't use it (the commands just won't find matching files to act
on).

## Out of scope for v1

- Any agent other than Claude Code.
- `shaktimaan upgrade` / `shaktimaan check` (spec-kit parity commands).
- Publishing to PyPI (local `uv tool install` from the repo is enough
  until there's a second real consumer).
- Migrating any specific existing project onto shaktimaan (a separate,
  private follow-up, not part of this repo).

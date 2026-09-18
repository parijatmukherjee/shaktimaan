# Shaktimaan User Guide

This walks through using shaktimaan end to end: installing it, setting up a
project's requirements, and running the specify → implement → commit loop.
For the command reference and flags, see [README.md](../README.md); for
the architecture/rationale behind how it's built, see
[docs/superpowers/specs/](superpowers/specs/).

## 1. Install

Not published to PyPI yet — install from a local clone:

```bash
git clone git@github.com:parijatmukherjee/shaktimaan.git
cd shaktimaan
uv tool install .
```

### Starting a new project

```bash
mkdir my-project && cd my-project
git init
shaktimaan init .
```

### Adding shaktimaan to an existing project

```bash
cd my-existing-project
shaktimaan init .
```

Either way, `shaktimaan init` prompts for (or takes as flags — see
`shaktimaan init --help`):

| Prompt | What it's for |
|---|---|
| Project name | Used in generated docs |
| Requirements file path | Where your PRD lives |
| Feature-tracker file path | Where the feature-status snapshot lives |
| Requirements-status file path | Where per-requirement delivery status lives |
| Git commit identity (name/email) | What `commit-push-shaktimaan` verifies before committing |

It installs 17 Claude Code skills into `.claude/skills/` and scaffolding
into `.shaktimaan/` (config, extension hooks, scripts, templates). Re-run
`shaktimaan init` any time to reinstall the latest command set into an
existing project — it won't touch your `.shaktimaan/extensions.yml` if
you've customized it, and it pre-fills prompts from your existing config
instead of starting blank.

## 2. First-time project setup (once per project)

### `/new-requirements-shaktimaan` — write your requirements

Run this once, right after `init`, with a description of what you want to
build — as much or as little detail as you have. It asks clarifying
questions where your description is ambiguous (actor types, MVP vs. later
scope, anything with more than one reasonable reading), then writes two
files:

- **The requirements file** (`requirements_file` in `.shaktimaan/config.yml`)
  — a versioned, structured PRD: functional and non-functional requirements
  grouped by capability area, each tagged MVP / Phase 2 / Later priority,
  starting at v1.0.0.
- **The feature-tracker file** (`feature_tracker_file`) — one row per
  capability area, all starting at status **Not Started**. This is the
  running "what's built so far" snapshot the rest of the workflow reads.

This only runs once. After that, `/new-requirements-shaktimaan` refuses to
run again (it checks whether the requirements file already exists) and
tells you to use `/update-requirements-shaktimaan` instead for edits.

### `/constitution-shaktimaan` — set project principles

Run this to establish (or update) the governing principles for the
project — things like "security first," "no breaking changes without a
migration path," coding conventions, whatever matters for how this project
should be built. You can paste your own text and the command will fold it
in alongside anything it asks you about. It writes
`.shaktimaan/memory/constitution.md`.

This isn't a one-time-only command like requirements bootstrapping — you
can revisit it as the project's principles evolve. But do it at least once
before your first `/prioritise-next-shaktimaan` call, since that command
reads the constitution as one of its inputs.

## 3. The development loop (repeat for every feature)

This is the core cycle. Run it once per feature slice, from picking what
to build next through to a committed, working increment.

```
prioritise-next-shaktimaan
        │
        ▼
specify-shaktimaan  ──▶  clarify-shaktimaan (optional, if the spec has
        │                 ambiguous areas)
        ▼
plan-shaktimaan
        │
        ▼
tasks-shaktimaan  ──▶  analyze-shaktimaan (optional, cross-checks
        │                spec/plan/tasks for consistency)
        ▼
implement-shaktimaan
        │
        ▼
converge-shaktimaan
        │
        ├── gaps found → back to implement-shaktimaan
        │
        └── converged  → commit-push-shaktimaan
                                │
                                ▼
                    back to prioritise-next-shaktimaan
                       for the next slice
```

### `/prioritise-next-shaktimaan` — what to build next

A read-only recommendation — it doesn't write anything. It reads your
requirements file, feature tracker, constitution, and any `research.md`
files from prior features' planning, cross-references `specs/` for what's
already been speced, and recommends the **smallest slice that's still a
complete, production-deployable increment** — not "do this whole feature
area," but the narrowest subset of it that can actually ship. It hands you
back a ready-to-paste feature description.

### `/specify-shaktimaan` — write the spec

Takes that feature description (or your own) and writes `spec.md` under a
new `specs/<NNN>-<slug>/` directory: user scenarios, functional
requirements, success criteria. Up to 3 clarifying questions if something
is genuinely ambiguous and no reasonable default exists.

### `/clarify-shaktimaan` (optional)

If the spec still has open questions after `/specify-shaktimaan`, run this
to resolve up to 5 more, encoded back into `spec.md`.

### `/plan-shaktimaan` — design the implementation

Produces the technical design artifacts: `plan.md`, and depending on the
feature, `data-model.md`, `contracts/`, `research.md`. This is where
technical decisions and constraints get written down — later
`/prioritise-next-shaktimaan` runs read any `research.md` this produces.

### `/tasks-shaktimaan` — break it into tasks

Generates a dependency-ordered `tasks.md` from the spec and plan —
setup, tests, core implementation, integration, polish, with `[P]` markers
for tasks that can run in parallel.

### `/analyze-shaktimaan` (optional)

A non-destructive consistency check across `spec.md`, `plan.md`, and
`tasks.md` — catches contradictions or gaps before you start implementing.

### `/implement-shaktimaan` — build it

Executes `tasks.md` phase by phase, test-first, marking each task `[X]` as
it completes. Halts on a non-parallel task failure rather than plowing
ahead.

### `/converge-shaktimaan` — check it's actually done

Assesses what got built against the spec, plan, and tasks. Two outcomes:

- **Gaps found** — appends the remaining work as new tasks to `tasks.md`.
  Go back to `/implement-shaktimaan`.
- **Converged** — nothing left. Move on to `/commit-push-shaktimaan`.

### `/commit-push-shaktimaan` — ship it

Stages by name (never a blanket `add -A`), verifies your git identity
matches `.shaktimaan/config.yml` before committing, commits with no
unwanted attribution trailer, and pushes. Refuses to force-push or push
over history it didn't just create — you're asked first. Also runs the
`before_commit_push` hook (`/readme-shaktimaan`, wired by default — see
below), so your README's badges and feature-status table stay current
automatically.

Then it's back to `/prioritise-next-shaktimaan` for the next slice.

## 4. Keeping things current

A few commands run mostly on their own, via the extension hooks
`shaktimaan init` wires up by default in `.shaktimaan/extensions.yml` — you
don't normally invoke them directly, but it helps to know what they do:

- **`/requirements-sync-shaktimaan`** — after `/specify-shaktimaan` and
  after `/implement-shaktimaan`, traces the spec's requirement IDs against
  your requirements file and keeps the requirements-status file current
  (which IDs are Not Started / In Progress / Done). Flags it if a spec
  implies behavior with no matching requirement, rather than inventing a
  mapping.
- **`/feature-tracker-shaktimaan`** — rolls that per-requirement status up
  into the feature-area-level tracker (the file
  `/new-requirements-shaktimaan` first created). Moves an area from Not
  Started to In Progress the first time a spec targets it, and to
  Delivered once every MVP requirement in that area is verified — never
  from a spec or a task list alone.
- **`/readme-shaktimaan`** — refreshes your project's `README.md` (badges,
  setup instructions, feature-status table) right before every commit.

You can also run any of these by hand if you want a status check without
waiting for the next hook trigger.

Two commands you'll reach for as the project evolves, not on a fixed
schedule:

- **`/update-requirements-shaktimaan`** — add, edit, retire, or reconcile
  requirements after the initial bootstrap. Bumps the requirements file's
  version and adds a changelog entry for anything that changes meaning.
- **`/taskstoissues-shaktimaan`** — convert an active feature's `tasks.md`
  into dependency-ordered GitHub issues, if you want task tracking to live
  there instead of (or alongside) `tasks.md`.

## 5. Where things live

| What | Where |
|---|---|
| Requirements (PRD) | `requirements_file`, from `.shaktimaan/config.yml` |
| Feature-area status | `feature_tracker_file` |
| Per-requirement delivery status | `requirements_status_file` |
| Project principles | `.shaktimaan/memory/constitution.md` |
| Feature specs, plans, tasks | `specs/<NNN>-<slug>/` |
| Extension hooks | `.shaktimaan/extensions.yml` |
| Installed commands | `.claude/skills/*-shaktimaan/` |

Every path above except the last two is configurable per project — set
once at `shaktimaan init` time, read by every command at runtime from
`.shaktimaan/config.yml`. Changing one later is a one-line edit to that
file, not a reinstall.

# Shaktimaan

A personal Spec-Driven Development (SDD) toolkit for Claude Code: a CLI
that scaffolds a `specify → clarify → plan → tasks → analyze → checklist →
implement → converge` workflow into any project, plus `commit-push` and
`prioritise-next`, and a requirements-tracking bundle for PRD-style
projects.

Inspired by [github/spec-kit](https://github.com/github/spec-kit) (MIT
licensed) — same workflow shape, own implementation, own commands.

## Install

Not published to PyPI yet — install from a local clone of this repo:

```bash
git clone git@github.com:parijatmukherjee/shaktimaan.git
cd shaktimaan
uv tool install .
```

## Usage

```bash
shaktimaan init /path/to/your/project
```

Prompts for (or takes as flags):

| Flag | What it's for |
|---|---|
| `--project-name` | Used in generated docs |
| `--requirements-file` | Path to your PRD |
| `--feature-tracker-file` | Path to your feature-status tracker |
| `--requirements-status-file` | Path to your per-requirement delivery-status file |
| `--git-user-name` / `--git-user-email` | The identity `commit-push-shaktimaan` verifies before committing |

Installs 17 Claude Code skills into `.claude/skills/` and scaffolding into
`.shaktimaan/`.

See [docs/GUIDE.md](docs/GUIDE.md) for a full walkthrough — first-time
setup, the specify → implement → commit loop, and what each command does.

## Commands installed

`specify-shaktimaan`, `clarify-shaktimaan`, `plan-shaktimaan`,
`tasks-shaktimaan`, `analyze-shaktimaan`, `checklist-shaktimaan`,
`implement-shaktimaan`, `converge-shaktimaan`, `taskstoissues-shaktimaan`,
`constitution-shaktimaan`, `commit-push-shaktimaan`,
`prioritise-next-shaktimaan`, `new-requirements-shaktimaan`,
`requirements-sync-shaktimaan`, `feature-tracker-shaktimaan`,
`update-requirements-shaktimaan`, `readme-shaktimaan`.

## Status

v1: Claude Code only. See `docs/superpowers/specs/` for the design doc.

## License

MIT — see [LICENSE](LICENSE).

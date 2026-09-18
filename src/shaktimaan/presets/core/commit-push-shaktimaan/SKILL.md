---
name: "commit-push-shaktimaan"
description: "Stage, commit, and push the current changes using this project's configured git identity and commit-message conventions (no Co-Authored-By or Generated-with trailers unless the project asks for one)."
argument-hint: "Optional commit message override"
compatibility: "Requires .shaktimaan/config.yml (run `shaktimaan init` first)"
user-invocable: true
disable-model-invocation: false
model: sonnet
---

## User Input

```text
$ARGUMENTS
```

If non-empty, use this as the commit message (still validate it makes sense against the diff).
Otherwise derive a concise message from the staged/unstaged diff.

## Pre-Execution Checks

**Check for extension hooks (before commit-push)**:
- Check if `.shaktimaan/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_commit_push` key.
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that
  `.shaktimaan/extensions.yml` could not be read (include the parser error) and that no hooks
  were checked, including any mandatory (`optional: false`) hooks registered there, then
  continue normally.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field
  as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition`
  expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable.
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to
    the HookExecutor implementation.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to Steps.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish
    before continuing to Steps below. Emitting the block alone does not run the hook.
- If no hooks are registered or `.shaktimaan/extensions.yml` does not exist, skip silently.

## Steps

1. Read `.shaktimaan/config.yml` for `git_user_name` and `git_user_email`. If the file doesn't
   exist, **STOP** and tell the user to run `shaktimaan init` first.

2. Run `git status` and `git diff` (staged and unstaged) to see what actually changed —
   including any changes a `before_commit_push` hook just made. Flag anything that looks like a
   secret (`.env`, credentials, private keys, tokens) to the user before staging it — never
   commit those silently.

3. **Verify git identity** — run `git config --local user.name` and
   `git config --local user.email`. They MUST resolve to exactly the `git_user_name` /
   `git_user_email` values read in step 1.

   If either is unset or different, **STOP** and tell the user to fix `git config --local
   user.name` / `user.email` first. Never silently fall back to a different identity, and never
   set one yourself without being asked to.

4. Stage the relevant files **by name** — never `git add -A` or `git add .`. Call out any file
   in the diff that looks unintended or unrelated to the change being committed. If a
   `before_commit_push` hook modified a file (e.g. README.md), include it by name so it lands in
   this same commit.

5. Commit with a concise message focused on *why*, passed via a heredoc for correct formatting.
   Do **not** append a `Co-Authored-By:` trailer or any "Generated with Claude Code" line unless
   this project's own conventions explicitly ask for one.

6. Push the current branch to its tracked remote: `git push`, or
   `git push -u origin <branch>` if it has no upstream yet.
   - If the branch is `main`/`master`, or pushing would require `--force`/`--force-with-lease`,
     **STOP** and ask the user first — this command never force-pushes and never pushes over
     history it didn't just create.

7. Report the commit hash, branch name, and remote/branch pushed to.

## Done When

- [ ] Extension hooks (`before_commit_push`) dispatched or skipped according to the rules in
      Pre-Execution Checks above
- [ ] Changes staged by name (no blanket `add -A`) and no secrets committed
- [ ] Git identity verified against `.shaktimaan/config.yml` before committing
- [ ] Commit created with no unwanted attribution trailer
- [ ] Branch pushed to its remote (or the user was asked first, for a force-push case)
- [ ] Commit hash and branch reported to the user

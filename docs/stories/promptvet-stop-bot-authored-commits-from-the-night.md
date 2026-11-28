# Story: stop bot-authored commits from the nightly eval workflow

- id: `promptvet-stop-bot-authored-commits-from-the-night`
- kind: maintenance, priority P1
- eval spec: [`evals/promptvet-stop-bot-authored-commits-from-the-night.yaml`](../../evals/promptvet-stop-bot-authored-commits-from-the-night.yaml)
- construction: **human** (the change is to `.github/workflows/evals.yml`, which agents may not edit)

## Problem

`.github/workflows/evals.yml` runs `python evals/run_golden.py` every night, then sets git to `promptvet-bot`, commits `evals/results` and pushes straight to `main` with a `contents: write` token. That has put 11 non-sai337 commits on `main` so far, breaks the rules that every commit is `sai337 <sai.devop@gmail.com>` and that nothing pushes to `main`, and is exactly what the scope-guard (`commit_violations` in the agency repo) rejects in PRs. The `|| true` on the commit and push lines also hides push failures. The gate step itself has no `|| true` and must stay that way.

The fix: the nightly job only runs the gate and publishes the metrics to the run's job summary (`$GITHUB_STEP_SUMMARY`). It needs no write token, no new action and no commits.

## Acceptance criteria

| id | criterion |
|---|---|
| AC1-no-bot-commits | The nightly workflow no longer sets a git identity, stages, commits or pushes anything, and has no reference to `promptvet-bot`. A run leaves every branch head unchanged. |
| AC2-read-only-token | Workflow-level permissions are exactly `contents: read`, no job overrides them, and checkout does not persist the token (`persist-credentials: false`). |
| AC3-results-visible | Every run, pass or fail, writes the `golden.json` metrics (or an explicit "no results" line when the gate crashed before writing them) to the job summary via `$GITHUB_STEP_SUMMARY`. No new third-party action: only `actions/checkout@v4` and `actions/setup-python@v5`. |
| AC4-failures-surface | Nothing swallows a failure: no `\|\| true`, no `\|\| :`, no `continue-on-error`, no `set +e`. The gate step is the bare `python evals/run_golden.py`, so a gate miss (exit 1) fails the job. |
| AC5-clean-pr | The PR changes only `.github/workflows/evals.yml`, `docs/EVALS.md` and this story's two planning files; CI and scope-guard are green; every PR commit is authored by `sai337 <sai.devop@gmail.com>` with no trailers; the privacy check reports nothing new compared with `main`. |
| AC6-history-preserved | Existing `promptvet-bot` commits on `main` and the `evals/results/<date>/` directories stay as they are: no deletion, no rewrite, no force-push. |

## Exact replacement for `.github/workflows/evals.yml`

Replace the whole file with:

````yaml
name: evals-nightly
# Nightly golden-set gate. Read-only token: results go to the job summary; nothing is committed or pushed.
on:
  schedule: [{cron: "17 9 * * *"}]
  workflow_dispatch: {}
permissions: {contents: read}
jobs:
  golden:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {persist-credentials: false}
      - uses: actions/setup-python@v5
        with: {python-version: "3.13"}
      - name: Golden-set gate
        run: python evals/run_golden.py
      - name: Golden results to job summary
        if: always()
        run: |
          f="evals/results/$(date +%F)/golden.json"
          {
            echo "## Golden-set eval, $(date +%F)"
            if [ -f "$f" ]; then
              echo '```json'
              cat "$f"
              echo
              echo '```'
            else
              echo "No \`$f\` was produced: the gate step failed before writing results. See its log."
            fi
          } >> "$GITHUB_STEP_SUMMARY"
````

Notes for the person applying it:
- Keep the step name `Golden results to job summary` exactly; the `dispatch-run-clean` check looks for it.
- `date +%F` and `run_golden.py` both use the runner's local date (UTC), and the cron runs at 09:17 UTC, so the paths always match.
- The extra `echo` after `cat` is needed because `golden.json` has no trailing newline.

In `docs/EVALS.md`, replace the line under `## Nightly` with:

> `.github/workflows/evals.yml` runs the golden gate nightly with a read-only token and posts `golden.json` to the run's job summary; it commits nothing. `evals/results/` keeps the results committed before this change.

Commit locally with `git -c user.name=sai337 -c user.email=sai.devop@gmail.com commit` and no trailers. A web-UI edit also passes scope-guard, but GitHub becomes the committer. Optionally run `gh workflow disable evals-nightly -R sai337/promptvet` until the PR merges, so no more bot commits land, then `gh workflow enable evals-nightly -R sai337/promptvet`.

## `evals/results/` history

It stays in the repo as the record from before this change. Nothing is deleted or rewritten, and new nightly results live only in each run's job summary.

## Out of scope

Rewriting or reverting the old bot commits, deleting `evals/results/`, changing the gate or dataset, editing other workflows or SHA-pinning existing actions, adding `actions/upload-artifact` (that would need a full commit-SHA pin and vetting), and branch-protection changes.

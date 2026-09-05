# Upstream sync state (auto-maintained by the weekly cron task)

- **last synced upstream/main SHA:** `2d68ded2f2b7d4ba540855119433be86ed87bd84`
  ("feat: restore Neural Inverse branding across IDE UI", 2026-07-22)
- **last checked:** 2026-09-05 (baseline set when the weekly sync automation was created)
- **integration branch:** merges from `upstream/main` land on the current
  primary development branch (see each run's report), never on `upstream`.

## Known issues / human decisions

- Local `main` (2d68ded) is healthy vs upstream, but `origin/main` (62b92c24)
  came from the old fork's force-pushed main and has diverged. Not blocking
  branch-level syncs; needs a one-time human reconciliation decision.

## Run log (newest first)

- 2026-09-05 — baseline established at 2d68ded2 (no changes pulled yet).

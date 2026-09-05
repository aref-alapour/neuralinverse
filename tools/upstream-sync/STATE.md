# Upstream sync state (auto-maintained by the weekly cron task)

- **last synced upstream/main SHA:** `2d68ded2f2b7d4ba540855119433be86ed87bd84`
  ("feat: restore Neural Inverse branding across IDE UI", 2026-07-22)
- **last checked:** 2026-09-05
- **integration branch:** merges from `upstream/main` land on the current
  primary development branch, then push to `origin` (the fork:
  aref-alapour/neuralinverse) and to `private` (zoomcode backup mirror).
  Upstream itself is never pushed to (push URL DISABLEd); contributions go
  via PRs only (see AGENTS.local.md Collab gate).

## Repo topology (2026-09-05)

- `origin` = aref-alapour/neuralinverse — a FRESH real fork (the original
  fork got detached from the fork network during a brief privacy change and
  was renamed to `neuralinverse-archive`). `isFork: true`, public.
- fork `main` = `upstream/main` = `2d68ded2` (the historical divergence of
  the old fork's main is gone with the fresh fork — resolved).
- `private` = aref-alapour/zoomcode — standalone private backup.
- Upstream PRs #134/#136 could not be reopened after the detach (head-repo
  links dropped) → recreated as **#137** and **#138**.

## Run log (newest first)

- 2026-09-05 — baseline established at 2d68ded2; repo topology reworked to
  fork-first collaboration; clean-room license gate added (no verbatim code
  from freebuff/ComfyUI or any licensed third party — AGENTS.local.md gate 2).

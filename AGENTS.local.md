# AGENTS.local.md — NeuralInverse development rules (OUR project rules)

We work ON the fork (`aref-alapour/neuralinverse`) and collaborate with
upstream (`NeuralInverse/neuralinverse`) via professional issues and PRs.
The owner's OK in chat is the publish trigger: whatever the owner approves
locally ALSO goes upstream as a clean issue/PR.
(The root `AGENTS.md` belongs to upstream VS Code — never edit it.)

## Hard gates (never skip)

1. **Collab gate:** when the owner approves work in chat ("اوکیه", "بفرست",
   "PR بزن", ...), publish it upstream in the SAME task: carve the
   upstream-able part into a clean branch (ONLY the code change — never
   `tools/`, `AGENTS.local.md`, `تسک/`, `PROMPT-SESSION.md`, handoff docs),
   push to the fork, then open a professional issue and/or PR in English
   (Problem → root cause → Fix → Testing; link related issues; `Fixes #N`;
   reference superseded PRs when applicable). Without OK: commit locally and
   report — never publish on your own initiative.
2. **License / clean-room gate (2026-09-05):** for any third-party licensed
   codebase in our orbit (Codebuff/freebuff — Apache-2.0; ComfyUI — GPL-3.0;
   any other external project): READ it to understand, TAKE IDEAS, learn the
   design — but NEVER copy code verbatim or near-verbatim. No "ported" or
   "adapted" files, no provenance-header copies, no mechanical
   line-by-line translation. Implement concepts in OUR own architecture and
   words so the result is fully ours and upstream-PR-able (upstream is a
   public international project). Never add runtime dependencies from those
   projects without the owner's explicit approval. (Code inside this fork's
   own MIT lineage — VS Code/Void/NeuralInverse — is our codebase, not
   third-party; normal fork rules apply to it.)
3. **Live-test gate:** a fix is "done" only after the owner tested it on the
   installed app (see Live testing). Source-only = not done.
4. **Live-patch gate:** every source change ships in the SAME task with its
   `tools/live-patch.py` port, applied to the installed app (run elevated,
   verify markers, owner restarts to see it live). A commit without its
   live-patch port is NOT done.
5. Never push to `upstream` directly (its push URL is DISABLEd). All upstream
   contributions go via fork branches + PR. Never force-push shared branches.
6. Never edit files outside our scope (below) without saying why first.
7. Never print or commit secrets/keys. Persian in chat; issues/PRs/code in
   English.

## Remotes & branching

- `origin` → aref-alapour/neuralinverse — the REAL fork (recreated fresh on
  2026-09-05; the old one got detached from the fork network when it briefly
  went private, now `neuralinverse-archive`). PR heads live here.
- `upstream` → NeuralInverse/neuralinverse (source of truth; fetch-only)
- `private` → aref-alapour/zoomcode (private backup mirror; push milestones)
- Fork `main` mirrors `upstream/main` — before new work: `git fetch upstream`
  and branch from the right base:
  - fixes to files as they exist upstream → branch from `upstream/main`
  - continuation of our unmerged work → branch from our feature branch
- One concern per branch/PR. Reference the issue (`Fixes #N`).

## Code scope

- Allowed by default: `src/vs/workbench/contrib/neuralInverse/**`
- Allowed when justified: `src/vs/workbench/contrib/void/**`,
  `src/vs/platform/update/**` (say why in the commit/PR)
- Forbidden: core vscode paths, root `AGENTS.md`
- `IAgentDefinition.id` is canonical; agent resolution keys by `id` first.
- Match the file's existing TS style. No reformat drives. Sparse checkout:
  `git sparse-checkout add <path>` when more of the repo is needed.

## Live testing (installed app)

- Install: `C:\Program Files\NeuralInverse`
- Bundles patched by `tools/live-patch.py`:
  `out/vs/workbench/workbench.desktop.main.js` (renderer),
  `out/main.js` (main process) + `product.json` (checksums dropped, version
  stamped from their update API). Write access needs admin elevation.
- After ANY app update: files are replaced → tell the owner to run the
  desktop shortcut **"Repatch NeuralInverse.bat"**, then re-verify every
  patch marker still applies; if a pattern went missing, update the script
  for the new bundle BEFORE any new work.
- To revert everything: `python tools/live-patch.py --revert` (admin).
- Owner restarts the app to load patches. Known limitation of the
  conversation-memory live patch: two agents running concurrently can mix
  context (the source fix doesn't have this).

## Session workflow (per task)

1. State the task and the file(s) you expect to touch.
2. Investigate source first (read before editing).
3. Implement on source; commit locally with a clear English message.
4. Port to `tools/live-patch.py` (minified patterns), run elevated, verify
   markers, ask the owner to restart + test.
5. Iterate until the owner approves.
6. On owner OK: clean branch → push to fork → professional issue/PR on
   upstream → report links. If an issue already covers it, link it.
7. Mirror the branch to the `private` backup remote.

## Upstream state (update as things merge)

- #137 PR: agent resolution by id (supersedes #134, was auto-closed when the
  fork briefly went private) — OPEN, awaiting review
- #138 PR: updater client-side version guard (supersedes #136; fixes #135
  item 1) — OPEN, awaiting review
- #133 / #135 issues: OPEN (both addressed by the PRs above)
- Local, not yet PR'd: `feat/agent-conversation-memory` (conversation memory,
  intake questions, stream resilience, pre-send context pipeline, tool-name
  aliases, executor chatMode null). Carve into clean PR(s) after owner OK +
  live test.
- Policy history: 2026-09-05 fork collaboration restored; clean-room license
  gate added (no verbatim code from freebuff/ComfyUI or any licensed source).

## Build (heavy — avoid unless needed)

Full VS Code build (`npm i && gulp`): hours + tens of GB on Windows. Prefer
upstream CI for compile verification on PRs.

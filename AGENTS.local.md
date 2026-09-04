# AGENTS.local.md — NeuralInverse development rules (OUR project rules)

Fork of VS Code / Void. We develop here, test live on the installed app, and
PR to upstream ONLY after the owner's explicit approval.
(The root `AGENTS.md` belongs to upstream VS Code — never edit it.)

## Hard gates (never skip)

1. **Approval gate:** completing work locally is NOT permission to publish.
   Pushing to the fork, opening issues, or opening PRs on
   NeuralInverse/neuralinverse requires the owner's explicit OK in chat
   ("بفرست", "PR بزن", ...). Until then: commit locally, report, stop.
2. **Live-test gate:** a fix is "done" only after the owner tested it on the
   installed app (see Live testing). Source-only = not done.
3. Never push to `upstream` directly. All upstream contributions go via
   fork branches + PR. Never force-push shared branches.
4. Never edit files outside our scope (below) without saying why first.
5. Never print or commit secrets/keys. Persian in chat; issues/PRs/code in
   English.

## Remotes & branching

- `origin` → aref-alapour/neuralinverse (fork; PRs come from here)
- `upstream` → NeuralInverse/neuralinverse (source of truth)
- Before new work: `git fetch upstream` and branch from the right base:
  - fixes to files as they exist upstream → branch from `upstream/main`
  - continuation of our unmerged work → branch from our feature branch
- One concern per branch/PR. Reference the issue (`Fixes #N`).
- Upstream PR branches must contain ONLY the code change — never our
  local tooling (`tools/`, `AGENTS.local.md`, `PROMPT-SESSION.md`, `تسک/`).

## Code scope

- Allowed by default: `src/vs/workbench/contrib/neuralInverse/**`
- Allowed when justified: `src/vs/workbench/contrib/void/**`,
  `src/vs/platform/update/**` (say why in the commit/PR)
- Forbidden: core vscode paths, root `AGENTS.md`
- GPL containment: `workflow-engine/` (ported from ComfyUI, GPL-3.0 — see
  `تسک/07-comfyui/`) is fork-only. NEVER include it, its exports, or its code
  in upstream PRs (upstream is Apache-2.0). Provenance headers + PORTED-FROM.md
  are mandatory in every ported file.
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
3. Implement on source; commit locally with a clear message.
4. Port to `tools/live-patch.py` (minified patterns), run elevated, verify
   markers, ask the owner to restart + test.
5. Iterate until the owner approves.
6. Only then: clean branch → push to fork → issue/PR on upstream →
   report links. If an issue already covers it, link instead of duplicating.

## Upstream state (update as things merge)

- #133 issue: agent resolution keyed by name not id (+ adhoc registration,
  hydration race) — OPEN
- #134 PR: id-keyed lookup maps — awaiting review
- #135 issue: updater endless banner + fake download crash — OPEN
- #136 PR: updater client-side version guard — awaiting review
- Local, not yet PR'd: feat/agent-conversation-memory (conversation memory
  + executor chatMode null). PR AFTER owner's live test passes.
- Known upstream bugs not yet reported: none queued.

## Build (heavy — avoid unless needed)

Full VS Code build (`npm i && gulp`): hours + tens of GB on Windows. Prefer
upstream CI for compile verification on PRs.

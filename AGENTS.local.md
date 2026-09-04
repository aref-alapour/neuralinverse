# AGENTS.local.md — NeuralInverse development (our ZCode project rules)

Fork of VS Code / Void. We develop here and PR to upstream.
(The root `AGENTS.md` belongs to upstream VS Code — don't edit it.)

## Remotes
- `origin` → aref-alapour/neuralinverse (our fork; PRs come from here)
- `upstream` → NeuralInverse/neuralinverse (source of truth)

## Workflow
1. `git fetch upstream` before starting any branch.
2. Branch from `upstream/main`: `git checkout -b <type>/<slug> upstream/main`.
3. One concern per branch / PR. Reference the issue (`Fixes #N`).
4. Rebase before pushing if upstream moved. Never push to upstream directly.
5. PR body in English (maintainers' language); chat in Persian is fine.

## Code rules
- Touch ONLY under `src/vs/workbench/contrib/neuralInverse` (and `contrib/void`
  or `contrib/powerMode` when strictly related). Never modify core vscode paths.
- `IAgentDefinition.id` is canonical; anything resolving agents keys by `id`
  first, display-name aliases only for backward compatibility.
- Match existing TS style in the file you edit; no reformat drives.
- Sparse checkout is on: `git sparse-checkout add <path>` when more is needed.

## Live testing (installed app)
- Installed app: `C:\Program Files\NeuralInverse`
- Bundle: `resources/app/out/vs/workbench/workbench.desktop.main.js` (minified,
  ~24 MB). Write access needs admin elevation.
- `tools/live-patch.py` applies our source-level fixes to that bundle so we can
  test before a real build. It backs up the original once (`.orig`).
- After an app auto-update the bundle is replaced → re-run the patch script.
- To revert: restore the `.orig` backup.

## Build (heavy — avoid unless needed)
Full VS Code build: `npm i && gulp` in repo root. Hours + tens of GB on
Windows. Prefer upstream CI for compile verification on PRs.

## Current roadmap
1. #133 Bug 3: register ad-hoc workflow in configLoader (dead primary path).
2. #133 Bug 4: `whenReady` gate on AgentStoreService hydration race.
3. Agent chat history/session persistence (root cause of "agent forgets"
   loops — our doc-writer case).
4. Design discussion upstream: multi-agent channels / team orchestration.

## Open items
- PR #134 (fix/agent-resolution-by-id) — awaiting review.
- Issue #133 — bug report backing the PR.

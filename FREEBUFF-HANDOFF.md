# Handoff: Freebuff Analysis → Task Breakdown for NeuralInverse

## Purpose of this document

You are receiving this document to perform **task breakdown (تسک‌بندی)**: turn the findings below into a concrete, ordered set of implementation tasks for upgrading the AI-agent subsystems of **NeuralInverse** (a VS Code fork) by porting patterns from **Freebuff/Codebuff** (an open-source multi-agent coding framework).

This document is self-contained. Verify current repo state before finalizing tasks — the working tree may contain uncommitted modifications.

---

## 1. The two codebases

### 1.1 Source: Freebuff (analysis target)

- **Location (already cloned):** `C:\Users\jobal\dev\freebuff` (sibling of the neuralinverse repo — do NOT nest it inside)
- **Upstream:** https://github.com/CodebuffAI/freebuff — Codebuff's public snapshot repo. Git history is squashed "Sync public snapshot" commits from a private repo; no useful per-commit history.
- **What it is:** A terminal-based multi-agent AI coding assistant (TUI built with React + OpenTUI on the Bun runtime). NOT a VS Code fork. Its value to us is the **agent architecture, tool protocols, prompts, and resilience patterns** — not UI.
- **License:** Apache 2.0 + a `NOTICE` file ("Codebuff, Copyright 2025 Codebuff"). We may copy/adapt code freely as long as we preserve attribution (keep the NOTICE terms in adapted files or a third-party notices file).
- **Scale:** ~34k lines TS, ~1,500 files, Bun monorepo.
- **Monorepo layout:**

| Path | Role |
|---|---|
| `packages/agent-runtime/` | The agent execution loop, stream parsing, tool execution pipeline, context compaction |
| `common/` | Tool schemas (Zod, ~40 tools), message/event protocol types, client↔server wire types, utilities |
| `agents/` | Agent definitions: base2/base3 harnesses, editor, reviewer, thinker, researcher, basher, context-pruner, … |
| `sdk/` | `@codebuff/sdk` public embedding API (CodebuffClient, run(), RunState continuation) |
| `cli/` | Terminal UI client (React + OpenTUI, Zustand + TanStack Query) |
| `freebuff/` | Free-tier product variant built from the same `cli/` via compile-time `FREEBUFF_MODE` flag |
| `packages/code-map/` | Tree-sitter identifier extraction, file relevance scoring, reverse-dependency map |
| `packages/llm-providers/` | OpenAI-compatible LLM provider shim (AI SDK v7 `LanguageModelV2`) |
| `evals/` | "BuffBench": commit-reconstruction evals with dual AI judges |
| `scripts/tmux/` | tmux drivers for TUI e2e testing |

### 1.2 Target: NeuralInverse (our editor)

- **Repo:** `C:\Users\jobal\dev\neuralinverse` — a VS Code fork. Follow `AGENTS.md` and `.github/copilot-instructions.md` for build/validation conventions.
- **Our agent subsystem lives in:** `src/vs/workbench/contrib/neuralInverse/browser/` (~132 TS files). Current subsystems that matter for this work:

| Area | Files | Current state |
|---|---|---|
| Tool registry | `tools/toolRegistry.ts` (193 ln), `tools/fsTools.ts`, `tools/terminalTools.ts`, `tools/gitTools.ts`, `tools/httpTools.ts`, `tools/communicationTools.ts` | Registry + individual tools exist; **`toolRegistry.ts` has uncommitted local modifications** |
| Agent loop | `executor/agentExecutor.ts` (544 ln), `executor/toolCallParser.ts` (91 ln), `executor/retryPolicy.ts`, `executor/budgetTracker.ts`, `executor/outputValidator.ts`, `executor/toolCache.ts` | Single-agent loop with retry/budget; no sub-agents, no streaming tool-call channel |
| Context pipeline | `context/` — `index/workspaceSymbolIndex.ts`, `graph/dependencyGraph.ts`, `relevance/relevanceScorer.ts`, `search/{bm25Index,trigramIndex,embeddingService,hybridSearchService,persistentStore}.ts`, `packer/contextPacker.ts`, `tracker/changeTracker.ts` | Rich local indexing already exists (comparable to freebuff's code-map). The **deltas** we want: reverse-dependency annotation on file reads, token-scored file tree rendering, compaction |
| Interactive tools | `tools/communicationTools.ts` (400 ln) | Review whether it already covers ask_user-style structured Q&A before planning a port |
| Workflow/orchestration | `orchestrator/`, `composer/`, `agentManagerPart.ts`, `backgroundAgentService.ts` | Canvas-style workflow composition exists; sub-agent delegation patterns from freebuff are complementary |

**Key architectural fact about freebuff to internalize:** the agent loop runs **in-process in the host**, and all I/O tools (file writes, terminal) are delegated back to the host via a `requestClientToolCall` indirection — the runtime itself never touches the filesystem. This maps 1:1 onto our extension-host boundary: the loop can live anywhere while VS Code owns execution, permissions, and edits (via `workspace.applyEdit` / `TextDocuments`).

---

## 2. Freebuff deep-dive: the patterns worth porting

Each item below = candidate task cluster. Ordered by (value ÷ effort) for NeuralInverse, tiers P0/P1/P2.

### P0-1. Exact-match `str_replace` edit tool with input-repair layer

**What:** Freebuff's core edit tool is deterministic exact-match string replacement (no fuzzy matching, no regex). Reliability comes from (a) a preprocessing layer that repairs common LLM formatting mistakes before validation, and (b) failure messages that teach the model to self-correct.

**Source files:**
- `C:/Users/jobal/dev/freebuff/common/src/tools/params/tool/str-replace.ts` — input schema + prompt-engineered description
- `C:/Users/jobal/dev/freebuff/common/src/tools/params/utils.ts` — `coerceToArray` (LLMs pass single object/stringified array where array expected), `coerceToObject`, `normalizeReplacementAliases` (maps `old/old_str/old_string` → `oldString`, `new/new_str/new_string` → `newString`)
- `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/tools/tool-executor.ts` — `parseRawToolCall`: up-to-3× JSON.parse for double-encoded args, per-tool validation hints (e.g. missing `newString` → "set newString to \"\" for deletion")

**Semantics:** `{ path, replacements: [{ oldString (min 1), newString (may be "" = delete), allowMultiple? }] }`. Batch multiple edits in ONE call. No/multiple match → structured `{ file, errorMessage, patch? }` result (not an exception) so the model retries.

**Maps to:** `tools/fsTools.ts` — replace/upgrade our file-edit tool. Natural VS Code execution: `workspace.applyEdit` with `TextEdit` ranges located by exact match.

### P0-2. Mechanical (LLM-free) context compaction with cache-aware trigger

**What:** When conversation history exceeds budget — or the prompt cache has gone cold anyway — history is rewritten **deterministically** into a compact `<conversation_summary>` form. No extra LLM call, no provider failure path.

**Source files:**
- `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/compact-history.ts` (~992 ln) — the in-process compactor used by the base3 harness
- `C:/Users/jobal/dev/freebuff/agents/context-pruner.ts` (963 ln) — parallel agent-definition copy (same logic as a spawned agent); port ONE of them, prefer the runtime copy
- `C:/Users/jobal/dev/freebuff/common/src/constants/compaction-policy.ts` — per-model `{ cacheExpiryMs, cacheExpiryMinTokens }` policy table

**Design points to preserve:**
- Two triggers: (1) hard context limit (must compact), (2) **prompt-cache expired** (gap between message `sentAt` timestamps > threshold AND history above a token floor) — compaction then costs nothing because the next request re-reads history at full price regardless
- Role-separated token budgets: user prompts get a larger budget (50k) than assistant+tool messages (20k) — tool-result flooding must not evict user instructions
- Per-tool-call one-line summaries ("inspected files: a.ts, b.ts" / "ran command: npm test…")
- Truncation keeps 80% head / 20% tail; deleted entries replaced by placeholder messages; images preserved
- A continuation message so the model resumes mid-turn cleanly

**Maps to:** new module under `context/` (e.g. `context/compaction/`) feeding `executor/agentExecutor.ts` before each model call.

### P0-3. `referencedBy` reverse-dependency annotation on file reads

**What:** Every `read_files` result carries `referencedBy: [files that call symbols defined in this file]`, so the model learns blast radius without spending a grep call.

**Source files:**
- `C:/Users/jobal/dev/freebuff/packages/code-map/src/parse.ts` — `getFileTokenScores()` → `{ tokenScores, tokenCallers }`; scoring: `0.8^dirDepth * sqrt(numLines/(identifiers+1))`, boosted by `1 + log(1 + externalCalls)`; budgets: 10k files / 1MB per file / 500MB total
- `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/tools/handlers/tool/read-files.ts` + `util/render-read-files-result.ts` — attaches `referencedBy` per file
- `C:/Users/jobal/dev/freebuff/common/src/util/file.ts` — `printFileTreeWithTokens()`: file tree with top identifiers inline per file (Aider-style repo map for the system prompt)

**Maps to:** we ALREADY have `context/graph/dependencyGraph.ts` + `context/index/workspaceSymbolIndex.ts` — the task is the *plumbing*: annotate our file-read tool output and render a token-scored tree in the system prompt. This is mostly integration, not new indexing.

### P1-4. Windowed file reads with self-describing truncation

**What:** Reads are windowed (offset/limit) with hard budgets, and every truncation footer tells the model exactly how to continue.

**Source:** `C:/Users/jobal/dev/freebuff/common/src/util/file-read-limits.ts` — per-call 100k chars / 20k est. tokens; per-file 2k lines / 50k chars; `windowFileRead` (offset/limit) emits footers like "[showing lines X–Y of Z… call again with offset=Y+1]"; surrogate-pair-safe truncation.

**Maps to:** our file-read tool in `tools/fsTools.ts`; pairs with P0-3.

### P1-5. Propose/apply split for review-safe edits (+ best-of-N editing)

**What:** Shadow tools `propose_str_replace` / `propose_write_file` return `unifiedDiff` without touching disk. Multiple proposals on the same file "stack correctly". A parent/user reviews then applies. MAX mode goes further: N parallel implementers draft with `propose_*`, a selector agent compares unified diffs and returns `{ implementationId, suggestedImprovements }`, and the coordinator replays the winner as real edits.

**Source files:**
- `C:/Users/jobal/dev/freebuff/common/src/tools/params/tool/propose-str-replace.ts`, `propose-write-file.ts`
- `C:/Users/jobal/dev/freebuff/agents/editor/best-of-n/editor-multi-prompt.ts`, `editor-implementor.ts`, `best-of-n-selector2.ts`
- Each `write_file`/`propose_write_file` input includes a one-sentence `instructions` field reused as the diff summary line in review UI

**Maps to:** VS Code native fit — proposed changes render as inline review decorations; apply via `workspace.applyEdit`. Start with propose/apply alone; best-of-N is a later increment gated on having sub-agent spawning (P2-8).

### P1-6. Host-executed tools / permission boundary (requestClientToolCall pattern)

**What:** The runtime never performs I/O; it emits typed tool calls to the host and awaits results. Our equivalent boundary already exists conceptually (tools execute in the browser/extension-host against VS Code APIs), so the task here is **hardening + consistency**: every tool result is a structured union (success | `{ errorMessage, patch? }`), permission checks against a per-agent tool whitelist happen at one chokepoint, and restricted tools emit error events instead of executing.

**Source:** `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/tools/tool-executor.ts`, `handlers/list.ts` (handler registry, ~40 handlers), `common/src/types/contracts/agent-runtime.ts`.

**Maps to:** `tools/toolRegistry.ts` + `executor/agentExecutor.ts`.

### P1-7. Terminal execution isolated from the UI process

**What:** Shell commands run through a "broker": a separate console-free helper process owns `child_process.spawn`; request/response over files with size caps; the TUI process never spawns shells directly; the broker self-reaps its process tree if the parent disappears (polls parent PID). Also: model-chosen timeouts clamped to 600s max; `process_type: 'SYNC' | 'BACKGROUND'`; output unions with `stdoutOmittedForLength`; POSIX-syntax mandate on all OSes (Git Bash on Windows) embedded in the tool description.

**Source:**
- `C:/Users/jobal/dev/freebuff/sdk/src/tools/run-terminal-command.ts`
- `C:/Users/jobal/dev/freebuff/cli/src/utils/terminal-command-broker.ts` + docs section in `C:/Users/jobal/dev/freebuff/docs/agents-and-tools.md` ("Console-free terminal command broker")

**Maps to:** `tools/terminalTools.ts`. In VS Code the cleaner equivalent is a dedicated `ITerminalService`/extension-host terminal or a detached helper — the requirement to satisfy: tool output must never fight the UI process, background processes must be reap, timeouts clamped.

### P1-8. Structured user-interaction tools (typed agent↔UI vocabulary)

**What:** `ask_user` — multi-choice questions with `{ question, header ≤18ch, options ≥2, multiSelect, validation: { minLength, maxLength, pattern, patternError } }`, UI auto-provides an "Other" free-text field. Plus `suggest_followups` (clickable next-prompt cards), `write_todos` (rewrite-all semantics), `render_ui` typed widgets where links are opaque runtime-resolved references (never trust model-transcribed URLs).

**Source:** `C:/Users/jobal/dev/freebuff/common/src/tools/params/tool/ask-user.ts`, `suggest-followups.ts`, `render-ui.ts`, `write-todos.ts`; `C:/Users/jobal/dev/freebuff/common/src/utils/ask-user-bridge.ts`; CLI side: `C:/Users/jobal/dev/freebuff/cli/src/hooks/use-ask-user-bridge.ts`.

**Maps to:** `tools/communicationTools.ts` (audit first — may partially exist) + chat UI. Note: our repo already has local "intake questions" work (see recent commit `9bc1183`) — reconcile rather than duplicate.

### P2-9. Dual-channel tool calls: XML-in-text with mid-stream execution

**What:** Besides native function-calling, the model may emit `<codebuff_tool_call>{json}</codebuff_tool_call>` inside its text stream; a stateful parser buffers partial tags across chunk boundaries and executes the tool **immediately, pausing the stream**. Benefits: works with ANY model (even without native tool support) and gives instant tool latency mid-response. Tool execution ordering is kept strictly sequential via promise-chaining (`previousToolCallFinished`), discovered-in-stream but executed serially — deterministic edit ordering with zero queue infrastructure. First call starts with an already-resolved promise (no deadlock waiting for stream end).

**Source:** `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/tools/stream-parser.ts` (660 ln), `src/tool-stream-parser.ts`, `src/util/stream-xml-parser.ts`, `C:/Users/jobal/dev/freebuff/common/src/util/partial-json-delta.ts` (incremental parse of partially-streamed JSON tool args for live UI).

**Maps to:** `executor/toolCallParser.ts` / `agentExecutor.ts`. Assess current streaming architecture first.

### P2-10. Stream-interruption recovery ("next step is the retry")

**What:** On dropped connection or output-limit stop: append a *tagged* system/user note describing the interruption and force another step — the model sees its own partial output and continues. Consecutive tagged recoveries are counted by walking the history tail; fail loudly after 3 (`MAX_CONSECUTIVE_STREAM_RECOVERIES`). Related hygiene at a single chokepoint: drop unanswered tool calls before the next request (strict providers 400 otherwise); neutralize lone UTF-16 surrogates (a truncated emoji can poison every subsequent request); convert tool-result images to user messages while preserving call/result adjacency.

**Source:** `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/tools/stream-parser.ts`; `C:/Users/jobal/dev/freebuff/common/src/util/messages.ts` (`convertCbToModelMessages`).

**Maps to:** `executor/retryPolicy.ts` + `executor/outputValidator.ts` — likely an upgrade of both.

### P2-11. Sub-agent orchestration (spawn_agents) + "enforce modes by toolset"

**What:** Sub-agents are declared as first-class tools (`spawnableAgents` → each becomes an ordinary tool the parent can call; pre-spawn validation catches agent-vs-tool confusion: `"X" is a tool, not an agent. Call it directly.`). Child config knobs: `inheritParentSystemPrompt` (shares system prompt with parent → prompt-cache hits), `includeMessageHistory`, `outputMode: last_message | all_messages | structured_output` + `outputSchema`, `spawnerPrompt` (the agent's description written FOR the parent model — doubles as the tool description). Critical safety lesson: **plan/read-only mode is enforced by removing write tools AND write-capable sub-agents from the toolset, not by prompt** — their experience: with prose-only enforcement, PLAN-mode users got whole features built and committed via the terminal sub-agent.

**Source:** `C:/Users/jobal/dev/freebuff/agents/base2/base2.ts` (581 ln orchestrator), `agents/base3.ts` (193 ln single-loop harness), `packages/agent-runtime/src/templates/prompts.ts` (`buildAgentToolSet`), `agents/types/agent-definition.ts` (full schema), `common/src/tools/params/tool/spawn-agents.ts`.

**Maps to:** `orchestrator/` + `executor/`. Large effort; depends on P1-6 hardening. Note freebuff's own trend: their newest default harness (base3) went back to a **single loop with no sub-agents** for the mainline — treat sub-agents as an opt-in "deep mode", not the default.

### P2-12. Session persistence: opaque RunState + crash-resume checkpoints

**What:** `RunState` (session + output) is opaque JSON the host holds and passes back as `previousRun` to continue. Checkpoints via `onStateSnapshot` every ~5s but only when `messageHistory` array identity changed (avoids deep-cloning multi-MB sessions while waiting on LLMs); JSON round-trip clone ~50× faster than `cloneDeep`; settle-then-save ordering so stale async writes can't clobber final state; synchronous flush from signal handlers; on interrupt: `dropUnansweredToolCalls`, append "work preserved" note, delta-adjust token counts instead of recounting.

**Source:** `C:/Users/jobal/dev/freebuff/sdk/src/run.ts`, `sdk/src/run-state.ts`, `cli/src/utils/run-state-storage.ts` (603 ln).

**Maps to:** `agentStoreService.ts` / `backgroundAgentService.ts`.

### P2-13. Steering: mid-turn user messages without abort

**What:** `drainSteeringMessages()` hook — the host can queue user messages while the agent works; they're injected at the next step boundary and keep the turn alive; undrained leftovers are re-queued at the front and their chat bubbles retracted.

**Source:** `C:/Users/jobal/dev/freebuff/sdk/src/run.ts` + `cli/src/utils/steering-buffer.ts`, consumed in `packages/agent-runtime/src/run-agent-step.ts`.

**Maps to:** chat UX in the agent panel — "type while the agent works".

### P2-14. Token-budget & model-context plumbing

**What:** Local token counting (GPT-4o tokenizer + 1.35× fudge factor, images = flat 1600 tokens, LRU cache) — they deliberately dropped a provider `count_tokens` round-trip that "added seconds of serial overhead to every step". Anthropic cache-control breakpoints (max 4) placed automatically on tagged message boundaries (`USER_PROMPT`, `STEP_PROMPT`, `LAST_ASSISTANT_MESSAGE`).

**Source:** `C:/Users/jobal/dev/freebuff/packages/agent-runtime/src/util/token-counter.ts`, `common/src/util/messages.ts`, `common/src/util/tokens.ts` (cache-read-aware accounting).

**Maps to:** `executor/budgetTracker.ts` upgrade.

### P2-15. Eval harness (BuffBench) for our agent

**What:** Commit-reconstruction tasks on real repos (check out parent commit, ask agent to reimplement the commit, diff against reality), parallel runners, dual AI judges (averaged, median analysis kept), final-check commands (tests/lints), trace + meta analyzers.

**Source:** `C:/Users/jobal/dev/freebuff/evals/buffbench/` — `run-buffbench.ts`, `agent-runner.ts`, `judge.ts`, `gen-evals.ts`.

**Maps to:** new `evals` harness for NeuralInverse's agent (run against fixture repos), so future agent changes are regression-tested.

### Reference: notable agent-definition patterns (for later prompt work)

From `C:/Users/jobal/dev/freebuff/agents/` — useful when we get to prompt/behavior quality, not infrastructure:
- `basher.ts` — single-command executor that returns **raw output untouched when ≤ ~2000 chars** ("strictly more information than a summary of it"); only spends an LLM round-trip summarizing genuinely noisy output
- `reviewer/code-reviewer.ts` — reviewer with **zero tools** + `inheritParentSystemPrompt` + full history → reviews edits in-context with a one-line spawn prompt
- `thinker/thinker.ts` — no tools, one step, strips its own `<think>` tags before returning output
- `researcher/researcher-web.ts` — "may not write a final answer until ≥3 pages fetched with read_url"; `stepPrompt: "Continue. Respond with either more tool calls or your final written answer"` fixes models that stop silently after a tool result
- `file-explorer/code-searcher.ts` etc. — "mechanical" agents: `handleSteps` generator loops over params and run tools with **no LLM call at all** (composable but free)
- Structured outputs include a `lessons[]` field ("advice for future runs: workarounds discovered") fed back into the next spawn
- base2's worked `<example>` choreography in the prompt demonstrates the exact intended parallel spawn sequence

---

## 3. Suggested task-breakdown structure

Group tasks so each is independently landable. Suggested waves:

**Wave 1 — Editing & file tools (P0-1, P1-4, P0-3):** deterministic str_replace with input repair → windowed reads → referencedBy annotations. All touch `tools/fsTools.ts` + `context/`; no architectural change.

**Wave 2 — Resilience (P2-10, P2-14):** stream-recovery tags + history hygiene chokepoint; budget tracker upgrade with local token counting.

**Wave 3 — Compaction (P0-2):** port compact-history with role-separated budgets and cache-aware trigger; wire into agentExecutor pre-call.

**Wave 4 — UX tools (P1-8, P2-13, P1-7):** ask_user/followups/todos vocabulary (after auditing communicationTools.ts), steering buffer, terminal broker hardening.

**Wave 5 — Review flow (P1-5):** propose/apply split with inline diff review in the editor.

**Wave 6 — Architecture (P1-6, P2-9, P2-11, P2-12):** tool-executor chokepoint hardening, dual-channel streaming tool calls, optional sub-agent spawning with toolset-enforced modes, RunState persistence/checkpoints.

**Wave 7 — Quality loop (P2-15):** eval harness.

Each task should define: touched NeuralInverse files, source freebuff files to consult, acceptance criteria (behavior-level, not just "compiles"), and a validation step per `.github/copilot-instructions.md`.

---

## 4. Constraints & gotchas

1. **Do not add freebuff as a dependency.** Copy/adapt code into `neuralInverse` contrib, preserving Apache 2.0 attribution (NOTICE terms) in a `THIRD-PARTY-NOTICES` file or file headers.
2. **Runtime mismatch:** freebuff is Bun + Zod v4 + AI SDK v7 + ESM. VS Code's browser layer is its own module system with strict layering (`vs/base`, `vs/platform`, `vs/workbench`) — port *logic and schemas*, not imports. Check what Zod (if any) is already vendored in our fork before introducing one.
3. **Prompt-embedding style differs:** freebuff embeds behavioral policy (git-commit guides, timeout rules, POSIX-on-Windows) directly in tool descriptions with generated example calls (`common/src/tools/params/utils.ts` → `$getNativeToolCallExampleString`). Our `toolRegistry` descriptions should adopt this documentation style.
4. **Windows specifics:** freebuff fought real Windows battles (console-free brokers, bunfs WASM resolution, Git Bash POSIX mandates, `> nul` creating undeletable files). Our fork IS Windows-first — mine their `WINDOWS.md` and terminal tool description for rules we should adopt.
5. **base3 vs base2 lesson:** freebuff's production default moved from heavy multi-agent orchestration (base2) to a single-loop harness (base3) with in-process compaction — sub-agents remain only for deep/max modes. Mirror that: keep our default loop simple; make sub-agents opt-in.
6. **Uncommitted state:** `tools/toolRegistry.ts` and `tools/live-patch.py` have local modifications in our repo; review them before planning changes to the registry.
7. **Verification of freebuff behavior:** when porting, read the actual source at the paths listed (they are accurate as of this analysis, commit `7b2113670`); freebuff is a synced snapshot repo and paths may drift on future pulls.

---

## 5. Quick reference: key freebuff files by topic

| Topic | File |
|---|---|
| Agent step loop | `packages/agent-runtime/src/run-agent-step.ts` |
| Stream → tool pipeline | `packages/agent-runtime/src/tools/stream-parser.ts` |
| Tool execution/validation/repair | `packages/agent-runtime/src/tools/tool-executor.ts` |
| Tool handler registry | `packages/agent-runtime/src/tools/handlers/list.ts` |
| Tool schemas (all ~40) | `common/src/tools/params/tool/*.ts` |
| Input repair helpers | `common/src/tools/params/utils.ts` |
| Compaction (runtime copy) | `packages/agent-runtime/src/compact-history.ts` |
| Compaction policy table | `common/src/constants/compaction-policy.ts` |
| Read budgets/windowing | `common/src/util/file-read-limits.ts` |
| Message hygiene chokepoint | `common/src/util/messages.ts` |
| Token counting | `packages/agent-runtime/src/util/token-counter.ts` |
| code-map scoring/reverse deps | `packages/code-map/src/parse.ts` |
| File tree w/ tokens | `common/src/util/file.ts` (`printFileTreeWithTokens`) |
| Terminal broker | `sdk/src/tools/run-terminal-command.ts`, `cli/src/utils/terminal-command-broker.ts` |
| Session persistence | `sdk/src/run.ts`, `cli/src/utils/run-state-storage.ts` |
| Steering | `sdk/src/run.ts` + `cli/src/utils/steering-buffer.ts` |
| Orchestrator agent | `agents/base2/base2.ts` |
| Single-loop agent | `agents/base3.ts` |
| Agent definition schema | `agents/types/agent-definition.ts` |
| Reviewer / thinker / basher | `agents/reviewer/code-reviewer.ts`, `agents/thinker/thinker.ts`, `agents/basher.ts` |
| Eval harness | `evals/buffbench/run-buffbench.ts` |

(All paths relative to `C:\Users\jobal\dev\freebuff`.)

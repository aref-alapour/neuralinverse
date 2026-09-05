# Handoff: ComfyUI → Task Breakdown for NeuralInverse

## Purpose of this document

You are receiving this document to perform **task breakdown**: turn it into a concrete, ordered set of implementation tasks for porting ComfyUI's workflow-graph technology into **NeuralInverse** (a VS Code fork, all-TypeScript agent/workflow editor).

This document is self-contained. Verify current repo state before finalizing tasks (working trees may contain uncommitted modifications).

## 0. Recorded project decisions (do not re-litigate)

1. **Code will be taken directly, not just patterns.** ComfyUI is GPL-3.0; the project decision is that NeuralInverse is internal-only and the license is accepted. Do not add license warnings to tasks. One engineering rule survives regardless: **every ported file gets a provenance header** (see §6) so ported code stays identifiable for maintenance and any future change of plans.
2. **Language gap is the central technical fact:** ComfyUI is Python; NeuralInverse is TypeScript. "Taking the code" therefore means one of two tracks, both planned here:
   - **Track A — faithful TS ports** of the execution-engine modules (§2) into the NeuralInverse browser layer. This is the default track and the main body of work.
   - **Track B — run ComfyUI itself as an embedded local backend** (§3) for AI media-generation features, controlled from the editor over HTTP/WebSocket. Zero porting; gives the editor image/video generation capability.
3. Scope priority: NeuralInverse's `composer/` + `orchestrator/` (the workflow canvas) is the primary beneficiary of Track A. Do NOT port ComfyUI's model-management / diffusion / VRAM subsystems (`comfy/model_management.py`, samplers, `ops.py`, quantization) — they are irrelevant to a TS editor and useless in translation.

---

## 1. The two codebases

### 1.1 Source: ComfyUI

- **Location (already cloned):** `C:\Users\jobal\dev\comfyui` (sibling of the neuralinverse repo)
- **Upstream:** https://github.com/comfy-org/comfyui, version **0.34.0**, HEAD `acb2a019` (active daily development)
- **What it is:** a node-graph execution engine for AI content generation: Python + aiohttp server; the Vue frontend is a separate repo consumed as pip package (irrelevant to us — NeuralInverse has its own canvas).
- **Layout (only the parts that matter for Track A):**

| Path | Role |
|---|---|
| `execution.py` (~63KB) | `PromptExecutor`, `validate_prompt()`, `validate_inputs()`, input resolution, batch-list zipping, node execution |
| `comfy_execution/graph.py` | `DynamicPrompt`, `TopologicalSort` with re-staging, `ExecutionList` |
| `comfy_execution/caching.py` | input-signature cache keys, `HierarchicalCache`, `LRUCache`, `RAMPressureCache` |
| `comfy_execution/graph_utils.py` | `is_link()`, `GraphBuilder` for runtime subgraphs, `ExecutionBlocker` |
| `comfy_execution/validation.py` | link type-compatibility (set semantics) |
| `comfy_execution/jobs.py` | modern jobs view over queue+history |
| `server.py` | HTTP+WS surface; `object_info` node-schema export (`node_info()`, line ~751) |
| `nodes.py` (~110KB, 2601 ln) | node contract, `NODE_CLASS_MAPPINGS`, `load_custom_node()` |
| `comfy/comfy_types/node_typing.py` | typed node contract (InputTypeDict, IO enum) |
| `comfy_api/latest/_io.py` | V3 schema-based node API (DynamicCombo, Autogrow) |
| `comfy_api_nodes/` | external-API node pattern (pricing badge, proxied auth) |
| `folder_paths.py` | directory registry + mtime-cached filename lists |
| `script_examples/basic_api_example.py` | canonical prompt-JSON example |

### 1.2 Target: NeuralInverse

- **Repo:** `C:\Users\jobal\dev\neuralinverse` (VS Code fork). Follow `AGENTS.md` + `.github/copilot-instructions.md` for build/validation.
- Agent subsystem: `src/vs/workbench/contrib/neuralInverse/browser/` (~132 TS files).
- Subsystems relevant to this handoff (audit these BEFORE task breakdown — their internals may have changed):

| Area | Files | Assumed state |
|---|---|---|
| Workflow canvas | `composer/` — `model/composerModel.ts`, `model/composerHistory.ts`, `model/composerSerializer.ts`, `nodes/nodeRegistry.ts`, `nodes/nodeRenderer.ts`, `edges/edgeValidator.ts`, `edges/edgeRenderer.ts`, `canvas/*.ts`, `panels/*` | Visual node canvas exists; execution model maturity unknown — audit |
| Orchestration | `orchestrator/workflowOrchestrator.ts`, `orchestrator/workflowComposer.ts`, `orchestrator/approvalGate.ts`, `orchestrator/conditionalEvaluator.ts` | Some execution flow exists — audit and decide: extend vs replace with the ported engine |
| Executor | `executor/agentExecutor.ts`, `executor/toolCallParser.ts`, `executor/retryPolicy.ts` | Single-agent LLM loop (different concern; only shares event/telemetry plumbing) |
| Tools | `tools/toolRegistry.ts` + per-domain tool files | Tool registry for the LLM agent — **not** the node graph; keep concerns separate |
| Background agents | `backgroundAgentService.ts`, `agentManagerPart.ts`, `agentStoreService.ts` | Long-running task surface; Track A queue integrates here |

Key architectural decision for the next session: where the ported engine lives. Suggested: `src/vs/workbench/contrib/neuralInverse/browser/workflow-engine/` (new), with `composer/` and `orchestrator/` refactored to sit on top of it.

---

## 2. Track A — TS port of the graph execution engine

Port targets, ordered. Each item: source → target → semantics to preserve → acceptance criteria.

### A1. Graph format & core types

**Source:** prompt JSON format (`script_examples/basic_api_example.py`, `execution.py:987` `is_link` handling, `comfy_execution/graph_utils.py:1-10`).

**Port:** a new `workflow-engine/graph.ts`:
- `WorkflowGraph = Map<NodeId, { classType: string; inputs: Record<string, unknown> }>`
- Link representation: a 2-element array `[sourceNodeId, outputSlotIndex]`. Detect via `isLink(value)`. A widget value that is legitimately a list must be wrapped (`{"__value__": [...]}` — keep this exact escape-hatch semantics).
- `DynamicGraph` equivalent of `DynamicPrompt` (`graph.py:21-62`): base graph + runtime-added **ephemeral nodes**, with parent/display-id maps so events on ephemeral nodes attribute back to the visible node that created them (`getRealNodeId` / `getDisplayNodeId`).

**Acceptance:** graphs round-trip through `composerSerializer`-compatible JSON; ephemeral-node parent attribution works.

### A2. Validation

**Source:** `execution.py:846-1120` (`validate_inputs`), `execution.py:1128-1247` (`validate_prompt`), `comfy_execution/validation.py` (type compatibility).

**Port:** `workflow-engine/validation.ts`. Preserve:
- Recursive validation from each output node (`OUTPUT_NODE = true`) with memoization.
- **Cycle detection** producing a human-readable chain `"id (class) -> id (class)"` error per node on the path.
- The structured per-node error shape — this is the contract the canvas UI will render:
  ```ts
  NodeErrors { errors: Array<{ type; message; details; extraInfo }>; dependentOutputs: NodeId[]; classType }
  ```
- Error taxonomy: `required_input_missing`, `bad_linked_input`, `return_type_mismatch`, `value_smaller_than_min` / `value_bigger_than_max`, `value_not_in_list`, `dependency_cycle`, `invalid_input_type`, `custom_validation_failed`, `prompt_no_outputs`, `missing_node_type` (with the friendly "custom node may not be installed" message using `_meta.title`).
- Type compatibility with **set semantics** over comma-joined type strings (`"FLOAT,INT"` = union, `"*"` = wildcard), overlap = compatible. Translate the legacy `__ne__` idiom as plain set intersection.
- In-place coercion of INT/FLOAT/STRING/BOOLEAN widget values; combo-membership check that suppresses echoing option lists > 20 entries.
- Per-node `validateInputs` hook (node-defined custom validation) that, when present, takes over validation for that node's inputs, and receives the resolved link types.

**Acceptance:** given fixture graphs (valid, cycle, missing input, type mismatch, out-of-range), the port returns byte-equivalent error structures to the Python implementation on the same inputs.

### A3. Topological execution with re-staging (the heart)

**Source:** `comfy_execution/graph.py:106-342` (`TopologicalSort`, `ExecutionList`), `execution.py:727-843` (`execute_async`), `execution.py:438-662` (single-node `execute`).

**Port:** `workflow-engine/executionList.ts` + `workflow-engine/executor.ts`. Preserve:
- Iterative DFS dependency discovery from seed output nodes; inputs flagged `lazy` are NOT followed unless requested; cached upstream nodes are skipped.
- **blockCount / blocking strong-link bookkeeping** (Kahn-style dissolve): `getReadyNodes()` returns nodes with `blockCount === 0`.
- **The re-staging mechanism** — a node returns `PENDING` plus a request to convert inputs to strong links; it re-enters the ready set once those dependencies complete. This single mechanism powers lazy inputs, async nodes, and subgraph expansion; do not split it into three features.
- External blocks for async nodes: the executor awaits; when the async task completes it unblocks and the event wakes (`unblockedEvent` → in TS, a promise the scheduler awaits).
- **UX-friendly node picking** (`ux_friendly_pick_node`, `graph.py:275-312`): prefer output nodes and async nodes, then nodes 1–2 hops from an output — previews surface early.
- Runtime cycle detection over dynamic links (`get_nodes_in_cycle` reverse dissolve).
- Execution results tri-state: `SUCCESS | PENDING | FAILURE`; failure handler mirrors `handle_execution_error` (stop siblings, mark dependents).
- Per-node: input resolution (`get_input_data` — links from upstream output cache, constants become 1-element arrays, hidden inputs injected: `PROMPT`, `DYNPROMPT`, `UNIQUE_ID`, `EXTRA_PNGINFO`), then batch-list zipping (`slice_dict` — shorter input lists repeat their last element = implicit broadcasting; `INPUT_IS_LIST`/`OUTPUT_IS_LIST` fan-out flags).

**Acceptance:** async test graph (two slow async nodes + one sync consumer) executes interleaved, not serialized; a Switch-like lazy node executes only the selected branch; all three behaviors come from the same re-staging path.

### A4. Node definition contract (TS flavor)

**Source:** `nodes.py` V1 contract (class attributes; see `CheckpointLoaderSimple` at nodes.py:616 and `KSampler` at 1597), typed vocabulary in `comfy/comfy_types/node_typing.py`, V3 dynamic inputs in `comfy_api/latest/_io.py`.

**Port:** `workflow-engine/nodeTypes.ts` + registry. In TS the contract becomes a typed interface instead of duck-typed class attributes:
```ts
interface WorkflowNodeDef {
  id: string;                       // class_type
  displayName?: string; category: string;   // slash-delimited palette path
  inputTypes(): NodeInputSpec;      // { required, optional, hidden }
  outputs: readonly string[];       // RETURN_TYPES
  outputNames?: readonly string[];
  isOutputNode?: boolean;           // OUTPUT_NODE
  execute(inputs, ctx): Promise<NodeResult | 'PENDING' | ...>;
  isChanged?(inputs): unknown;      // IS_CHANGED fingerprint
  validateInputs?(inputs, linkTypes): true | string;
  checkLazyStatus?(available: string[]): string[];  // names still needed
}
```
- Input spec entries: `{ type: string | string[] /* combo options */, options: { default?, min?, max?, step?, lazy?, tooltip?, controlAfterGenerate? } }`. Combo = live list (see A7 for filesystem-backed combos).
- Port the **hidden-input control channel**: `PROMPT`, `DYNPROMPT`, `UNIQUE_ID`, `EXTRA_PNGINFO` — nodes can see the whole workflow and report metadata.
- Port `ExecutionBlocker` (`graph_utils.py:140-155`): a value-level veto that propagates through links; with a message it surfaces as a synthetic execution error, silent blocks short-circuit downstream.
- Do NOT port the V1/V3 dual system — implement the V3-style typed contract only, but keep the V1 vocabulary (type strings, combos-as-lists) so prompts/serialized graphs stay format-compatible.
- Adapt the existing `composer/nodes/nodeRegistry.ts` to produce `WorkflowNodeDef`s (audit its current shape first).

**Acceptance:** the canvas palette lists nodes from the registry with categorized paths; serialized composer graphs execute through the new engine.

### A5. Caching subsystem

**Source:** `comfy_execution/caching.py` (all), `execution.py:60-101` (`IsChangedCache`).

**Port:** `workflow-engine/caching.ts`. Preserve:
- Two caches: **output cache** (node results, keyed by input signature) and **object cache** (node instance state, keyed by `[nodeId, classType]` — survives graph edits).
- **Input signature = the node plus its entire ordered ancestry**: `[classType, isChangedValue, [inputName, value | ["ANCESTOR", index]]]` — ancestor references by deterministic index (input-name-sorted DFS), NOT by node id, so renamed-but-identical subgraphs hit cache. Include `nodeId` in the signature only for nodes marked non-idempotent or consuming `UNIQUE_ID`.
- **Unhashable → never-equal poisoning:** in Python this is `NaN` (never `==` itself). In TS, model it as a dedicated `UNHASHABLE` symbol/singleton whose `equals` always returns false — never a false cache hit.
- `IS_CHANGED` fingerprints (e.g. file mtime) executed with constants only, memoized into the node record, exceptions → poisoned value.
- Eviction strategies as pluggable interfaces: `HierarchicalCache` (subcaches for expanded subgraphs), `LRUCache` (generation counter), `RAMPressureCache`. For the editor, the practically-needed one is **LRU + signature invalidation** (`cleanUnused()` deletes entries whose keys vanished from the new prompt); port RAM-pressure scoring only if the engine runs in a worker with large outputs.
- **Partial re-execution:** only subgraphs whose signature changed re-run; untouched outputs are reported as `execution_cached` so the UI dims them. Also port `partial_execution_targets` (execute a subset, `server.py:1106`).

**Acceptance:** change one widget value in a 10-node diamond graph → exactly the affected path re-executes, upstream and sibling branches come from cache; deleting a branch drops its cache entries.

### A6. Queue, run lifecycle, progress protocol

**Source:** `execution.py:1251-1411` (`PromptQueue` — heapq + front-jump), `main.py:351-446` (`prompt_worker`), `server.py:269-327` (WS protocol), `comfy_execution/progress.py` (progress registry), `execution.py:700-712` (error payloads).

**Port:** `workflow-engine/queue.ts` + event types. Translation notes:
- Python's worker thread + per-prompt `asyncio.run()` becomes the VS Code browser event loop: a serial async runner (`while (item = queue.take()) await executor.execute(...)`) — possibly inside a web worker if node work is CPU-heavy. Keep the invariant: **one prompt executing at a time; queue mutations observable**.
- Event stream (map to your existing canvas/agent event bus): `execution_start → execution_cached → (executing → progress* → executed)* → execution_success | execution_error | execution_interrupted → executing{node: null}`.
- Error payload shape: `{ promptId, nodeId, nodeType, exceptionMessage, exceptionType, executed, currentInputs, currentOutputs }` — canvas uses `currentInputs` to highlight the failing widget.
- **Interrupts:** Python uses a `BaseException` checked at node start and every progress tick. In TS: an `AbortSignal` checked at the same two points; interrupt must be **atomic per prompt** (can't leak onto the next queued run) and must preserve completed partial outputs.
- `front: true` queue insertion and `delete(ids)` / `clear()` operations.

**Acceptance:** two queued runs; interrupt the first mid-node → it ends as `execution_interrupted` with partial outputs preserved, second run unaffected, `executing{node:null}` always terminal.

### A7. Node schema export (object_info) & dynamic combos

**Source:** `server.py:751-798` (`node_info`), `folder_paths.py` (mtime-cached filename lists).

**Port:** `workflow-engine/nodeInfo.ts` — a single function producing, for every registered node: `{ input, inputOrder, output, outputIsList, outputNames, name, displayName, description, category, outputNode, deprecated/experimental flags, searchAliases }`. This is what the palette, auto-completion, and connection-type checking consume; per-node serialization failures must not break the whole payload.
- **Filesystem-as-data-source combos:** combos backed by directory scans with **mtime-based cache validation** (directory mtime changes when files are added/removed) + a per-request memo so multiple reads in one validation pass don't rescan. In VS Code: back this with the workspace fs API.

**Acceptance:** palette and validation both derive from `nodeInfo` — single source of truth; adding a file to a watched folder refreshes combos without restart.

### A8. Optional but high-value ports

- **Jobs view** (`comfy_execution/jobs.py` + `/api/jobs` routes): a modern status/cancel API over queue+history — fits `backgroundAgentService.ts`.
- **History store** (`execution.py:1280-1291`): capped (10k) FIFO of past runs with outputs — maps to `composerHistory.ts` / workspace storage.
- **Node replacement registry** (`app/node_replace_manager.py`): apply registered node-renaming maps to prompts before validation — cheap future-proofing for evolving node packs.
- **API-node pattern** (`comfy_api_nodes/util/client.py`, `nodes_anthropic.py`): retries with Retry-After/rate-limit backoff, poll-based jobs, **live pricing badge** (cost expression evaluated by UI), and auth injected at the boundary so secrets never flow through the graph — port the pattern for paid AI-service nodes in the editor.
- **OOM-style failure UX** (execution.py:641-647): classify known failure signatures into actionable tips attached to the error event.

---

## 3. Track B — embed ComfyUI as a local backend (optional, decide separately)

If NeuralInverse should offer image/video generation: run the cloned ComfyUI as a managed local service instead of porting anything.

- Spawn `python main.py --port 8188 --disable-all-custom-nodes` (+ `--enable-manager` if desired) as a managed child process from a NeuralInverse service (extension-host side on Desktop; note Python dependency detection/install UX).
- Drive it with the documented API: `POST /prompt` (queue a graph), `GET /ws?clientId=` (event stream — same event types as A6), `GET /object_info` (build a native palette in the editor canvas from ComfyUI's own node catalog), `POST /interrupt`, `GET /history/{id}`, `POST /upload/image`, `GET /view?filename=`.
- The prompt JSON produced by Track A's graph format is exactly what `POST /prompt` consumes — **Tracks A and B compose**: the editor's engine runs agent/workflow nodes natively and hands media-generation subgraphs to the embedded ComfyUI.
- `script_examples/basic_api_example.py` and `websockets_api_example.py` are the reference integrations.

Track B tasks: process lifecycle manager, health/version handshake (`/system_stats` incl. `required_frontend_version` drift check), clientId correlation, artifact retrieval into the editor, failure surfacing. Keep it strictly optional — independent of Track A waves.

---

## 4. Python → TypeScript translation notes

Load-bearing differences to encode into every task:

1. **Concurrency model:** worker-thread + per-prompt asyncio loop → single-threaded VS Code event loop with async functions; the "external block" wake-up (`unblockedEvent.set()`) becomes a resolved promise. CPU-heavy node work belongs in a web worker; the engine core should stay UI-thread-safe.
2. **`BaseException` interrupts → `AbortSignal`** checked at node start + every progress tick; never catch-and-swallow (Python made it `BaseException` precisely so node `except Exception` blocks can't eat it — in TS, rethrow `AbortError`).
3. **Deterministic ordering:** Python dicts preserve insertion order — the ancestry-index signature depends on it. Use `Map`/arrays; where the Python code sorts input names (`get_ordered_ancestry`), port the sort explicitly.
4. **NaN-poisoning:** Python relies on `NaN != NaN` inside hash-based lookup. In TS, implement the cache key equality check explicitly with an `Unhashable` sentinel — do not depend on `Object.is(NaN, NaN) === false` subtleties deep in a Map.
5. **heapq priority queue → small sorted array or binary heap**; queue sizes are tiny, correctness of `front: true` matters more than big-O.
6. **`weakref.finalize` cleanup → explicit disposal** in a `dispose()` on the engine/services (VS Code `IDisposable` convention).
7. **Exceptions-as-data:** validation and execution errors are VALUES in the protocol (the structured error objects), not thrown across boundaries. Keep that; only interrupts are control-flow.
8. **No `torch` concepts:** `torch.inference_mode` context, dtype/device fields — drop entirely.

---

## 5. Suggested task waves

**Wave 0 — Audit & skeleton (prereq):** read current `composer/` + `orchestrator/` internals; decide extend-vs-replace; create `workflow-engine/` module with graph types (A1). Land the decision note in the module README.

**Wave 1 — Validate:** A2 validation engine + fixture tests (port Python's `tests/execution/` graph fixtures where useful: `C:/Users/jobal/dev/comfyui/tests/execution/`, `tests-unit/execution_test/`). Wire into `edgeValidator`/canvas errors.

**Wave 2 — Execute:** A3 executor + A4 node contract; migrate 3–5 real composer node kinds onto `WorkflowNodeDef`; run graphs end-to-end headless (unit-level).

**Wave 3 — Cache:** A5 output+object caches with signature keys; `execution_cached` events; partial re-execution. This is the flagship user-visible win — prioritize demoing "edit one node → only downstream re-runs".

**Wave 4 — Queue & lifecycle:** A6 queue/interrupts/progress protocol onto `backgroundAgentService`; A7 nodeInfo as single schema source for the palette.

**Wave 5 — Polish ports:** A8 items (jobs view, history, replacements, API-node pattern).

**Wave 6 (optional) — Track B** embedded ComfyUI service.

Each task must define: touched NeuralInverse files, source ComfyUI file+line refs, acceptance criteria (behavior-level), validation per `.github/copilot-instructions.md`.

---

## 6. Provenance & maintenance rules

- Every file ported from ComfyUI starts with a header comment:
  `// Ported from comfyui/<path> (GPL-3.0, comfy-org/comfyui @ acb2a019) — ported for internal use.`
- Maintain `workflow-engine/PORTED-FROM.md` listing each ported module, its source path, and upstream commit. Purpose: maintenance (upstream sync, future refactors) and keeping the ported surface identifiable if project plans ever change.
- Upstream moves fast (daily commits). Before porting a module, `git -C C:/Users/jobal/dev/comfyui log --oneline -5 -- <path>` to check for recent changes to it.
- Do not import freebuff/ComfyUI code as dependencies; both are copies-in-tree per project decision (freebuff is Apache-2.0, ComfyUI GPL-3.0 — both recorded decisions in FREEBUFF-HANDOFF.md and here).

---

## 7. Quick reference: ComfyUI source map for Track A

| Topic | File (relative to `C:\Users\jobal\dev\comfyui`) |
|---|---|
| Prompt format example | `script_examples/basic_api_example.py` |
| Link detection / graph utils | `comfy_execution/graph_utils.py` |
| Dynamic graph + topological sort | `comfy_execution/graph.py` |
| Validation (big) | `execution.py:846-1247` |
| Type compatibility | `comfy_execution/validation.py` |
| Input resolution & node execution | `execution.py:159-662` |
| Batch-list zipping | `execution.py:243-319` (`slice_dict`) |
| Caches & signatures | `comfy_execution/caching.py` |
| IS_CHANGED cache | `execution.py:60-101` |
| Queue | `execution.py:1251-1411` |
| Worker lifecycle | `main.py:351-446` |
| WS event protocol | `server.py:269-327`, payloads in `execution.py:700-743` |
| Node schema export | `server.py:751-798` |
| Node contract + loaders | `nodes.py` (contract ~616/1597/1660; loader ~2244) |
| Typed contract vocabulary | `comfy/comfy_types/node_typing.py` |
| V3 dynamic inputs | `comfy_api/latest/_io.py` |
| Folder-backed combos | `folder_paths.py` |
| API-node client pattern | `comfy_api_nodes/util/client.py`, `comfy_api_nodes/nodes_anthropic.py` |
| Jobs view | `comfy_execution/jobs.py`, `server.py:821-1043` |
| Execution tests to mirror | `tests/execution/`, `tests-unit/execution_test/` |

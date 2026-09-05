# AI Coding Tools & Automation Landscape — GitHub Research (September 2026)

**For:** NeuralInverse (VS Code fork with in-fork agent subsystem) — source-mining for patterns and code to port.
**Method:** 8 parallel background research agents + live GitHub API verification (`gh`, authenticated) on **2026-09-05**. All repos below are **shallow-cloned** under `projects/<category>/<name>/` (gitignored; see `projects/repos-verified.tsv` and `projects/batch1-stats.tsv` for raw data).
**License policy (user decision):** "open source" = code publicly accessible. License is metadata only (internal project, not sold). Permissively-licensed repos (MIT/Apache/BSD) are preferred for direct copying; GPL/AGPL and source-available (FSL/BUSL/Sustainable-Use) repos are still mined for code per project decision — keep provenance headers per the ComfyUI precedent.

**Research status caveat:** 1 of 8 deep-research reports completed (VS Code forks & ecosystem — the most important one for us, summarized in §3). The other 7 agents were killed mid-run by an API quota exhaustion (**resets 2026-09-08 22:28**). All stats below were re-verified live via the GitHub API instead, so the catalog is complete and accurate; only the per-project prose depth for 7 categories is pending — rerun after reset.

---

## 1. Master catalog (all verified via GitHub API, 2026-09-05)

Stars/license/archived/last-push are live API values. `→` = org/name moved; the clone follows the redirect.

### Terminal coding agents — `projects/terminal-agents/`

| Repo | ★ | License | Status | What it is / why it matters |
|---|---|---|---|---|
| [anomalyco/opencode](https://github.com/anomalyco/opencode) (formerly sst) | 204,101 | MIT | Active daily | The largest OSS agent project; terminal-first client/server agent. Kilo's CLI forks it; cpkt9762 embeds it in a VS Code fork. |
| [openai/codex](https://github.com/openai/codex) | 121,542 | Apache-2.0 | Active daily | OpenAI's Rust-based CLI agent; reference sandboxing + approval model. |
| [aaif-goose/goose](https://github.com/aaif-goose/goose) (→ from block) | 53,915 | Apache-2.0 | Active daily | Extensible Rust agent, MCPs as first-class extensions. |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 48,747 | Apache-2.0 | Slowing (last push 2026-05) | The original AI pair programmer; best repo-map / context-packing research in OSS. |
| [charmbracelet/crush](https://github.com/charmbracelet/crush) | 27,911 | FSL-1.1-MIT (source-available; files auto-MIT 2y after publish) | Active daily | Gorgeous Go TUI agent; LSP-native context. |
| [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code) | 27,657 | Apache-2.0 | Active daily | Qwen's terminal agent (Gemini CLI lineage). |
| [plandex-ai/plandex](https://github.com/plandex-ai/plandex) | 15,621 | MIT | Dormant (2025-10) | Branch/commit-oriented "build & plan" agent — unique reconciliation model worth reading even if dormant. |
| [bytedance/trae-agent](https://github.com/bytedance/trae-agent) | 12,070 | MIT | Active | LLM-agnostic SWE-style agent from the Trae IDE team; portable agent loop. |
| [aws/amazon-q-developer-cli](https://github.com/aws/amazon-q-developer-cli) | 1,985 | Apache-2.0 | Active | Amazon Q terminal agent (was awslabs). |
| [gptme/gptme](https://github.com/gptme/gptme) | 4,410 | MIT | Active | Local-first terminal agent, long-running sessions, tool use, browser. |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | 106,815 | Apache-2.0 | Active daily | Google's CLI agent. |
| [Factory-AI/droid-sdk-typescript](https://github.com/Factory-AI/droid-sdk-typescript) | 38 | — | Active | Droid CLI core is closed; this SDK + `Factory-AI/droid-action`/`droid-code-review` are the readable parts. |

### VS Code forks & from-scratch editors — `projects/vscode-forks-and-editors/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [zed-industries/zed](https://github.com/zed-industries/zed) | 89,771 | GPL/AGPL mix (NOASSERTION at root) | Active | Rust, GPUI. Zeta edit prediction, assistant panel, ACP. The from-scratch benchmark. |
| [lapce/lapce](https://github.com/lapce/lapce) | 38,820 | Apache-2.0 | Active again (pushed 2026-09) | Rust/Floem editor; earlier "dormant" reputation outdated. |
| [voideditor/void](https://github.com/voideditor/void) | 28,813 | Apache-2.0 | **Archived 2026-06-02** | NeuralInverse's own ancestor & the best in-fork AI blueprint (see §3). |
| [VSCodium/vscodium](https://github.com/VSCodium/vscodium) | 33,116 | MIT | Active nightly | Build/telemetry/branding surgery recipe + OpenVSX wiring. |
| [trypear/pearai-master](https://github.com/trypear/pearai-master) (+ `pearai-app` ★708 MIT, `pearai-submodule` ★121 Apache) | 770 | mixed | App frozen 2025-05; submodules active | Hybrid strategy: minimal fork + vendored Continue-fork extension. |
| [OpenCortexIDE/cortexide](https://github.com/OpenCortexIDE/cortexide) | 167 | MIT | Active | Largest active Void continuation (NeuralInverse is also listed in `voideditor/void-forks` ★43). |
| [cpkt9762/opencode-vscode-ide](https://github.com/cpkt9762/opencode-vscode-ide) | 16 | MIT | Active | VS Code fork embedding opencode as sidebar SPA via Electron-main loopback — the "fork shell + external agent runtime" pattern. |
| [voideditor/void-builder](https://github.com/voideditor/void-builder) | 36 | MIT | 2025-10 | Void's public package/sign/auto-update pipeline (VS Code's official one is private). |
| [agentclientprotocol/agent-client-protocol](https://github.com/agentclientprotocol/agent-client-protocol) | 4,153 | Apache-2.0 | Active | Zed's ACP — drive any agent (opencode, gemini-cli, claude code) from any editor over stdio JSON-RPC. Architecturally important for us. |

### IDE extension agents — `projects/ide-extensions/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [cline/cline](https://github.com/cline/cline) | 67,482 | Apache-2.0 | Very active | Root of the Roo/Kilo lineage; plan/act modes, checkpoints, MCP client, browser tool; now also an SDK/CLI. |
| [continuedev/continue](https://github.com/continuedev/continue) | 35,764 | Apache-2.0 | Maintained (acquired by Cursor; code stays open) | Best-structured UI-agnostic AI subsystem: `core/` (llm, autocomplete, indexing+LanceDB, edit/apply, protocol) + one webview for VS Code & JetBrains. |
| [Kilo-Org/kilocode](https://github.com/Kilo-Org/kilocode) | 27,176 | MIT | Very active (Anaconda-owned) | Cline→Roo→Kilo lineage; VS Code + JetBrains + CLI (opencode fork); 5 built-in agents, `kilo run --auto` for CI, MCP marketplace. |
| [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) | 24,311 | Apache-2.0 | **Archived 2026-05-15** | Died at 3M installs; community successor Zoo-Code. Memory Bank + custom modes live on in the archive. |
| [Zoo-Code-Org/Zoo-Code](https://github.com/Zoo-Code-Org/Zoo-Code) | 1,794 | Apache-2.0 | Active | Ex-Roo maintainers' continuation. |
| [avante-corp/avante.nvim](https://github.com/avante-corp/avante.nvim) (→ from yetone) | 18,148 | Apache-2.0 | Very active | Cursor-like flows in Neovim; often ahead of VS Code extensions in creative UX. |
| [TabbyML/tabby](https://github.com/TabbyML/tabby) | 33,860 | custom (Apache w/ parts, NOASSERTION) | Active | Self-hosted autocomplete serving + models — infrastructure reference. |
| [olimorris/codecompanion.nvim](https://github.com/olimorris/codecompanion.nvim) | 6,834 | Apache-2.0 | Active | Neovim agent with adapters/strategies architecture. |
| [smallcloudai/refact](https://github.com/smallcloudai/refact) | 3,540 | BSD-3-Clause | **Archived 2026-05-30** | End-to-end agent (plan/execute) — archived, still readable. |
| [The-PR-Agent/pr-agent](https://github.com/The-PR-Agent/pr-agent) (→ from Codium-ai) | 12,857 | MIT | Active | Open-source PR review agent. |

### Autonomous agent frameworks — `projects/agent-frameworks/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) (→ from All-Hands-AI) | 86,182 | MIT | Very active | Code-agent platform: sandboxed runtime, event-stream architecture, agent hub. |
| [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) (→ from geekan) | 70,222 | MIT | Slow (2026-01) | Multi-agent "software company" simulation; role orchestration reference. |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 58,091 | MIT | Active | Role-based agent orchestration framework. |
| [AntonOsika/gpt-engineer](https://github.com/AntonOsika/gpt-engineer) | 55,109 | MIT | **Archived 2025-05** | Historical precursor to Lovable. |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 20,222 | MIT | Active | Princeton; the "ACI" (agent-computer interface) concept + config-driven agent design. |
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 29,197 | MIT | Active | OpenAI's lightweight multi-agent SDK. |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | 29,158 | Apache-2.0 | Active | Code-writing ("think in code") agents; tiny, clean loop. |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 41,065 | MIT | Active | StateGraph durable agent orchestration (checkpointing, human-in-the-loop). |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | 13,331 | MIT | Active | MS's new unified framework (AutoGen successor). |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 60,800 | CC-BY-4.0 (!) | Stalled (2026-04) | Superseded by agent-framework. |
| [kirodotdev/KiroCrew](https://github.com/kirodotdev/KiroCrew) | 3,645 | Apache-2.0 | Active | AWS Kiro's open "persistent agent workspace that self-improves across sessions" — memory/persistence patterns. |
| [SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench) | 5,776 | MIT | Active | The coding-agent benchmark. |
| [SweepAI/sweep](https://github.com/SweepAI/sweep) | 7,708 | custom | Dormant (2025-09) | GitHub-issue→PR agent; read for its CI loop design. |
| [ghuntley/amazon-kiro.kiro-agent-source-code-analysis](https://github.com/ghuntley/amazon-kiro.kiro-agent-source-code-analysis) | 368 | none | Static | Reverse-engineered analysis of Kiro's agent extension — spec-driven dev internals. |

### Native editors (context) — `projects/native-editors/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [helix-editor/helix](https://github.com/helix-editor/helix) | 46,083 | MPL-2.0 | Active | Modal editor, minimal AI — context for the from-scratch editor space. |

### Automation platforms (n8n & friends) — `projects/automation-platforms/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [apache/airflow](https://github.com/apache/airflow) | 46,732 | Apache-2.0 | Active | DAG-based scheduler; the classic. |
| [huginn/huginn](https://github.com/huginn/huginn) | 49,898 | MIT | Maintained | Ruby agents that monitor and act — the granddad (2013). |
| [kestra-io/kestra](https://github.com/kestra-io/kestra) | 27,991 | Apache-2.0 | Active | Event-driven declarative (YAML) orchestration; flow engine + triggers. |
| [node-red/node-red](https://github.com/node-red/node-red) | 23,619 | Apache-2.0 | Active | Flow-based programming original; runtime + editor split. |
| [activepieces/activepieces](https://github.com/activepieces/activepieces) | 24,257 | MIT core + piece-specific (NOASSERTION root) | Active | "Zapier alternative"; piece-based architecture, ~400 MCP servers. |
| [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) | 23,781 | Apache-2.0 | Active | Pythonic dynamic workflows. |
| [temporalio/temporal](https://github.com/temporalio/temporal) | 22,828 | MIT | Active | **Durable execution engine** — the semantics agent workflows need (replay, retries, state). |
| [windmill-labs/windmill](https://github.com/windmill-labs/windmill) | 17,780 | AGPL (NOASSERTION) | Active | Rust flow engine over dependency graph; scripts→workflows→UIs; openflows. |
| [dagster-io/dagster](https://github.com/dagster-io/dagster) | 16,107 | Apache-2.0 | Active | Asset-oriented orchestration + strong typing/observability. |
| [automatisch/automatisch](https://github.com/automatisch/automatisch) | 13,963 | AGPL (NOASSERTION) | Slow (2026-02) | Open-source Zapier. |
| [triggerdotdev/trigger.dev](https://github.com/triggerdotdev/trigger.dev) | 16,215 | Apache-2.0 | Active | Durable background functions for JS. |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 203,367 | **Sustainable Use (source-available)** | Very active | The reference workflow automation platform — 2nd-largest repo in this catalog. Node manifests, task runners, queue mode, execution persistence/resume, credentials, AI/LangChain nodes. Code is readable & portable per user policy. |

### Visual AI workflow builders — `projects/ai-workflow-builders/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [langgenius/dify](https://github.com/langgenius/dify) | 154,469 | modified Apache (conditions; NOASSERTION) | Very active | LLM app platform: agent workflows, RAG pipelines, multi-model. |
| [langflow-ai/langflow](https://github.com/langflow-ai/langflow) | 154,259 | MIT | Very active | Visual agent builder (IBM/DataStax); typed component graph. |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 90,055 | Apache-2.0 | Very active | Deep-document RAG engine + agent workflows. |
| [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) | 55,420 | custom (NOASSERTION) | **Archived 2026-08-13** | Visual LLM app builder — archived but fully readable. |
| [simstudioai/sim](https://github.com/simstudioai/sim) | 29,543 | Apache-2.0 | Very active | Collaborative agent/workspace builder — 2025 breakout. |
| [labring/FastGPT](https://github.com/labring/FastGPT) | 29,572 | conditions (NOASSERTION) | Very active | Knowledge-base + visual workflow platform. |
| [stackblitz-labs/bolt.diy](https://github.com/stackblitz-labs/bolt.diy) | 19,847 | Apache-2.0 w/ restrictions | Slow (2026-02) | Open-source AI web-app builder (bolt.new lineage). |
| [onlook-dev/onlook](https://github.com/onlook-dev/onlook) | 26,638 | Apache-2.0 | Active | "Cursor for designers" — visual React editor. |
| [coze-dev/coze-studio](https://github.com/coze-dev/coze-studio) | 21,543 | Apache-2.0 | Active | ByteDance's one-stop visual agent platform. |
| [coze-dev/coze-loop](https://github.com/coze-dev/coze-loop) | 5,712 | Apache-2.0 | Active | **Agent observability/tracing/eval platform** — directly relevant to our agent tracing needs. |

### Emerging / reference — `projects/emerging/`

| Repo | ★ | License | Status | What it is |
|---|---|---|---|---|
| [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) | 25,694 | CC (docs) | Stable | The canonical "how to build production LLM agents" primer — schema, small tools, stateless reducer, contact switches. |
| [JRedeker/opencode-morph-fast-apply](https://github.com/JRedeker/opencode-morph-fast-apply) | 170 | MIT | Active | Morph Fast Apply integration for opencode — fast edit-apply model usage pattern. |

### Notable deaths / unfindables (checked 2026-09-05, do not chase)

- `sourcegraph/cody` — deleted/renamed (Sourcegraph pivoted; nothing to clone).
- `twobees/twinny` — 404, gone.
- `samejs/same` — wrong org; same.new's OSS home not found under that name (Sim covers the space).
- `morph-labs/morphFastApply` — 404; only the plugin + `morphllm/*` demos are public.
- gpt-engineer (archived), Flowise (archived), Roo Code (archived), refact (archived), Void (archived) — archived ≠ useless; code remains fully readable and portable.

---

## 2. What moved in 2026 (redirects you'll hit)

block/goose → **aaif-goose/goose** · yetone/avante.nvim → **avante-corp** · geekan/MetaGPT → **FoundationAgents** · All-Hands-AI/OpenHands → **OpenHands/OpenHands** · princeton-nlp/SWE-bench → **SWE-bench/SWE-bench** · Codium-ai/pr-agent → **The-PR-Agent** · zed-industries/agent-client-protocol → **agentclientprotocol** · trigger-dev → **triggerdotdev** · sst/opencode → **anomalyco/opencode** · kilocodeai → **Kilo-Org/kilocode**

---

## 3. Deep-dive: VS Code forks & the 2026 fork die-off (completed agent report)

The single most important landscape fact for NeuralInverse: **the first generation of open VS Code forks died in 2026, and the survivors moved the agent layer into extensions/CLIs.** Void archived 2026-06-02 (~14 months behind upstream at death); PearAI's fork froze 2025-05; Roo sunset 2026-05-15 (→ community fork Zoo-Code); Continue was acqui-hired by Cursor (code stays open). NeuralInverse is itself listed in `voideditor/void-forks` as the most-starred active Void continuation.

### Void (our ancestor — the portable blueprint)

- All AI code in one contrib folder: `src/vs/workbench/contrib/void/` with `browser/` + `common/` + `electron-main/` split; services via `registerSingleton`; keybindings as VS Code Actions.
- Key browser services: `editCodeService` (apply/diff streaming), `autocompleteService` (FIM), `chatThreadService`, `contextGatheringService`, `toolsService`, `terminalToolService`, `voidSCMService` (git checkpoints), `extensionTransferService` (pulls LSP/diagnostics out of the extension host), `quickEditActions` (Ctrl+K).
- Key common services: `sendLLMMessageService/Types` (streaming LLM abstraction with onPending/onFinal), `voidModelService` (background file edits + buffer/OS sync), native `mcpService`, `modelCapabilities` (per-model capability matrix), `prompt/` templates.
- **LLM calls run in electron-main over IPC** (dodges renderer CSP + allows node_modules). Most-copied trick.
- Chat UI is a full **React+Tailwind app compiled inside the fork** (`browser/react/`, custom build step + `scope-tailwind`) — impossible in plain extensions; the fork's superpower.
- **Edit primitives ("Apply")**: Fast Apply = LLM emits `<<<<<<< ORIGINAL / ======= / >>>>>>> UPDATED` search-replace blocks (works on 1000-line files); Slow Apply = whole-file rewrite. Primitives: **DiffZone** (streamable red/green region + llmCancelToken) and **DiffArea** (line-range tracker). One apply path serves chat-apply, the Edit tool, and Ctrl+K. *The single most valuable thing to port.*
- `void-builder` repo + public GitHub Actions replace VS Code's private build/sign/update pipeline.
- Marketplace: shipped `product.json` points at MS gallery (Cursor-style gray zone); OpenVSX is the legal alternative; PearAI's self-hosted proxy (`market.trypear.ai`) is the middle path.

### Lessons for fork maintenance (from the die-off)

1. Confine the diff to a contrib folder → upstream merges become tractable.
2. The merge treadmill is the #1 fork killer (Void died 14 months behind; Microsoft ships monthly). Automate tracking (VSCodium model: nightly scripts + product.json surgery).
3. Vendored dependencies die too (Continue, Roo both went read-only in 2026) → vendor and own ported code, don't submodule-track dead upstreams.
4. The strategic warning: Roo shut down at 3M installs concluding in-editor agents lose to cloud/CLI agents; survivors (Cline 67k★, Kilo 27k★, opencode 204k★) are extension/CLI-first. An in-fork agent subsystem is now rare/differentiated — Void's archive is basically the only full reference implementation, and we already own a continuation.

---

## 4. Port-value ranking for NeuralInverse (opinionated shortlist)

1. **Void (ancestor)** — Apply/DiffZone streaming-diff engine, electron-main LLM IPC, React-in-workbench build, native MCP service. Apache-2.0. We inherit its lineage; mine first.
2. **Continue `core/`** — the cleanest UI-agnostic agent subsystem (autocomplete, indexing+LanceDB, edit/apply, protocol, config-as-YAML). Apache-2.0.
3. **opencode + ACP** — 204k★ MIT agent; ACP lets an editor drive any external agent over JSON-RPC — a clean seam for "fork shell + agent runtime".
4. **Cline / Roo-archive / Kilo** — checkpoints (git-based snapshots), plan/act modes, Roo Memory Bank, custom modes, MCP marketplace patterns.
5. **crush (FSL) + trae-agent (MIT) + gemini-cli (Apache)** — terminal agent loops: context compaction, approval UX, tool protocols.
6. **aider (Apache)** — repo-map token-budgeting algorithms for our context packer.
7. **n8n + Windmill + Kestra + Temporal** — workflow execution semantics: node manifests, queue-mode workers, execution persistence/resume, durable-execution replay — feeds our composer/orchestrator canvas (alongside the ComfyUI work).
8. **coze-loop + LangGraph** — agent tracing/observability + checkpointed state graphs.
9. **12-factor-agents** — the design checklist to audit our agent loop against.

---

## 5. Pending (blocked on API quota reset — 2026-09-08 22:28)

Deep prose reports for: terminal agents (partial: licenses done), from-scratch editors, IDE extensions (Roo Memory Bank deep-dive), autonomous frameworks (OpenHands/SWE-agent deep-dives), emerging/hidden-gems sweep, automation platforms (n8n node-manifest/task-runner deep-dive), visual AI builders (canvas/execution patterns). Stats in this file are already API-verified; the pending work adds architecture depth per project (repo-layout walkthroughs like the freebuff/ComfyUI handoffs).

Rerun: relaunch the 7 agents with the same prompts (they are in this session's history) or do targeted deep-dives on the §4 shortlist only.

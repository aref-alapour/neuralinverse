/*--------------------------------------------------------------------------------------
 *  Copyright 2026 Neural Inverse Inc. All rights reserved.
 *  Licensed under the Apache License, Version 2.0. See LICENSE.txt for more information.
 *--------------------------------------------------------------------------------------*/

// Capability parity between the sidebar chat path and the native chat bridge
// (task A8, after the E1 and Q12 precedents).
//
// The native chat bridge (voidModelProvider) builds its system message and
// tool list SEPARATELY from the sidebar pipeline (convertToLLMMessageService
// + chatThreadService). Every capability that only the sidebar wires up is
// silently absent in native chat — this happened twice already (E1: workspace
// rules; A8: hybrid memory + ledger recall tools, both caught by the owner's
// live test, not by any automated check).
//
// This test parses the SOURCE of both paths and pins the wiring points as
// anchors, the same approach as sendLLMMessageParity.test.ts (Q12): if a
// future change drops or renames one of these wiring points, the suite goes
// red HERE instead of shipping and waiting for a manual test to notice.
//
// Each anchor names the capability it guards; keep failure messages
// self-explanatory because the fixer may not know this history.

import assert from 'assert';
import * as fs from 'fs';
import { dirname, join } from '../../../../../base/common/path.js';
import { fileURLToPath } from 'url';
import { ensureNoDisposablesAreLeakedInTestSuite } from '../../../../../base/test/common/utils.js';

const BRIDGE = 'src/vs/workbench/contrib/void/browser/voidModelProvider.ts';
const CONVERT = 'src/vs/workbench/contrib/void/browser/convertToLLMMessageService.ts';

/** Repo root walked up from this file; sentinel is .git (decoy package.json files in the standalone runner's temp tree would resolve one level too low). */
function findRepoRoot(): string {
	let dir = dirname(fileURLToPath(import.meta.url));
	while (true) {
		if (fs.existsSync(join(dir, '.git'))) { return dir; }
		const parent = dirname(dir);
		if (parent === dir) { break; }
		dir = parent;
	}
	throw new Error('Could not locate repo root (.git) above ' + dir);
}

function readSource(relPath: string): string {
	return fs.readFileSync(join(findRepoRoot(), relPath), 'utf-8');
}

suite('native chat parity — sidebar ↔ bridge capabilities (A8)', () => {
	ensureNoDisposablesAreLeakedInTestSuite();

	const bridge = readSource(BRIDGE);
	const convert = readSource(CONVERT);

	test('hybrid memory instructions reach the native chat bridge', () => {
		// The sidebar injects aiInstructions (incl. the Agent Memory block) via
		// prepareLLMChatMessages; the bridge must fetch the same content and
		// append it to its own system message.
		assert.ok(
			bridge.includes('getAIInstructionsForChat('),
			`${BRIDGE} must call _convertService.getAIInstructionsForChat(...) and append the result to its system message — otherwise the Agent Memory block exists only in the sidebar (task A8 gap 1)`
		);
		assert.ok(
			bridge.includes('systemMessage = `${systemMessage}\\n\\n${aiInstructions}`'),
			`${BRIDGE} must append the fetched AI instructions to systemMessage, not compute and drop them`
		);
	});

	test('the sidebar memory path is seeded with the user message (fresh chats)', () => {
		// recallForPrompt keys off workflow-agent state; without the user's
		// message as seed, a fresh chat (no agent running) never recalls.
		assert.ok(
			convert.includes('_getCombinedAIInstructionsForChat(lastUserContent)'),
			`${CONVERT} prepareLLMChatMessages must pass the last user message into _getCombinedAIInstructionsForChat — otherwise hybrid memory only surfaces while a workflow agent is running`
		);
		assert.ok(
			convert.includes('getChatMemoryContext(querySeed)'),
			`${CONVERT} must fall back to getChatMemoryContext(querySeed) when the agent context is empty — the fresh-chat recall path (task A8)`
		);
	});

	test('the bridge offers the internal tools it advertises', () => {
		// generateSystemMessage (chatMode 'agent') includes internal tool
		// schemas in the system message; extractXMLToolsWrapper only extracts
		// XML for tools present in ITS list. If the bridge does not merge
		// internalToolService.getToolInfos() into the tools it passes down,
		// the model is advertised recall_history but its calls never parse.
		assert.ok(
			bridge.includes('this._internalToolService.getToolInfos()'),
			`${BRIDGE} must merge internalToolService.getToolInfos() into its tool list (like chatThreadService does for the sidebar)`
		);
		assert.ok(
			/allBridgeTools,\s*systemMessage,\s*token/.test(bridge),
			`${BRIDGE} must pass the merged tool list (internal + copilot) to _callLLM — a list the XML extractor and native tool schemas both see`
		);
	});

	test('the bridge executes internal tool calls instead of rejecting them', () => {
		// Before A8 the routing fell through to `Tool "..." is not available.`
		// for every internal tool name — the exact failure the owner saw.
		assert.ok(
			bridge.includes('this._internalToolService.execute('),
			`${BRIDGE} must route internal tool names to internalToolService.execute — otherwise recall_history answers "not available" (task A8 gap 2)`
		);
		assert.ok(
			bridge.includes('this._internalToolService.has(toolName)'),
			`${BRIDGE} must branch on internalToolService.has(toolName) before the not-available fallback`
		);
	});

	test('the shared system-message builder keeps internal tools for agent chat modes', () => {
		// The bridge relies on generateSystemMessage('agent', ...) advertising
		// the internal tool schemas; dropping 'agent' from this condition
		// would silently hide them from native chat again.
		const idx = convert.indexOf('internalToolService.getToolInfos()');
		assert.ok(idx !== -1, `${CONVERT} generateSystemMessage must keep merging internalToolService.getToolInfos() into the advertised tool schemas`);
		const conditionWindow = convert.slice(Math.max(0, idx - 400), idx);
		assert.ok(
			conditionWindow.includes(`'agent'`),
			`${CONVERT} generateSystemMessage must include internal tool infos for chatMode 'agent' — the native chat bridge calls it with exactly that mode`
		);
	});
});

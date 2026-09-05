#!/usr/bin/env node
/**
 * # The one verify command (task Q5 §ج)
 *
 *   node tools/verify.mjs
 *
 * Runs, in order, and prints one honest summary:
 *   1. tools/typecheck-slice.mjs --self-test  (strict repo options, self-tested)
 *   2. tools/run-tests-standalone.mjs         (pure tests, mocha shim)
 *   3. tools/live-patch-selftest.py           (Q4 sandbox scenarios; SKIPPED
 *      when the installed app (and its pristine .orig baselines) is absent)
 *
 * The last lines of the output are the whole point:
 *   coverage   : NN% of the ledger feature files type-checked
 *   NOT CHECKED: <every feature file the harness did NOT see>
 * A green run that silently skipped files would be worse than no harness.
 */
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { ensureTypeScript } from './.verify/bootstrap.mjs';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function run(cmd, args, label) {
	const r = spawnSync(cmd, args, { encoding: 'utf8', cwd: REPO });
	return { label, code: r.status, out: (r.stdout ?? '') + (r.stderr ?? '') };
}

// ─── 0. private TypeScript (bootstrap; no-op when already present) ────────────
const ts = ensureTypeScript();

// ─── 1. type-check (self-tested) ──────────────────────────────────────────────
const tc = run(process.execPath, ['tools/typecheck-slice.mjs', '--self-test'], 'type-check');

// ─── 2. standalone tests ──────────────────────────────────────────────────────
const tt = run(process.execPath, ['tools/run-tests-standalone.mjs'], 'tests');

// ─── 3. live-patch sandbox self-test (Q4) ─────────────────────────────────────
const PY = process.platform === 'win32' ? 'python' : 'python3';
const lpScript = path.join(REPO, 'tools/live-patch-selftest.py');
const lpInstalled = existsSync('C:/Program Files/NeuralInverse/resources/app/out/vs/workbench/workbench.desktop.main.js.orig');
const lp = existsSync(lpScript)
	? (lpInstalled
		? run(PY, [lpScript], 'live-patch')
		: { label: 'live-patch', code: null, out: 'SKIPPED — installed app / pristine .orig baselines not found on this machine' })
	: { label: 'live-patch', code: null, out: 'SKIPPED — tools/live-patch-selftest.py not present' };

// ─── coverage: what the harness saw vs what it did NOT ───────────────────────
const SLICE = JSON.parse(readFileSync(path.join(REPO, 'tools/typecheck-slice.json'), 'utf8'));
const checked = new Set(SLICE.files);
const notChecked = SLICE.featureFiles.filter(f => !checked.has(f));
const linesOf = f => existsSync(path.join(REPO, f)) ? readFileSync(path.join(REPO, f), 'utf8').split('\n').length : 0;
const checkedLines = SLICE.files.reduce((a, f) => a + linesOf(f), 0);
const notCheckedLines = notChecked.reduce((a, f) => a + linesOf(f), 0);
const coverage = Math.round(100 * checkedLines / Math.max(1, checkedLines + notCheckedLines));

// ─── summary ──────────────────────────────────────────────────────────────────
console.log('──────────────────────────────────────────────────────────');
// the summary lines each step already printed (kept, not duplicated)
for (const r of [tc, tt, lp]) {
	const status = r.code === null ? 'SKIP' : (r.code === 0 ? 'PASS' : `FAIL(${r.code})`);
	const lines = r.out.trimEnd().split('\n').filter(l => l.trim() !== '');
	const tail = lines.slice(-3).join('\n  ');
	console.log(`${status.padEnd(8)} ${r.label}\n  ${tail}`);
}
console.log(`coverage   : ${coverage}% of the ledger feature files type-checked (${checkedLines.toLocaleString()} of ${(checkedLines + notCheckedLines).toLocaleString()} lines)`);
if (notChecked.length > 0) {
	console.log(`NOT CHECKED (${notChecked.length} files, ${notCheckedLines.toLocaleString()} lines):`);
	for (const f of notChecked) console.log(`  - ${f} (${linesOf(f)} lines)`);
}
if (ts.installed) console.log(`typescript  : bootstrapped via ${ts.how} (private install in tools/.verify)`);
console.log('──────────────────────────────────────────────────────────');

const failed = [tc, tt, lp].filter(r => r.code !== null && r.code !== 0);
process.exit(failed.length > 0 ? 1 : 0);

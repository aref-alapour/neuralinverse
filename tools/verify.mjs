#!/usr/bin/env node
/*--------------------------------------------------------------------------------------
 *  Copyright 2026 Neural Inverse Inc. All rights reserved.
 *  Licensed under the Apache License, Version 2.0. See LICENSE.txt for more information.
 *--------------------------------------------------------------------------------------*/

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
 *   4. contribution registration gate         (Q13: every *.contribution.ts
 *      under src/vs must be reachable — directly OR through any chain of
 *      imports — from a real bundle entrypoint, or be on the documented
 *      allowlist; details at ORPHAN_CONTRIBUTION_ALLOWLIST below)
 *
 * The last lines of the output are the whole point:
 *   coverage   : NN% of the ledger feature files type-checked
 *   NOT CHECKED: <every feature file the harness did NOT see>
 * A green run that silently skipped files would be worse than no harness.
 *
 * Debug helper (gate only, no type-check, prints import chains):
 *   node tools/verify.mjs --trace <path-fragment>
 */
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { ensureTypeScript } from './.verify/bootstrap.mjs';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function run(cmd, args, label) {
	const r = spawnSync(cmd, args, { encoding: 'utf8', cwd: REPO });
	return { label, code: r.status, out: (r.stdout ?? '') + (r.stderr ?? '') };
}

// ─── contribution registration gate (task Q13) ────────────────────────────────
//
// A *.contribution.ts that no bundle entrypoint reaches (directly or through
// any chain of imports) compiles and type-checks green but never registers at
// runtime — dead code that audits kept mistaking for ready infrastructure
// (neuralInverse.contribution.ts sat in that state through three independent
// audits on 2026-09-08). "Someone imports it" is NOT enough:
//   - powerMode.contribution.ts is imported only by the (unregistered)
//     neuralInverse.contribution.ts, so it is dead too — only reachability
//     from a real entrypoint counts;
//   - conversely workflowAgentService.ts is alive ONLY transitively
//     (void.contribution.ts -> toolsService.ts:34), so the walk must follow
//     import chains across contrib folders, static AND dynamic import().
//
// Roots = what the build actually bundles: the bootstrap entries (src/main.ts,
// src/cli.ts, src/server-main.ts, src/server-cli.ts), every *.main.ts /
// *.main.internal.ts under src/vs, and every 'vs/…' module name enumerated in
// build/buildfile.ts. The scanner is a small string/comment-aware lexer; regex
// literals are approximated (a stray false positive fails loudly here, never
// silently passes).

const ORPHAN_CONTRIBUTION_ALLOWLIST = new Map([
	['src/vs/workbench/contrib/neuralInverse/browser/neuralInverse.contribution.ts',
		'Q13 (owner decision 2026-09-08): not registered until task A1 wires the LLM into the background-agent loop; registering now would show a broken Agent Manager panel. See تسک/05-quality/13-contribution-registration-gate.md and the comment in src/vs/workbench/workbench.common.main.ts.'],
	['src/vs/workbench/contrib/powerMode/browser/powerMode.contribution.ts',
		'Q13: imported only by the unregistered neuralInverse.contribution.ts, so it is transitively dead; revive it together with that file (powerBusService itself stays alive via workflowAgentService).'],
	['src/vs/workbench/contrib/neuralInverseChecks/browser/neuralInverseChecks.contribution.ts',
		'Q10: not built yet — UI written against 9 services that do not exist; excluded from the compile in src/tsconfig.json and unregistered in workbench.common.main.ts.'],
	['src/vs/workbench/contrib/neuralInverseEnclave/browser/neuralInverseEnclave.contribution.ts',
		'Q10: not built yet — UI written against 15 services that do not exist; excluded from the compile in src/tsconfig.json and unregistered in workbench.common.main.ts.'],
	['src/vs/workbench/contrib/neuralInverseEnclave/browser/statusbar/enclaveStatus.contribution.ts',
		'Q10: statusbar part of the unbuilt Enclave contrib; reachable only through the (commented-out) enclave registration above.'],
	['src/vs/workbench/contrib/agentsVoice/browser/transcriptsView/voiceEventStream.contribution.ts',
		'DISCREPANCY found by this gate on 2026-09-08 (not in the Q13 table): no importer anywhere in this tree, and upstream VS Code agentsVoice.contribution.ts does not import it either — inherited upstream WIP/dead code. Owner decision needed: keep as upstream WIP or delete; do not import it blindly.'],
]);

function blankJsComments(src) {
	let out = '';
	let mode = 'code'; // code | line | block | a quote char while inside a string
	for (let i = 0; i < src.length;) {
		const c = src[i], d = src[i + 1];
		if (mode === 'code') {
			if (c === '/' && d === '/') { out += '  '; i += 2; mode = 'line'; continue; }
			if (c === '/' && d === '*') { out += '  '; i += 2; mode = 'block'; continue; }
			const code = c.charCodeAt(0);
			if (code === 39 /* ' */ || code === 34 /* " */ || code === 96 /* ` */) { mode = c; }
			out += c; i += 1; continue;
		}
		if (mode === 'line') {
			if (c === '\n' || c === '\r') { mode = 'code'; out += c; } else { out += ' '; }
			i += 1; continue;
		}
		if (mode === 'block') {
			if (c === '*' && d === '/') { out += '  '; i += 2; mode = 'code'; continue; }
			out += (c === '\n' || c === '\r') ? c : ' ';
			i += 1; continue;
		}
		// inside a string literal: copy verbatim (keeps escapes), exit on the
		// matching unescaped quote; ${…} nesting inside templates is treated
		// as string content (no import lives there in this tree)
		if (c === '\\') { out += src.slice(i, i + 2); i += 2; continue; }
		if (c === mode) { mode = 'code'; }
		out += c; i += 1;
	}
	return out;
}

function moduleSpecifiers(src) {
	const specs = new Set();
	const patterns = [
		/\bimport\s+[^;'"()]*?from\s*(['"])([^'"]+)\1/g, // import … from 'x' (incl. import type)
		/\bexport\s+[^;'"()]*?from\s*(['"])([^'"]+)\1/g, // export … from 'x'
		/\bimport\s*\(\s*(['"])([^'"]+)\1\s*\)/g,        // dynamic import('x')
		/\bimport\s*(['"])([^'"]+)\1/g,                  // side-effect import 'x'
		/\brequire\s*\(\s*(['"])([^'"]+)\1\s*\)/g,       // require('x')
	];
	for (const re of patterns) {
		for (const m of src.matchAll(re)) {specs.add(m[2]);}
	}
	return specs;
}

function resolveModule(spec, fromFile) {
	if (!spec.startsWith('.') && !spec.startsWith('vs/')) {return null;} // npm / node builtin / electron
	if (/\.(css|json|svg|media)$/.test(spec)) {return null;}             // assets, not modules
	const base = spec.startsWith('vs/')
		? path.join(REPO, 'src', spec)
		: path.resolve(path.dirname(fromFile), spec);
	const noJs = base.endsWith('.js') ? base.slice(0, -3) : null;
	const candidates = noJs
		? [noJs + '.ts', noJs + '.tsx', noJs + '.d.ts', base]
		: [base + '.ts', base + '.tsx', base + '.d.ts', base + '.js', path.join(base, 'index.ts')];
	for (const c of candidates) {
		try { if (statSync(c).isFile()) {return c;} } catch { /* not found — next */ }
	}
	return null;
}

function listFilesDeep(dir, out = []) {
	for (const e of readdirSync(dir, { withFileTypes: true })) {
		const p = path.join(dir, e.name);
		if (e.isDirectory()) { listFilesDeep(p, out); }
		else if (e.isFile()) { out.push(p); }
	}
	return out;
}

function checkContributionRegistration(traceFragment) {
	const SRC = path.join(REPO, 'src');
	const rel = f => path.relative(REPO, f).split(path.sep).join('/');

	// entry roots (what the bundles actually contain)
	const roots = new Set();
	for (const b of ['main.ts', 'cli.ts', 'server-main.ts', 'server-cli.ts']) {
		const f = path.join(SRC, b);
		if (existsSync(f)) {roots.add(f);}
	}
	const buildfile = path.join(REPO, 'build', 'buildfile.ts');
	if (existsSync(buildfile)) {
		for (const m of readFileSync(buildfile, 'utf8').matchAll(/'(vs\/[^']+)'/g)) {
			const f = resolveModule(m[1], buildfile);
			if (f) {roots.add(f);}
		}
	}
	const srcFiles = listFilesDeep(SRC);
	for (const f of srcFiles) {
		const b = path.basename(f);
		if ((b.endsWith('.main.ts') || b.endsWith('.main.internal.ts')) && !b.includes('.test.')) {roots.add(f);}
	}

	// transitive walk: importer -> imported, BFS from the roots
	const importer = new Map(); // file -> the entry/importer that reached it
	const queue = [...roots];
	for (const r of queue) {importer.set(r, undefined);}
	for (let i = 0; i < queue.length; i++) {
		const f = queue[i];
		let src;
		try { src = readFileSync(f, 'utf8'); } catch { continue; }
		for (const spec of moduleSpecifiers(blankJsComments(src))) {
			const t = resolveModule(spec, f);
			if (t && !importer.has(t)) { importer.set(t, f); queue.push(t); }
		}
	}

	// the check: every *.contribution.ts must be reachable
	const contributions = srcFiles.filter(f => f.endsWith('.contribution.ts')).sort();
	const orphans = contributions.filter(f => !importer.has(f));
	const unexpected = orphans.filter(f => !ORPHAN_CONTRIBUTION_ALLOWLIST.has(rel(f)));
	const stale = [...ORPHAN_CONTRIBUTION_ALLOWLIST.keys()].filter(k => !orphans.some(f => rel(f) === k));

	const lines = [];
	lines.push(`contribution-gate: ${contributions.length} *.contribution.ts files under src/vs`);
	lines.push(`  reachable from bundle entrypoints : ${contributions.length - orphans.length}`);
	lines.push(`  orphaned (on documented allowlist): ${orphans.length - unexpected.length}`);
	for (const f of orphans) {
		const reason = ORPHAN_CONTRIBUTION_ALLOWLIST.get(rel(f));
		if (reason) { lines.push(`    - ${rel(f)}\n        ${reason}`); }
		else { lines.push(`    - ${rel(f)}  <-- ORPHAN: no entrypoint reaches this registration`); }
	}
	if (unexpected.length > 0) {
		lines.push(`  UNEXPECTED ORPHANS (fix or allowlist): ${unexpected.length}`);
	} else if (orphans.length > 0) {
		lines.push('  unexpected orphans                 : 0 (all orphans documented)');
	}
	for (const k of stale) {
		lines.push(`  STALE allowlist entry (now reachable or gone — remove it): ${k}`);
	}
	lines.push(`  summary: ${contributions.length} *.contribution.ts, ${contributions.length - orphans.length} reachable, ${orphans.length} orphaned (${orphans.length - unexpected.length} documented, ${unexpected.length} unexpected, ${stale.length} stale allowlist)`);

	if (traceFragment) {
		lines.push(`trace '${traceFragment}':`);
		const hits = [...importer.keys(), ...contributions].filter(f => rel(f).includes(traceFragment));
		if (hits.length === 0) {lines.push('  no file in the import graph matches');}
		for (const h of hits) {
			if (!importer.has(h)) { lines.push(`  NOT REACHABLE: ${rel(h)}`); continue; }
			const chain = [];
			for (let c = h; c !== undefined; c = importer.get(c)) {chain.push(rel(c));}
			lines.push(`  reachable: ${chain.join('\n        imported by ')}`);
		}
	}

	return { label: 'contribution-gate', code: (unexpected.length + stale.length) > 0 ? 1 : 0, out: lines.join('\n') };
}

// `node tools/verify.mjs --trace <fragment>`: run only the contribution gate,
// with import chains for every file whose path contains <fragment>.
const traceIdx = process.argv.indexOf('--trace');
if (traceIdx !== -1) {
	const cgTrace = checkContributionRegistration(process.argv[traceIdx + 1] ?? '');
	console.log(cgTrace.out);
	process.exit(cgTrace.code);
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

// ─── 4. contribution registration gate (Q13; see block above for details) ────
const cg = checkContributionRegistration();
console.log(cg.out);

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
for (const r of [tc, tt, lp, cg]) {
	const status = r.code === null ? 'SKIP' : (r.code === 0 ? 'PASS' : `FAIL(${r.code})`);
	const lines = r.out.trimEnd().split('\n').filter(l => l.trim() !== '');
	const tail = lines.slice(-3).join('\n  ');
	console.log(`${status.padEnd(8)} ${r.label}\n  ${tail}`);
}
console.log(`coverage   : ${coverage}% of the ledger feature files type-checked (${checkedLines.toLocaleString()} of ${(checkedLines + notCheckedLines).toLocaleString()} lines)`);
if (notChecked.length > 0) {
	console.log(`NOT CHECKED (${notChecked.length} files, ${notCheckedLines.toLocaleString()} lines):`);
	for (const f of notChecked) {console.log(`  - ${f} (${linesOf(f)} lines)`);}
}
if (ts.installed) {console.log(`typescript  : bootstrapped via ${ts.how} (private install in tools/.verify)`);}
console.log('──────────────────────────────────────────────────────────');

const failed = [tc, tt, lp, cg].filter(r => r.code !== null && r.code !== 0);
process.exit(failed.length > 0 ? 1 : 0);

#!/usr/bin/env node
/**
 * # Standalone test runner (task Q5 §ب)
 *
 * Runs the ledger's pure test files WITHOUT the repo's mocha infrastructure
 * (which needs a full build). How:
 *
 * 1. the test files and their closure are EMITTED to JS by the private tsc
 *    in tools/.verify — tsc's emit is also the "type-only import → import
 *    type" transform the task demands: interfaces vanish and their imports
 *    are elided in the emitted copy, so the SOURCE is never touched;
 * 2. a mocha-compatible shim (suite/test/setup/teardown/suiteSetup/
 *    suiteTeardown + ensureNoDisposablesAreLeakedInTestSuite no-op) is
 *    installed on globalThis;
 * 3. each emitted test file is imported and its tests run sequentially.
 *
 * Exit 1 on any failure, with the failing test names listed.
 */
import { readFileSync, mkdirSync, rmSync, existsSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SLICE_JSON = JSON.parse(readFileSync(path.join(REPO, 'tools/typecheck-slice.json'), 'utf8'));
const TSC_BIN = path.join(REPO, 'tools/.verify/node_modules/typescript/bin/tsc');
const OUT_DIR = path.join(REPO, 'tools/.verify/tmp-tests');

// ─── mocha-compatible shim ────────────────────────────────────────────────────

const allTests = [];      // flat registry: every `test()` from any suite depth
let currentSuiteName = '';

globalThis.suite = (name, fn) => {
	const prev = currentSuiteName;
	currentSuiteName = prev ? `${prev} — ${name}` : name;
	try { fn(); } finally { currentSuiteName = prev; }
};
globalThis.test = (name, fn) => {
	allTests.push({ name: currentSuiteName ? `${currentSuiteName} — ${name}` : name, fn });
};
globalThis.setup = () => { /* per-file hooks are unnecessary for the pure slice */ };
globalThis.teardown = () => { /* nothing to do */ };
globalThis.suiteSetup = () => { /* nothing to do */ };
globalThis.suiteTeardown = () => { /* nothing to do */ };
globalThis.ensureNoDisposablesAreLeakedInTestSuite = () => { /* VS Code test infra only */ };

// ─── emit the tests + closure to JS ───────────────────────────────────────────

function emitTests(testFiles) {
	const baseOptions = JSON.parse(readFileSync(path.join(REPO, 'src/tsconfig.base.json'), 'utf8')).compilerOptions;
	rmSync(OUT_DIR, { recursive: true, force: true });
	mkdirSync(OUT_DIR, { recursive: true });
	const tsconfig = {
		compilerOptions: {
			...baseOptions,
			noEmit: false,
			declaration: false,
			sourceMap: false,
			inlineSourceMap: false,
			types: [],
			// relative layout under OUT_DIR mirrors the src/ tree so the emitted
			// './x.js' specifiers resolve to the emitted files
			rootDir: REPO,
			outDir: path.join(OUT_DIR, 'src'),
		},
		files: [
			path.join(REPO, 'tools/.verify/stubs/node-ambient.d.ts'),
			...testFiles.map(f => path.join(REPO, f)),
		],
	};
	const cfgPath = path.join(OUT_DIR, 'tsconfig.tests.json');
	writeFileSync(cfgPath, JSON.stringify(tsconfig, null, '\t'));
	// tsc exits 2 whenever the closure has out-of-slice sparse-checkout
	// diagnostics, but the EMIT still happens (noEmitOnError is false) — what
	// matters here is that the emitted files exist, not a clean exit code
	const res = spawnSync(process.execPath, [TSC_BIN, '-p', cfgPath, '--pretty', 'false'], { encoding: 'utf8', cwd: OUT_DIR });
	const emittedAny = testFiles.every(f => existsSync(path.join(OUT_DIR, 'src', f.replace(/\.ts$/, '.js'))));
	if (!emittedAny) {
		throw new Error(`tsc emit produced no output: ${res.stderr || res.stdout || 'unknown error'}`);
	}
	// ESM: emitted files keep import statements; the temp tree needs type=module
	writeFileSync(path.join(OUT_DIR, 'src', 'package.json'), JSON.stringify({ type: 'module' }) + '\n');
	writeFileSync(path.join(OUT_DIR, 'package.json'), JSON.stringify({ type: 'module' }) + '\n');
}

// ─── run ──────────────────────────────────────────────────────────────────────

export async function runTests() {
	const testFiles = SLICE_JSON.tests;
	const missing = testFiles.filter(f => !existsSync(path.join(REPO, f)));
	if (missing.length > 0) throw new Error('missing test files: ' + missing.join(', '));
	emitTests(testFiles);

	const results = [];
	for (const rel of testFiles) {
		const emitted = path.join(OUT_DIR, 'src', rel).replace(/\.ts$/, '.js');
		const before = allTests.length;
		try {
			await import(`file://${emitted.replace(/\\/g, '/')}`);
		} catch (e) {
			results.push({ name: `${rel} (file load)`, error: e });
			continue;
		}
		const fresh = allTests.splice(before); // tests registered by this file
		for (const t of fresh) {
			try {
				await t.fn();
				results.push({ name: t.name, error: null });
			} catch (e) {
				results.push({ name: t.name, error: e });
			}
		}
	}
	return results;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
	let results;
	try {
		results = await runTests();
	} catch (e) {
		console.error(`tests      : FAILED to run — ${e.message}`);
		rmSync(OUT_DIR, { recursive: true, force: true });
		process.exit(1);
	}
	const failed = results.filter(r => r.error);
	for (const f of failed) {
		console.error(`  FAIL ${f.name}`);
		console.error(`       ${String(f.error?.message ?? f.error).split('\n').join('\n       ')}`);
	}
	console.log(`tests      : ${results.length - failed.length} passed, ${failed.length} failed`);
	rmSync(OUT_DIR, { recursive: true, force: true });
	process.exit(failed.length > 0 ? 1 : 0);
}

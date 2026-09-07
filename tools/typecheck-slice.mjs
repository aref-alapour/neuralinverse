#!/usr/bin/env node
/**
 * # Type-check the reviewable slice (task Q5)
 *
 * `tsc -p src/tsconfig.json` needs a full checkout + node_modules; this repo
 * is a partial clone with ~10% of files on disk and zero packages, so a raw
 * run drowns in thousands of environment artifacts. This script instead
 * type-checks an EXPLICIT file list (tools/typecheck-slice.json) using the
 * repo's EXACT strict compilerOptions — copied verbatim (JSON-to-JSON) from
 * src/tsconfig.base.json into a temp tsconfig, never transcribed by hand —
 * and reports honestly:
 *
 *   - errors in slice files        → counted, printed, exit 1
 *   - errors in out-of-slice files → counted separately (sparse-checkout
 *                                     artifacts, not code bugs)
 *   - self-test (--self-test)      → injects a deliberate type error in a
 *                                     temp file and REQUIRES tsc to catch it;
 *                                     a harness that cannot go red is
 *                                     worthless (task Q5: «self-test اجباری»)
 */
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { ensurePlatformStubs } from './.verify/ensure-platform-stubs.mjs';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SLICE_JSON = JSON.parse(readFileSync(path.join(REPO, 'tools/typecheck-slice.json'), 'utf8'));
const TSC_BIN = path.join(REPO, 'tools/.verify/node_modules/typescript/bin/tsc');
const TMP_DIR = path.join(REPO, 'tools/.verify/tmp-typecheck');

// compilerOptions copied verbatim (same JSON strings) from src/tsconfig.base.json
const baseOptions = JSON.parse(readFileSync(path.join(REPO, 'src/tsconfig.base.json'), 'utf8')).compilerOptions;

/** Write the temp tsconfig and run tsc; returns parsed diagnostic lines. */
function runTsc(includeFiles) {
	ensurePlatformStubs(); // local .d.ts for off-disk vs/platform modules (Q5 §ه)
	mkdirSync(TMP_DIR, { recursive: true });
	const tsconfig = {
		compilerOptions: {
			...baseOptions,
			noEmit: true,
			// the slice must not depend on ambient @types that only exist after
			// a full npm install; the repo's own "types" list lives in src/tsconfig.json
			types: [],
		},
		files: [
			// minimal ambient declarations for node:assert + mocha globals —
			// the real @types packages need a full npm install (task Q5 §ه)
			path.join(REPO, 'tools/.verify/stubs/node-ambient.d.ts'),
			...includeFiles,
		],
	};
	const cfgPath = path.join(TMP_DIR, 'tsconfig.slice.json');
	writeFileSync(cfgPath, JSON.stringify(tsconfig, null, '\t'));
	try {
		execFileSync(process.execPath, [TSC_BIN, '-p', cfgPath, '--pretty', 'false'], { encoding: 'utf8', cwd: TMP_DIR });
		return { lines: [], raw: '' };
	} catch (e) {
		const raw = String(e.stdout ?? '') + String(e.stderr ?? '');
		// tsc emits `path(line,col): error TSxxxx: message` with paths relative
		// to the tsconfig's directory (our TMP_DIR cwd) — resolve against it,
		// never against this script's cwd
		const lines = [...raw.matchAll(/^([^\s(][^(]*)\((\d+),(\d+)\): (error|warning) (TS\d+): (.*)$/gm)]
			.map(m => ({ file: path.resolve(TMP_DIR, m[1]), line: Number(m[2]), col: Number(m[3]), severity: m[4], code: m[5], message: m[6] }));
		return { lines, raw };
	}
}

function countLines(files) {
	let lines = 0;
	for (const f of files) {
		if (!existsSync(f)) continue;
		lines += readFileSync(f, 'utf8').split('\n').length;
	}
	return lines;
}

export function typecheckSlice() {
	const files = SLICE_JSON.files.map(f => path.join(REPO, f));
	const missing = files.filter(f => !existsSync(f)).map(f => path.relative(REPO, f));
	if (missing.length > 0) {
		return { ok: false, sliceErrors: [{ text: 'missing slice files: ' + missing.join(', ') }], outOfSlice: 0, files: SLICE_JSON.files, lines: 0 };
	}
	const { lines } = runTsc(files);
	const sliceSet = new Set(files.map(f => path.resolve(f).toLowerCase()));
	const sliceErrors = [];
	let outOfSlice = 0;
	for (const l of lines) {
		if (sliceSet.has(l.file.toLowerCase())) sliceErrors.push({ text: `${path.relative(REPO, l.file).replace(/\\/g, '/')}:${l.line}:${l.col} ${l.code}: ${l.message}` });
		else outOfSlice++;
	}
	return { ok: sliceErrors.length === 0, sliceErrors, outOfSlice, files: SLICE_JSON.files, lines: countLines(files) };
}

// ─── self-test: the harness must be able to go red ───────────────────────────

export function selfTest() {
	const badDir = path.join(TMP_DIR, 'selftest');
	mkdirSync(badDir, { recursive: true });
	const bad = path.join(badDir, 'harness-selftest.ts');
	// an unambiguous type error that can ONLY be caught if tsc actually
	// analyzed the file — guarding against "0 errors because nothing ran"
	writeFileSync(bad, 'const n: number = "definitely not a number";\nexport const x = n;\n');
	try {
		const { lines } = runTsc([bad]);
		const caught = lines.some(l => l.file.toLowerCase() === bad.toLowerCase());
		return { ok: caught, caught };
	} finally {
		rmSync(badDir, { recursive: true, force: true });
	}
}

// ─── CLI ──────────────────────────────────────────────────────────────────────

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
	const st = process.argv.includes('--self-test') ? selfTest() : null;
	const r = typecheckSlice();
	for (const e of r.sliceErrors.slice(0, 50)) console.error('  ' + e.text);
	if (r.sliceErrors.length > 50) console.error(`  … ${r.sliceErrors.length - 50} more`);
	console.log(`type-check : ${r.files.length} files, ${r.lines.toLocaleString()} lines — ${r.sliceErrors.length} error(s)` + (r.outOfSlice ? `, ${r.outOfSlice} out-of-slice dependency diagnostics (outside the slice, ignored)` : ''));
	if (st) console.log(`self-test  : ${st.ok ? 'OK (deliberate error was caught)' : 'FAILED — harness cannot detect errors; results are meaningless'}`);
	rmSync(TMP_DIR, { recursive: true, force: true });
	process.exit((r.ok && (!st || st.ok)) ? 0 : 1);
}

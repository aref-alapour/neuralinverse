#!/usr/bin/env node
/**
 * Ensures a private TypeScript install exists under tools/.verify/node_modules.
 *
 * The repo root has NO node_modules (partial clone, postinstall broken — see
 * task Q5), so the verify harness ships its own tiny, independent TypeScript.
 * Preferred path: `npm install --no-audit --no-fund` (works offline whenever
 * the tarball is already in the npm cache). Fallback for restricted networks:
 * extract the tarball straight from the local npm cache (cacache), which is
 * exactly how the harness was first bootstrapped on this machine.
 */
import { createRequire } from 'node:module';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const TSC_DIR = HERE; // tools/.verify
export const TSC_BIN = path.join(HERE, 'node_modules', 'typescript', 'bin', 'tsc');
export const TS_VERSION = '5.9.3';

const tscOk = () => {
	if (!existsSync(TSC_BIN)) return false;
	try {
		const out = execFileSync(process.execPath, [TSC_BIN, '--version'], { encoding: 'utf8' });
		return out.includes(`Version ${TS_VERSION}`);
	} catch { return false; }
};

function viaNpm() {
	if (!existsSync(path.join(HERE, 'package.json'))) {
		writeFileSync(path.join(HERE, 'package.json'), JSON.stringify({
			name: 'neuralinverse-verify-typescript',
			private: true,
			description: 'Private TypeScript install for tools/verify.mjs — independent of the repo node_modules (task Q5)',
			devDependencies: { typescript: TS_VERSION },
		}, null, '\t') + '\n');
	}
	execFileSync('npm', ['install', '--prefer-offline', '--no-audit', '--no-fund', '--ignore-scripts', `typescript@${TS_VERSION}`],
		{ cwd: HERE, stdio: 'pipe', shell: process.platform === 'win32' });
}

/** npm's bundled cacache — available wherever npm itself is installed. */
function npmCacache() {
	const roots = [process.env.npm_root, path.dirname(path.dirname(process.execPath)), 'C:/Program Files/nodejs']
		.filter(Boolean);
	for (const root of roots) {
		const p = path.join(root, 'npm', 'node_modules', 'cacache');
		if (existsSync(p)) { try { return createRequire(import.meta.url)(p); } catch { /* try next */ } }
	}
	throw new Error('cacache not found next to npm');
}

function viaCacheExtract() {
	const cacache = npmCacache();
	const cacheDir = path.join(process.env.LOCALAPPDATA ?? '', 'npm-cache', '_cacache');
	const key = `make-fetch-happen:request-cache:https://registry.npmjs.org/typescript/-/typescript-${TS_VERSION}.tgz`;
	const tarball = path.join(HERE, `typescript-${TS_VERSION}.tgz`);
	const info = (() => {
		try { return cacache.get.info.sync(cacheDir, key); } catch { return null; }
	})();
	if (!info) throw new Error(`typescript@${TS_VERSION} tarball not in npm cache (${cacheDir}) and network install failed`);
	const buf = cacache.get.byDigest.sync(cacheDir, info.integrity);
	writeFileSync(tarball, buf);
	const pkgDir = path.join(HERE, 'node_modules', 'typescript');
	mkdirSync(pkgDir, { recursive: true });
	execFileSync('tar', ['-xzf', tarball, '-C', pkgDir, '--strip-components=1'], { stdio: 'pipe' });
}

export function ensureTypeScript() {
	if (tscOk()) return { installed: false };
	let how = 'npm';
	try { viaNpm(); } catch { how = 'cache-extract'; viaCacheExtract(); }
	if (!tscOk()) throw new Error('TypeScript bootstrap failed (npm install and cache extraction both failed)');
	return { installed: true, how };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
	const r = ensureTypeScript();
	console.log(r.installed ? `typescript@${TS_VERSION} installed via ${r.how}` : `typescript@${TS_VERSION} already present`);
}

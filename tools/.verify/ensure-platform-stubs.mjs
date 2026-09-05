#!/usr/bin/env node
/**
 * Ensures the minimal vs/platform declaration stubs exist for the type-check
 * slice (task Q5 §ه — «stub کردن چند ماژول پرتکرار vs/platform»).
 *
 * This sparse checkout has ~10% of the repo on disk; the heavy ledger files
 * (contextLedgerService, ledgerRecallService, agentMemoryService) import a
 * handful of vs/platform modules that are not materialized. Their REAL .ts
 * files are the source of truth upstream — these .d.ts files cover exactly
 * the API surface the slice uses, and become INERT the moment the real .ts
 * appears next to them (TypeScript prefers .ts over .d.ts).
 *
 * The stubs are local-only: this script appends their paths to
 * .git/info/exclude so they never get committed.
 */
import { existsSync, mkdirSync, appendFileSync, writeFileSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');

const STUBS = {
	// createDecorator returns a token usable BOTH as a parameter decorator and
	// (through the importing module's own type alias) as a type — mirrors
	// vs/platform/instantiation's ServiceIdentifier shape
	'src/vs/platform/instantiation/common/instantiation.d.ts':
`export interface ServiceIdentifier<T> { (...args: any[]): any; }
export interface IInstantiationService {
	invokeFunction<R>(fn: (accessor: any) => R): R;
	createInstance<C>(ctor: C, ...args: any[]): any;
}
export declare const IInstantiationService: any;
export declare function createDecorator<T>(id: string): T & ServiceIdentifier<T>;
`,
	'src/vs/platform/instantiation/common/extensions.d.ts':
`export declare function registerSingleton(id: any, ctor: any, type?: InstantiationType): void;
export declare enum InstantiationType { Delayed = 0, Eager = 1, Blocking = 2 }
`,
	// exactly the IFileService surface contextLedgerService touches
	'src/vs/platform/files/common/files.d.ts':
`export interface IFileService {
	readFile(uri: unknown): Promise<{ value: { toString(): string } }>;
	resolve(uri: unknown): Promise<{ children?: { name: string; size: number }[] }>;
	createFolder(uri: unknown): Promise<unknown>;
	writeFile(uri: unknown, content: unknown): Promise<unknown>;
	createFile(uri: unknown, content: unknown, options?: { overwrite?: boolean }): Promise<unknown>;
	del(uri: unknown, options?: { recursive?: boolean }): Promise<unknown>;
}
export declare const IFileService: any;
`,
	'src/vs/platform/workspace/common/workspace.d.ts':
`import type { URI } from '../../../base/common/uri.js';
export interface IWorkspaceContextService {
	getWorkspace(): { folders: { uri: URI }[] };
	isInsideWorkspace(resource: unknown): boolean;
}
export declare const IWorkspaceContextService: any;
`,
	// exactly the IStorageService surface agentMemoryService touches
	'src/vs/platform/storage/common/storage.d.ts':
`export interface IStorageService {
	get(key: string, scope: StorageScope): string | undefined;
	store(key: string, value: string, scope: StorageScope, target: StorageTarget): void;
	onWillSaveState(listener: (e: unknown) => void): { dispose(): void };
}
export declare const IStorageService: any;
export declare enum StorageScope { GLOBAL = 0, WORKSPACE = 1, APPLICATION = 2 }
export declare enum StorageTarget { MACHINE = 0, USER = 1 }
`,
	// exactly the INotificationService surface chatThreadService touches
	'src/vs/platform/notification/common/notification.d.ts':
`export interface INotification {
	severity: Severity;
	message: string;
	source?: string;
	sticky?: boolean;
	actions?: { primary: unknown[]; secondary?: unknown[] };
}
export interface INotificationService {
	notify(notification: INotification): { dispose(): void };
}
export declare const INotificationService: any;
export declare enum Severity { Ignore = 0, Info = 1, Warning = 2, Error = 3 }
`,
	// language feature registries: only `.ordered` iteration is used
	'src/vs/editor/common/services/languageFeatures.d.ts':
`export interface ILanguageFeaturesService {
	definitionProvider: { ordered(model: any): any[] };
	documentSymbolProvider: { ordered(model: any): any[] };
}
export declare const ILanguageFeaturesService: any;
`,
	// editor Position: constructed with (lineNumber, columnNumber)
	'src/vs/editor/common/core/position.d.ts':
`export declare class Position {
	readonly lineNumber: number;
	readonly column: number;
	constructor(lineNumber: number, column: number);
}
`,
	// workbench contribution registration (ledgerRecallContrib)
	'src/vs/workbench/common/contributions.d.ts':
`export declare const enum WorkbenchPhase { Eventually = 3 }
export declare function registerWorkbenchContribution2(id: string, ctor: any, phase: WorkbenchPhase): void;
`,
	// VS Code test helper imported by the browser-side ledger tests
	'src/vs/base/test/common/utils.d.ts':
`export declare function ensureNoDisposablesAreLeakedInTestSuite(): void;
`,
};

export function ensurePlatformStubs() {
	const created = [];
	for (const [rel, content] of Object.entries(STUBS)) {
		const dest = path.join(REPO, rel);
		const real = dest.replace(/\.d\.ts$/, '.ts');
		if (existsSync(dest) || existsSync(real)) continue; // real file wins; never overwrite
		mkdirSync(path.dirname(dest), { recursive: true });
		writeFileSync(dest, `// Local verify-harness stub — generated by tools/.verify/ensure-platform-stubs.mjs.\n// The real ${path.basename(real)} is the source of truth; this file is inert once it exists.\n` + content, 'utf8');
		created.push(rel);
	}
	if (created.length > 0) {
		const exclude = path.join(REPO, '.git', 'info', 'exclude');
		mkdirSync(path.dirname(exclude), { recursive: true });
		let existing = '';
		try { existing = readFileSync(exclude, 'utf8'); } catch { /* none yet */ }
		const marker = '# neuralinverse verify-harness platform stubs (local only)';
		if (!existing.includes(marker)) appendFileSync(exclude, `\n${marker}\n`);
		for (const rel of created) {
			if (!existing.includes(rel)) appendFileSync(exclude, `/${rel}\n`);
		}
	}
	return created;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
	const created = ensurePlatformStubs();
	console.log(created.length === 0
		? 'platform stubs: present (or real files exist)'
		: `platform stubs: created ${created.length} local .d.ts (git-excluded):\n  ${created.join('\n  ')}`);
}

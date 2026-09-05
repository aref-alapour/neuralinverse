/**
 * Minimal ambient declarations for the standalone verify harness (task Q5 §ه).
 *
 * The full repo type-checks tests against @types/node + @types/mocha from
 * node_modules, which does not exist in this partial clone. These stubs cover
 * EXACTLY the surface the slice's test files use (verified by grep:
 * assert.ok / assert.strictEqual / assert.deepStrictEqual) plus the mocha
 * globals — nothing more. The runtime side is the real node:assert module and
 * the shim in tools/run-tests-standalone.mjs.
 *
 * When a full `npm install` becomes possible, delete this file from the temp
 * tsconfig and use the real types instead (see task/full-typecheck path in
 * تسک/05-quality/full-typecheck.md).
 */

declare module 'assert' {
	export function ok(value: unknown, message?: string | Error): asserts value;
	export function strictEqual<T>(actual: unknown, expected: T, message?: string | Error): asserts actual is T;
	export function deepStrictEqual<T>(actual: unknown, expected: T, message?: string | Error): asserts actual is T;
	export function notStrictEqual(actual: unknown, expected: unknown, message?: string | Error): void;
	export function throws(block: () => unknown, message?: string | Error): void;
	export function ifError(value: unknown): asserts value is null | undefined;
}

// mocha globals (the standalone runner provides compatible implementations)
declare function suite(name: string, fn: () => void): void;
declare function test(name: string, fn?: () => void | Promise<void>): void;
declare namespace test {
	const skip: (name: string, fn?: () => void | Promise<void>) => void;
	const only: (name: string, fn?: () => void | Promise<void>) => void;
}
declare function setup(fn: () => void): void;
declare function teardown(fn: () => void): void;
declare function suiteSetup(fn: () => void | Promise<void>): void;
declare function suiteTeardown(fn: () => void | Promise<void>): void;
declare function ensureNoDisposablesAreLeakedInTestSuite(): void;

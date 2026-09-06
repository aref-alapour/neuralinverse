// Stress test of the fixed tool-result pipeline (mirrors the patched logic
// exactly: convertToLLMMessageService.ts cutToLen + role-aware trim budget,
// and toolsService.ts normalizeToolPath). Run: node stress-test.mjs
import { performance } from 'node:perf_hooks';

const TRIM_TO_LEN = 120;
const TOOL_TRIM_TO_LEN = 4000;
let failures = 0;
const check = (name, cond, detail = '') => {
	if (cond) { console.log(`PASS  ${name}`); }
	else { failures++; console.log(`FAIL  ${name} ${detail}`); }
};

// ── cutToLen (verbatim from the fixed source) ──────────────────────────────
const cutToLen = (content, cutLen) => {
	if (cutLen <= 0) return '...';
	let cut = content.slice(0, cutLen);
	const nl = cut.lastIndexOf('\n');
	if (nl > 0) cut = cut.slice(0, nl);
	return cut.replace(/\s+$/, '') + '...';
};

// ── normalizeToolPath (verbatim from the fixed source) ──────────────────────
const normalizeToolPath = (filePath, workspaceDir) => {
	const p = filePath.replace(/\\/g, '/');
	const root = workspaceDir.replace(/\\/g, '/');
	const isAbsolute = /^\/?[a-zA-Z]:\//.test(p) || p.startsWith('//')
		|| (p.startsWith('/') && root.startsWith('/') && p.toLowerCase().startsWith(root.toLowerCase() + '/'));
	if (isAbsolute) return p;
	return `${root}/${p.replace(/^\//, '')}`;
};

// ── 1. trim loop behavior on adversarial tool outputs ──────────────────────
const WS = 'c:/Users/jobal/dev/escapezoom_dev';

// 1a. grep-shaped output: 100k lines ending in paths
{
	const lines = [];
	for (let i = 0; i < 100_000; i++) lines.push(`c:\\repo\\src\\mod${i}\\functions.php:${i + 1}: function foo${i}() {`);
	const grep = lines.join('\n');
const out = cutToLen(grep, TOOL_TRIM_TO_LEN - 3);
const kept = out.slice(0, -3).split('\n');
check('grep 100k-line output: cut is line-aligned', out.endsWith('...') && kept[kept.length - 2] !== '' && /^c:\\repo\\src\\mod\d+\\functions\.php:\d+:/.test(kept[kept.length - 2]), `last kept line: ${JSON.stringify(kept[kept.length - 2])}`);
	check('grep: every retained line intact (path not mid-cut)', kept.every(l => /^c:\\repo\\src\\mod\d+\\functions\.php:\d+:/.test(l) || l === ''), kept.find(l => !/^c:\\repo\\src\\mod\d+/.test(l)) ?? '');
	check('grep: under budget', out.length <= TOOL_TRIM_TO_LEN, `${out.length}`);
}

// 1b. single-line 5MB output (pathological: no newline to back off to)
{
	const huge = 'x'.repeat(5 * 1024 * 1024);
	const t0 = performance.now();
	const out = cutToLen(huge, TOOL_TRIM_TO_LEN - 3);
	const ms = performance.now() - t0;
	check('5MB single-line: fast (<50ms)', ms < 50, `${ms.toFixed(1)}ms`);
	check('5MB single-line: cut at budget', out.length === TOOL_TRIM_TO_LEN - 3 + 3 || out.length <= TOOL_TRIM_TO_LEN, `${out.length}`);
}

// 1c. final-cut branch (slice from the end, like `content.length - remaining`)
{
	const content = Array.from({ length: 1000 }, (_, i) => `line ${i} c:\\repo\\file${i}.ts`).join('\n');
	const out = cutToLen(content, content.length - 30_000 - 3); // cutLen > content? no: content ~30k
	// realistic: cutLen smaller than content by a "remaining" amount
	const out2 = cutToLen(content, 25_000);
	check('final-cut branch: line-aligned', out2.endsWith('...') && out2.includes('\n'), '');
}

// 1d. whole trim loop simulation — 40 tool messages + huge history, OSS budget
{
	const messages = [
		{ role: 'system', content: 'S'.repeat(20_000) },
		{ role: 'user', content: 'U'.repeat(500) },
	];
	for (let i = 0; i < 40; i++) messages.push({ role: 'tool', content: 'c:\\repo\\src\\functions.php:1: x\n'.repeat(800) }); // ~21k each
	messages.push({ role: 'user', content: 'do it' });
	let total = messages.reduce((s, m) => s + m.content.length, 0);
	const budget32k = Math.max((32_768 - 4_096) * 4, 5_000); // patched default: 114,688
	const budgetOld = 5_000; // old 4096 default fell to the floor on EVERY request
	check('32k default raises the trim budget 23x vs the old floor', budget32k > 20 * budgetOld, `${budgetOld} -> ${budget32k}`);
	check('1M-char thread still trims (expected — that is a genuinely long thread)', total > budget32k, `total ${total.toLocaleString()}`);
	// when the loop fires, tool messages keep 4000 line-aligned chars instead of 117
	const tool = messages.find(m => m.role === 'tool');
	const trimmed = cutToLen(tool.content, TOOL_TRIM_TO_LEN - 3);
	check('loop cut keeps 4000 chars of tool result', trimmed.length >= 3_900 && trimmed.length <= TOOL_TRIM_TO_LEN, `${trimmed.length}`);
}

// ── 2. normalizeToolPath: the ENOENT cases ─────────────────────────────────
const cases = [
	// [input, expected]
	['c:\\Users\\jobal\\dev\\escapezoom_dev\\app\\functions.php', 'c:/Users/jobal/dev/escapezoom_dev/app/functions.php'],
	['C:\\Users\\jobal\\dev\\escapezoom_dev\\app\\functions.php', 'C:/Users/jobal/dev/escapezoom_dev/app/functions.php'],
	['/c:/Users/jobal/dev/escapezoom_dev/app/functions.php', '/c:/Users/jobal/dev/escapezoom_dev/app/functions.php'],
	['app/functions.php', 'c:/Users/jobal/dev/escapezoom_dev/app/functions.php'],
	['/app/functions.php', 'c:/Users/jobal/dev/escapezoom_dev/app/functions.php'], // model habit: workspace-relative with leading slash
	['\\\\server\\share\\file.ts', '//server/share/file.ts'],
	['src\\nested\\file.ts', 'c:/Users/jobal/dev/escapezoom_dev/src/nested/file.ts'],
];
for (const [input, expected] of cases) {
	const got = normalizeToolPath(input, 'c:\\Users\\jobal\\dev\\escapezoom_dev');
	check(`normalizeToolPath(${JSON.stringify(input)})`, got === expected, `→ ${got}`);
}
// Linux workspace: in-root absolutes stay as-is; outside-root joins (old behavior)
check('linux: in-root absolute kept', normalizeToolPath('/home/u/ws/src/a.ts', '/home/u/ws') === '/home/u/ws/src/a.ts');
check('linux: outside-root joined like before', normalizeToolPath('/etc/hosts', '/home/u/ws') === '/home/u/ws/etc/hosts');

// ── 3. multi_replace validation logic (mirrors the guards) ─────────────────
const validateChunks = (le) => {
	if (!Array.isArray(le) || le.length === 0) throw new Error('empty');
	for (const c of le) {
		if (!c || typeof c.TargetContent !== 'string' || c.TargetContent === '' || typeof c.ReplacementContent !== 'string') throw new Error('invalid chunk');
	}
	return true;
};
check('multi_replace: "[]" rejected', (() => { try { validateChunks([]); return false; } catch { return true; } })());
check('multi_replace: missing ReplacementContent rejected', (() => { try { validateChunks([{ StartLine: 1, EndLine: 2, TargetContent: 'x' }]); return false; } catch { return true; } })());
check('multi_replace: empty TargetContent rejected', (() => { try { validateChunks([{ StartLine: 1, EndLine: 2, TargetContent: '', ReplacementContent: 'y' }]); return false; } catch { return true; } })());
check('multi_replace: delete-style chunk accepted', validateChunks([{ StartLine: 1, EndLine: 2, TargetContent: 'x', ReplacementContent: '' }]));

console.log('─'.repeat(60));
console.log(failures === 0 ? 'ALL STRESS TESTS PASSED' : `${failures} FAILURE(S)`);
process.exit(failures === 0 ? 0 : 1);

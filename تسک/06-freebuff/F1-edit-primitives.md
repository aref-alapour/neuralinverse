# F1 — ابزارهای ویرایش قطعی: str_replace + لایه‌ی تعمیر ورودی + خواندن پنجره‌ای

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P0 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** —
- **منبع الگو:** freebuff (Codebuff snapshot) — راستی‌آزمایی‌شده روی کد
- **چرا مهم است:** الان `fsTools.ts` فقط `writeFile` کل‌فایلی دارد — یعنی هر ویرایش
  کوچک، بازنویسی کل فایل است. این پرخطاترین و پرهزینه‌ترین ابزار ممکن برای مدل است.

## الف) str_replace قطعی با لایه‌ی تعمیر

**منبع (همه تأییدشده):**
- `common/src/tools/params/tool/str-replace.ts` — اسکیمای `{path, replacements[{oldString(min 1), newString(میتواند ""=حذف), allowMultiple}]}`؛
  نتیجه union است نه exception: `{file, message} | {file, errorMessage, patch?}`
- `common/src/tools/params/utils.ts` — `coerceToArray` (LLM آرایه را تکی/رشته‌ای می‌فرستد)،
  `coerceToObject`، `normalizeReplacementAliases` (نگاشت `old/old_str/old_string→oldString`
  و `new/new_str/new_string→newString`)، `$getNativeToolCallExampleString` (تولید example
  call داخل description)
- `packages/agent-runtime/src/tools/tool-executor.ts` — `parseRawToolCall` (L196):
  `parseStringifiedToolInput` تا ۳ بار JSON.parse برای ورودی دوبار-encode شده؛
  `getToolValidationHint` (L186) hint های per-tool؛ `summarizeMissingReplacementFields`
  (L148: «اگر قصد حذف است، newString را صریحاً "" بگذار»)؛ خطا همیشه به‌صورت
  `ToolCallError` object برمی‌گردد، هرگز throw نمی‌شود
- `common/src/tools/params/tool/apply-patch.ts` — پریمیتیو سوم ویرایش (union ای از
  create_file/update/delete به شکل diff) — به‌عنوان fallback برای تغییرات بزرگ

**پیاده‌سازی در ما:**
1. ابزار `str_replace` جدید در `tools/fsTools.ts` با همان semantics (batch در یک call)؛
   اجرا از طریق `workspace.applyEdit` با یافتن range با exact match
2. لایه‌ی تعمیر ورودی در مسیر `toolCallParser.ts` / اجرای ابزار: coercion ها + alias ها +
   hint های خطا (مستقل از مدل — با ۲۲ provider ما این لایه طلاست)
3. سبک description ها: قوانین رفتاری + example call تولیدشده داخل توضیح ابزار
   (سبک مستندسازی freebuff — در `toolRegistry.ts`)
4. `apply_patch` برای diff های بزرگ (تک‌فراخوان به‌جای چند str_replace)

## ب) خواندن پنجره‌ای با footer خودتوصیف

**منبع:** `common/src/util/file-read-limits.ts` — per-call: 100k کاراکتر / 20k توکن؛
per-file: 2000 خط / 50k کاراکتر؛ `windowFileRead(offset, limit)`؛ footer:
`[read_files: showing lines X–Y of Z ... call again with offset=N]`؛
`avoidSplittingSurrogatePair` (ایموجی نصف‌شده = درخواست‌های مسموم بعدی).

**پیاده‌سازی:** پارامترهای `offset/limit` روی `readFile` ما + همان footer ها +
ترانکیشن surrogate-safe. (ما `capToolResultForHistory` برای تاریخچه داریم؛ این
مستقیماً روی خروجی ابزار است.)

## ج) referencedBy روی خواندن فایل‌ها

**منبع:** `packages/code-map/src/parse.ts` — `scoreFileTokens` (L269):
`0.8^depth * sqrt(numLines/(identifiers+1))`؛ `boostScoresByExternalCalls`:
`×(1+log(1+calls))`؛ `buildTokenCallers` (نقشه‌ی وابسته‌های معکوس، سقف ۲۵)؛
اتصال در `render-read-files-result.ts` (L15): هر فایل خوانده‌شده `referencedBy`
می‌گیرد (چه فایل‌هایی symbol های این فایل را صدا می‌زنند) — مدل blast radius را
بدون یک grep اضافه می‌فهمد.

**پیاده‌سازی در ما:** داده از قبل داریم! `dependencyGraph.ts` + `workspaceSymbolIndex.ts`.
فقط plumbing: خروجی `readFile` (هم در fsTools هم ابزارهای chat) سطر
`referencedBy: [...]` بگیرد. فرمول امتیازدهی freebuff را هم با `relevanceScorer`
خودمان مقایسه/ادغام کن (تسک C5 هم‌راستاست).

## معیارهای پذیرش
- [ ] ویرایش ۳ خطی در فایل ۱۰۰۰ خطی بدون بازنویسی کل فایل انجام می‌شود
- [ ] ورودی خراب مدل (تکی‌جای‌آرایه، alias، دوبار-encode‌شده) به‌جای خطا، تعمیر می‌شود
- [ ] عدم تطابق oldString → نتیجه‌ی ساخت‌یافته با hint، مدل دور بعد اصلاح می‌کند (نه crash)
- [ ] فایل ۵۰۰۰ خطی با offset/limit خوانده می‌شود و footer مسیر ادامه را می‌گوید
- [ ] خروجی readFile شامل referencedBy است (روی این repo خودمان قابل مشاهده)
- [ ] attribution: هدر Apache 2.0 در فایل‌های پورت‌شده + ثبت در `ThirdPartyNotices.txt`

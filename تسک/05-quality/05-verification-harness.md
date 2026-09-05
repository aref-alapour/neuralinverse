# Q5 — هارنس راستی‌آزمایی (type-check و تست بدون build کامل)

- **اولویت:** P0 — پیش‌نیاز بستن دروازه‌ی «done» هر تسک بزرگ | **برآورد:** M | **وضعیت:** 🔴
- **وابستگی:** — | **مرتبط:** [Q4](04-live-patch-integrity.md)، [M5](../01-memory/05-context-ledger.md)

## چرا این تسک وجود دارد

روی شاخه‌ی `feat/context-ledger` (۶٬۲۱۵ خط جدید) خواستیم مطمئن شویم کد کامپایل
می‌شود. نشد. اندازه‌گیری‌های ۲۰۲۶-۰۹-۰۵:

| واقعیت | عدد |
|---|---|
| فایل‌های src در git (هر پسوندی) | ۹٬۲۹۲ |
| از این‌ها روی دیسک (sparse-checkout) | **۸۹۵ (۹.۶٪)** |
| فایل‌های `.ts`/`.tsx` در git | ۸٬۰۵۹ |
| از این‌ها روی دیسک | **۷۹۲ (۹.۸٪)** — از این تعداد ۷۵۴ تا `.ts` و ۳۸ تا `.tsx` |
| `node_modules` | **صفر پکیج** |
| نوع کلون | partial (`filter=blob:none`) |
| `postinstall` | `node build/npm/postinstall.ts` — و `build/` اصلاً checkout نشده |

نتیجه: `npm install` همان ثانیه‌ی اول می‌شکند و `tsc -p src/tsconfig.json` هزاران خطای
`cannot find module` می‌دهد که همه artifact محیط‌اند نه باگ کد.

با یک tsconfig موقت (با **همان** گزینه‌های سخت‌گیرانه‌ی repo) توانستیم فقط بخش
self-contained را چک کنیم:

| | خطوط |
|---|---|
| type-check شده و سبز | ۲٬۲۹۶ |
| type-check نشده | ۳٬۸۸۱ |
| **پوشش** | **۳۷٪** |

و از ۱۱۲ تست کامیت‌شده، فقط ۶۷ تا قابل اجرا بودند (بقیه از `browser/` وارد می‌کنند و
`vs/platform` را می‌کشند). یعنی سنگین‌ترین فایل‌ها — `contextLedgerService` (۷۵۸)،
`episodeSummarizer` (۶۵۹)، `ledgerRecallService` (۴۲۷) و همه‌ی ویرایش‌های
`chatThreadService`/`agentExecutor` — **هرگز کامپایل نشده‌اند**.

سه باگ واقعی هم در همین ممیزی پیدا و رفع شد (کامیت `955b621d`): migration نبودن
فلگ `contextLedgerEnabled` که Ledger را روی هر نصب موجود بی‌صدا خاموش می‌کرد،
ناپایداری round-trip در `mergeEpisodeBodies`، و یک import با عمق اشتباه در
`ledgerRecall.test.ts` که یعنی آن فایل هرگز کامپایل نشده بود. دو تای اول را ابزار
پیدا نکرد — دستی پیدا شدند. این تسک همان ابزار را می‌سازد.

## هدف

سه چیز که بدون `npm install` کامل و بدون build کار کنند:

1. type-check روی برشِ قابل‌بررسی، با گزینه‌های دقیقِ repo
2. اجرای تست‌های خالص (بدون وابستگی به mocha و زیرساخت تست repo)
3. یک دستور واحد که درصد پوشش را گزارش کند و در صورت هر خطا `exit 1` بدهد

به‌علاوه یک مسیر مستندشده برای وقتی که پوشش ۱۰۰٪ لازم است.

## طرح پیاده‌سازی

### الف) `tools/typecheck-slice.mjs`
- یک لیست فایل صریح در `tools/typecheck-slice.json` (شروع: پنج فایل ledger در
  `void/common` + سه تست node شان)
- tsconfig موقت در پوشه‌ی temp با **کپی دقیق** `compilerOptions` از
  `src/tsconfig.base.json` (`strict`, `noUnusedLocals`, `noImplicitOverride`,
  `noImplicitReturns`, `allowUnreachableCode:false`, `noUncheckedSideEffectImports`)
- typescript به‌صورت devDependency محلی در `tools/.verify/` (کوچک، مستقل از
  `node_modules` ریشه)
- خطاها فیلتر شوند به فایل‌های همان لیست؛ خطاهای فایل‌های خارج از cone (که artifact
  sparse-checkout اند) شمرده ولی جدا گزارش شوند
- **self-test اجباری:** یک خطای عمدی در یک فایل موقت تزریق کند و انتظار داشته باشد
  که tsc آن را بگیرد. اگر نگرفت، هارنس خودش را قرمز اعلام کند. (بدون این، «صفر خطا»
  می‌تواند یعنی «هیچ فایلی اصلاً تحلیل نشد».)

### ب) `tools/run-tests-standalone.mjs`
- shim سازگار با mocha: `suite` / `test` / `setup` / `teardown` / `suiteSetup` +
  no-op برای `ensureNoDisposablesAreLeakedInTestSuite`
- اجرای فایل‌های `*.test.ts` با type-stripping بومی Node
- تبدیل خودکار import های type-only به `import type` **در کپی موقت** (سورس هرگز
  دست نمی‌خورد) — چون Node تایپ‌ها را پاک می‌کند ولی تشخیص نمی‌دهد
- خروجی: تعداد pass/fail + نام تست‌های شکست‌خورده + `exit 1`

### ج) `tools/verify.mjs` (دستور واحد)
اجرای الف + ب، و چاپ:

```
type-check : 8 files, 2296 lines — 0 errors
tests      : 67 passed, 0 failed
coverage   : 37% of the branch diff type-checked   (3881 lines NOT checked)
NOT CHECKED: contextLedgerService.ts, episodeSummarizer.ts, ledgerRecallService.ts, …
```

آن خط آخر مهم‌ترین بخش است: هارنس باید **صادقانه بگوید چه چیزی را ندیده**، وگرنه
خروجی سبزش گمراه‌کننده‌تر از نبودنش است.

### د) مسیر پوشش کامل (مستندسازی، نه اتوماسیون)
در `تسک/05-quality/full-typecheck.md` ثبت شود:

```bash
git sparse-checkout set --cone build src resources tools "تسک"
ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm install --ignore-scripts
npx tsc -p src/tsconfig.json --noEmit
```

با هشدار هزینه (چند صد مگابایت دانلود چون کلون partial است) و دستور برگشت به حالت
سبک (لیست اصلی sparse در `scratchpad/sparse-original.txt` نگهداری شود، یا بهتر:
در `tools/sparse-light.txt` کامیت شود).

### ه) گسترش تدریجی لیست
هر بار که فایلی از cone قابل‌چک شد (یا وابستگی‌اش stub شد)، به
`typecheck-slice.json` اضافه شود. هدف میان‌مدت: بردن پوشش از ۳۷٪ به بالای ۸۰٪ با
stub کردن چند ماژول پرتکرار `vs/platform` به‌صورت `.d.ts` در `tools/.verify/stubs/`.

## معیارهای پذیرش

- [ ] `node tools/verify.mjs` بدون هیچ نصب اضافه‌ای در این checkout اجرا می‌شود
- [ ] روی HEAD فعلی: `0 errors` و `67 passed` گزارش می‌دهد
- [ ] self-test: با تزریق خطای عمدی، هارنس قرمز می‌شود (تست خودِ هارنس)
- [ ] درصد پوشش و **فهرست فایل‌های چک‌نشده** در خروجی می‌آید
- [ ] یک تست شکست‌خورده → `exit 1` (قابل استفاده در گیت DoD)
- [ ] `AGENTS.local.md`: به DoD اضافه شود «`node tools/verify.mjs` سبز» قبل از commit
- [ ] مسیر پوشش کامل مستند و تست‌شده است (یک‌بار اجرا و نتیجه ثبت شود)

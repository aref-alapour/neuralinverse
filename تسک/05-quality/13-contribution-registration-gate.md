# Q13 — کدی که کامپایل می‌شود ولی ثبت نمی‌شود (گیت registration)

- **اولویت:** **P0 (تصمیم، نه کد)** | **برآورد:** S (تصمیم) + M (اجرا) | **وضعیت:** 🟡
  (G1+G2 کامل: تصمیم + کامنت + گیت + commit موج ۱، 2026-09-08؛
  تست owner = اجرای سبز `node tools/verify.mjs`)
- **کشف:** ۲۰۲۶-۰۹-۰۸، [ممیزی سه‌گانه](task-vs-code-audit-2026-09-08.md) — بستن N5 در [Q8](08-open-debt-register.md)
- **بلاک‌کننده‌ی:** [A1](../03-agent-parity/01-background-agents-loop.md)، [A6](../03-agent-parity/06-multi-agent-composer.md)

## مسئله

`neuralInverse.contribution.ts` تنها جایی است که یک دسته سرویس و پنل را ثبت
می‌کند، و **هیچ‌کس import اش نمی‌کند** — نه در سورس، نه در باندل ساخته‌شده:

```bash
grep -rn "neuralInverse\.contribution" src build out   # صفر در هر سه
```

این با [Q10](10-unbuilt-contribs-checks-enclave.md) فرق دارد: Checks و Enclave
**عمداً** از `tsconfig` و workbench کنار گذاشته شده‌اند و در کد کامنت مستند دارند.
اینجا کد typecheck سبز می‌گیرد، در تست‌ها شرکت می‌کند، در ممیزی‌ها به‌عنوان
«زیرساخت آماده» شمرده می‌شود — و اجرا نمی‌شود.

### تفکیک دقیق: چه چیزی مرده است و چه چیزی نه

هر ماژولی زیر این پوشه مرده **نیست**. بعضی‌ها ترانزیتی از contrib های ثبت‌شده
بالا می‌آیند:

| ماژول | مسیر رسیدن | وضعیت |
|---|---|---|
| `workflowAgentService` + `orchestrator/` + `executor/` + `budgetTracker` | `contrib/void/browser/toolsService.ts:34` (import ایستا) | ✅ زنده |
| موتور context (`context/**`) | `toolsService.ts:297–313, 1149–1199` (import پویا) | ✅ زنده |
| `fim/neuralInverseFIMService` | `contrib/void/browser/autocompleteService.ts:22` | ✅ زنده |
| `powerMode/powerBusService` | ترانزیتی از `workflowAgentService.ts:52` | ✅ زنده |
| **`backgroundAgentService` + `backgroundAgentPanel` + `backgroundAgentCommands` + `agentManagerPart`** | فقط contribution | ❌ **مرده** |
| **`composer/composerModule`** | فقط contribution | ❌ **مرده** |
| **`agentStoreService`، سینگلتون‌های `modelManagement`** | فقط contribution | ❌ **مرده** |
| **`powerMode.contribution`** (ثبت قابلیت‌های Power Mode) | فقط contribution | ❌ **مرده** |

```bash
grep -rn "backgroundAgentService\|composerModule\|agentManagerPart" src --include=*.ts \
  | grep -v contrib/neuralInverse/     # صفر → ستون مرده
```

### بازبینی هنگام اجرا (۲۰۲۶-۰۹-۰۸) — دو ردیف جدول نیاز به اصلاح دارند

گیت import-graph که ساخته شد (و .js ها را هم راه می‌رود، برخلاف grep بالا که
`--include=*.ts` داشت) نشان داد:

| ردیف | ادعای جدول بالا | واقعیت فعلی |
|---|---|---|
| `backgroundAgentService` | مرده | **سرویس + `registerSingleton` (خط ۲۸۷ خود فایل) زنده است** از مسیر: `sessions.common.main` ← `fileActions.contribution:30` ← `voidSettingsPane:26` ← باندل کامپایل‌شده‌ی `react/out/void-settings-tsx/index.js` ← shim در `void/neuralInverse/browser/backgroundAgentService.js` ← فایل .ts. پنل/کامندها/`agentManagerPart` همچنان مرده‌اند. |
| `agentStoreService` | مرده | **زنده** از مسیر `workflowAgentService.ts:37` (که خودش زنده است). سینگلتون‌های `modelManagement` (marketplace/cloud) همچنان مرده‌اند — فقط در contribution ثبت می‌شوند. |

نکته: «ثبت‌شده» به معنی «کار می‌کند» نیست — مغز LLM همان A1 است و پنل/مارکت‌پلیس
بدون همان contribution بالا نمی‌آیند. تصمیم گزینه‌ی ۲ را تغییر نمی‌دهد.

**کشف جدید خارج از جدول:** `contrib/agentsVoice/browser/transcriptsView/voiceEventStream.contribution.ts`
هم یتیم است — نه در این درخت کسی import اش می‌کند، نه upstream خودش (بررسی شد:
`agentsVoice.contribution.ts` در upstream فقط `voiceTranscripts.contribution` را
import می‌کند). به‌عنوان DISCREPANCY در allowlist گیت ثبت شده؛ تصمیم نگه‌داشتن/حذف
با owner است (کد upstream است، خارج از scope این تسک).

## چرا این P0 است حتی با اینکه «فقط» چند پنل است

سه تسک (A1، A6، و بخشی از Q1) روی این کد برنامه‌ریزی شده‌اند و برآورد خورده‌اند.
هر ممیزی‌ای که فایل را ببیند و importer را چک نکند، آن را «آماده» گزارش می‌کند —
همان اتفاقی که در هر سه ممیزی ۲۰۲۶-۰۹-۰۸ به شکل‌های مختلف افتاد. تا این تصمیم
گرفته نشود، برآوردهای A1 و A6 بی‌معنی‌اند.

## تصمیم لازم (یکی از سه)

1. **ثبت کن** — `neuralInverse.contribution.js` به `workbench.common.main.ts`
   اضافه شود. هزینه: باید همه‌ی سرویس‌های وابسته واقعاً کار کنند، وگرنه پنل خراب
   به کاربر نشان داده می‌شود. قبلش A1 باید مغز داشته باشد و باگ `/tmp` رفع شود.
2. **کنار بگذار مثل Q10** — از `tsconfig` exclude شود + کامنت مستند در
   `workbench.common.main.ts` که چرا. صادقانه‌ترین گزینه اگر A1/A6 به‌زودی
   اجرا نمی‌شوند.
3. **حذف کن** — اگر مسیر جدید A1 «وصل‌شدن به `agentSessions` upstream» است
   (توصیه‌ی ممیزی)، پنل و سرویس قدیمی اصلاً آینده ندارند.

**پیشنهاد:** گزینه‌ی ۲ حالا، گزینه‌ی ۳ بعد از بسته‌شدن A1 روی زیرساخت upstream.

## معیار پذیرش

1. تصمیم بالا در همین فایل ثبت و اعمال شود.
2. **گیت خودکار** در `tools/verify.mjs`: هر `*.contribution.ts` که از هیچ ورودی
   workbench (مستقیم یا ترانزیتی) قابل رسیدن نیست، باید build را قرمز کند مگر
   اینکه در یک allowlist مستند با دلیل ثبت شده باشد. این گیت همان چیزی است که
   Q10 و Q13 هر دو را از تکرار مصون می‌کند.
3. گیت روی وضعیت فعلی اجرا شود و دقیقاً دو مورد شناخته‌شده را گزارش کند
   (`neuralInverse`، و Checks/Enclave در allowlist).
4. یک خط در [Q8](08-open-debt-register.md) که N5 را بسته اعلام کند.

## درس روشی (برای همه‌ی ممیزی‌های بعدی)

معیار «انجام شده» برای هر تسک باید چهار چیز داشته باشد، نه یکی:
**فایل پیاده‌سازی + `registerSingleton`/contribution + caller واقعی + سناریوی
قابل‌مشاهده در UI**. سه ممیزی مستقل روی این کدبیس نشان دادند که چک‌کردن فقط
مورد اول، هم false-positive می‌دهد (کد مرده = «آماده») و هم false-negative
(«grep پیدا نکرد» = «وجود ندارد»).

## ثبت اجرا (۲۰۲۶-۰۹-۰۸)

- **تصمیم (گزینه ۲ — کنار بگذار مثل Q10):** اعمال شد. کامنت مستند در
  `src/vs/workbench/workbench.common.main.ts` (بالای import های Checks/Enclave)
  که چرا `neuralInverse.contribution.ts` ثبت نمی‌شود و شرط ثبتش چیست (بسته‌شدن
  A1). از `tsconfig` exclude نشد — برخلاف Checks/Enclave این پوشه کامپایل می‌شود
  و باید بشود (بخش‌های زنده‌اش مثل workflow/context/fim از همین کامپایل بالا
  می‌آیند).
- **گیت خودکار:** در `tools/verify.mjs` (قدم ۴ هر اجرا؛ همچنین
  `node tools/verify.mjs --trace <fragment>` برای دیدن زنجیره‌ی import ها).
  ریشه‌ها = ورودی‌های واقعی باندل (`src/main.ts`، `src/cli.ts`،
  `src/server-main.ts`، `src/server-cli.ts`، همه‌ی `*.main.ts`/`*.main.internal.ts`
  زیر `src/vs`، و نام‌های ماژول در `build/buildfile.ts`). یال‌ها =
  import/export-from/`require`/`import()` پویا؛ کامنت‌ها حذف می‌شوند تا
  import های کامنت‌شده (مثل Q10) به‌عنوان یال شمرده نشوند. فایل‌های `.js`
  هم راه می‌روند (به همین دلیل زنجیره‌ی react-bundle بالا دیده شد).
- **خروجی اجرا روی درخت فعلی:** ۲۵۹ فایل `*.contribution.ts`؛ ۲۵۳ قابل‌رسیدن؛
  ۶ یتیم همگی در allowlist مستند (neuralInverse + powerMode با دلیل Q13،
  Checks + Enclave×۲ با دلیل Q10، voiceEventStream به‌عنوان DISCREPANCY جدید)؛
  «unexpected orphans: 0» — سبز.
- **مصداق ترانزیتیو:** `workflowAgentService.ts` سبز است از مسیر
  `workbench.common.main.ts` ← `void.contribution.ts` ← `toolsService.ts:34`
  ← خود فایل — دقیقاً همان زنجیره‌ای که جدول بالا ادعا می‌کرد.

### باقیمانده برای owner

1. ~~**commit** این تغییرات~~ — انجام شد (commit موج ۱، 2026-09-08).
2. اجرای `node tools/verify.mjs` و دیدن گیت سبز (G3/G4 همین است — تغییر
   runtime ندارد، پس پورت live-patch موضوعیت ندارد). اجرای orchestrator سبز بود؛
   تأیید نهایی با owner.
3. یک خط در [Q8](08-open-debt-register.md) برای بستن N5 + به‌روزرسانی ردیف Q13 در
   جدول وضعیت `تسک/README.md` — هر دو توسط orchestrator در commit docs موج ۱.
4. تصمیم درباره‌ی `voiceEventStream.contribution.ts` (نگه‌داشتن به‌عنوان WIP
   upstream یا حذف).
5. هنگام بسته‌شدن A1: uncomment کردن import در `workbench.common.main.ts` و
   حذف دو مدخل Q13 از allowlist گیت (گیت خودش STALE می‌گوید اگر فراموش شد).

# Q13 — کدی که کامپایل می‌شود ولی ثبت نمی‌شود (گیت registration)

- **اولویت:** **P0 (تصمیم، نه کد)** | **برآورد:** S (تصمیم) + M (اجرا) | **وضعیت:** 🔴
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

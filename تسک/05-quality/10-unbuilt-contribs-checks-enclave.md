# Q10 — دو contrib ساخته‌نشده: Checks و Enclave

- **اولویت:** P1 (تصمیم محصولی) | **برآورد:** L یا حذف | **وضعیت:** 🔴 (از کامپایل خارج شد)
- **کشف:** ۲۰۲۶-۰۹-۰۷، حین [کمپین بیلد Q7](07-source-build-campaign.md) — اولین کامپایل
  واقعی این فورک
- **شاخه:** `feat/context-ledger`

## چه اتفاقی افتاد

اولین کامپایل کامل از سورس ۱۷۷ خطا داد. بعد از رفع شش خطای خودمان و دو ناحیه‌ی
واقعاً خراب (`open-remote-ssh` و `firmware`)، **۱۵۵ خطا ماند و همه‌شان در این دو
contrib بودند**. بررسی نشان داد این‌ها کد خرابِ قابل‌تعمیر نیستند؛ **فیچرهایی‌اند
که UI شان نوشته شده ولی لایه‌ی سرویسشان هرگز ساخته نشده.**

هر دو روی `origin/main` هم دقیقاً همین وضعیت را دارند و شاخه‌ی Ledger هیچ فایلی از
آن‌ها را لمس نکرده (`git diff --name-only origin/main...HEAD` → صفر فایل).

## `neuralInverseEnclave` — ۳۰ خطا

کل contrib **۸ فایل** دارد. `browser/parts/enclaveManagerPart.ts` این ۱۵ سرویس را
ایمپورت می‌کند که هیچ‌کدام روی دیسک وجود ندارند:

```
common/services/firewall/enclaveFirewallService.js
common/services/sandbox/enclaveSandboxService.js
common/services/audit/enclaveAuditTrailService.js
common/services/attestation/enclaveAttestationService.js
common/services/session/enclaveSessionService.js
common/services/toolchain/enclaveToolchainService.js
common/services/sbom/enclaveSBOMService.js
common/services/analysis/enclaveAnalysisProofService.js
common/services/commit/enclaveCommitService.js
common/services/build/enclaveBuildService.js
common/services/integrity/enclaveFileIntegrityService.js
common/services/test/enclaveTestProofService.js
common/services/review/enclaveReviewService.js
common/services/vault/enclaveVaultService.js
```

(به‌اضافه‌ی دو ایمپورت همان‌ها از `browser/services/actionLog/enclaveActionLogService.ts`.)

## `neuralInverseChecks` — ۱۲۵ خطا

| کد | تعداد | معنی |
|---|---|---|
| TS2339 | ۷۵ | UI متدهایی را صدا می‌زند که روی اینترفیس سرویس تعریف نشده‌اند (`createSession`, `cancel`, `queryViolations`, `toggleRule`, `deleteRule`, `saveRule`, `importFramework`, `triggerAIAnalysis`, `dismiss`, …) |
| TS7006 | ۲۳ | `any` ضمنی — معلولِ موارد بالا |
| TS2307 | ۹ | ماژول ناموجود |
| TS2551/2554/2305/2741/18048/6133/2882 | ۱۸ | امضای غلط، عضو ناموجود، احتمال undefined |

نه ماژول ناموجود:

```
./checksAgentProcessor.js
./ai/nanoAgentService.js
./projectAnalyzer.js
../engine/services/auditTrailService.js
../engine/services/complianceReportService.js
../engine/config/invariantConfigLoader.js
../dependencyTracker/dependencyTrackerService.js
../extensionTracker/extensionTrackerService.js
../projectConfigSyncService.js
```

پرخطاترین فایل‌ها: `checksManagerPart.ts` (۴۰)، `checksAgentTerminalHost.ts` (۲۱)،
`checksSocketService.ts` (۱۷)، `voidGRCToolsContrib.ts` (۱۰).

## تصمیم گرفته‌شده (۲۰۲۶-۰۹-۰۷، توسط مالک)

**از کامپایل خارج شوند** — نه حذف، نه پیاده‌سازی حدسی. دلیل: پیاده‌سازی یعنی
اختراع رفتار محصول در حوزه‌ی امنیت و انطباق (فایروال، سندباکس، attestation، SBOM،
vault، موتور GRC)؛ کدی که کامپایل می‌شود و معنایش ساختگی است از خطای کامپایل بدتر
است. این دو contrib در وضعیت فعلی به‌هرحال کار نمی‌کنند، پس چیزی از دست نمی‌رود.

دو تغییر، هر دو با کامنت و کاملاً برگشت‌پذیر:

1. `src/vs/workbench/workbench.common.main.ts` — دو `import` کامنت شد (ثبت
   contribution متوقف شد).
2. `src/tsconfig.json` — دو مسیر به `exclude` اضافه شد.

## راه برگشت

هر دو تغییر را با هم برگردان (کامنت‌ها همدیگر را ارجاع می‌دهند). کامپایل تا وقتی
سرویس‌های بالا وجود نداشته باشند دوباره ۱۵۵ خطا می‌دهد.

## معیارهای پذیرش برای بستن Q10

یکی از این دو مسیر، با تصمیم صریح مالک:

- **الف) ساخت:** ۱۵ سرویس enclave و ۹ ماژول Checks پیاده شوند، اینترفیس‌ها به آنچه
  UI صدا می‌زند برسند، و هر دو contrib دوباره ثبت و از `exclude` خارج شوند — با
  کامپایل سبز و تست.
- **ب) حذف:** اگر این فیچرها روی نقشه نیستند، کل دو پوشه و UI مرده‌شان حذف شوند تا
  کدبیس ادعای چیزی را نکند که ندارد. تاریخچه‌ی گیت طرح UI را نگه می‌دارد.

تا وقتی یکی از این دو انجام نشده، **این دو فیچر نباید در هیچ معرفی یا README
به‌عنوان قابلیت موجود ذکر شوند.**

# Q11 — بدهی لینت دو فایل هسته + حذف shim خلاصه‌ساز

- **اولویت:** P2 | **برآورد:** M | **وضعیت:** 🔴
- **کشف:** ۲۰۲۶-۰۹-۰۷، حین فاز ۴ از [کمپین بیلد Q7](07-source-build-campaign.md)
- **وابستگی:** ندارد، ولی تا بسته نشود یک فایل shim در ریپو می‌ماند

## چرا این تسک وجود دارد

`episodeSummarizer.ts` هیچ وابستگی DOM نداشت و همه‌ی ایمپورت‌هایش از `common/` بود،
ولی در `browser/` نشسته بود — و تستِ `test/node/` آن، طبق قاعده‌ی `code-layering`،
اجازه ندارد از `browser/` ایمپورت کند. پس فایل به `common/episodeSummarizer.ts`
منتقل شد (هم‌الگو با `common/ledgerJournalCore.ts` که از قبل هست).

سه مصرف‌کننده داشت. دو تای اول در استک هسته‌اند:

- `src/vs/workbench/contrib/neuralInverse/browser/executor/agentExecutor.ts`
- `src/vs/workbench/contrib/void/browser/chatThreadService.ts`

به‌روزکردن مسیر ایمپورت در این دو **یک خط در هرکدام** است، اما hygiene هر فایلِ
تغییریافته را کاملاً lint می‌کند؛ و این دو فایل روی هم **۲۷ هشدارِ از قبل موجود**
دارند. یعنی یک تغییر یک‌خطی، یک پاک‌سازی ۲۷موردی در قلب مسیر چت را وارد کامیتی
می‌کرد که موضوعش «اجرای تست‌های node» بود.

**تصمیم مالک (۲۰۲۶-۰۹-۰۷): دامنه تنگ نگه داشته شود.** مسیر قدیمی در
`browser/episodeSummarizer.ts` به یک خط `export * from '../common/episodeSummarizer.js'`
تبدیل شد تا آن دو فایل اصلاً وارد دیف نشوند، و بدهی‌شان اینجا ثبت شود — **جدا شود،
نه پنهان**.

## فایل سوم — `voidAutoUpdaterService.ts` (افزوده ۲۰۲۶-۰۹-۰۷)

گاردِ «آپدیت نباید نسخه را عقب ببرد» در این فایل نوشته شد و **کامپایل سبز است**، ولی
به همان دلیل قابل کامیت نیست: ۱۵ هشدار از قبل موجود.

| نوع | نمونه | ارزیابی |
|---|---|---|
| `code-import-patterns` (۳) | `import https from 'https'` باید type-only باشد | **نیازمند بازطراحی** — کد واقعاً در ران‌تایم از https استفاده می‌کند؛ درستش این است که fetch از یک سرویس پلتفرم برود |
| `no-explicit-any` + `code-no-any-casts` (~۱۲) | `(this._product as any).updateUrl` | متوسط — `IProductService` این کلیدها را اعلام نکرده |

دومی نکته‌ی جالبی دارد: `updateUrl` و `quality` با `as any` خوانده می‌شوند چون در تایپ
محصول نیستند. همان خانواده‌ی مشکلی که امروز دو بار دیدیم (کلید product که کد بدون گارد
می‌خواند). اگر `IProductService` این‌ها را اعلام کند، هم `any` می‌رود هم کلیدهای جاافتاده
زودتر لو می‌روند.

## آنچه باقی مانده

### الف) ۲۷ هشدار در دو فایل

بعد از `eslint --fix` و فرمت (که ۱۲۱ مورد سمی‌کالن/curly را خودکار بست)، این‌ها ماندند:

| نوع | نمونه | ارزیابی |
|---|---|---|
| `code-no-in-operator` (۶) | `'parts' in msg`, `'text' in p`, `'content' in msg` | **امن و مکانیکی** — ریپو هلپر `hasKey` در `base/common/types.ts` دارد که narrowing را با type predicate حفظ می‌کند؛ کامپایلر درستی‌اش را اثبات می‌کند |
| `catch (e: any)` (۲) | `agentExecutor.ts:252,262` | **امن** — همان الگوی `_errMessage` که در `firmwarePart.ts` استفاده شد |
| `no-explicit-any` + `code-no-any-casts` (~۱۸) | `callTool[toolName](toolParams as any)`، `stringOfResult[toolName](… as any, … as any)`، `(this as any)[_ossRetryKey]` | **نیازمند بازطراحی** — این‌ها dispatch دینامیک روی یک مپ ناهمگن از ابزارهاست؛ تایپ درستش یعنی بازطراحی لایه‌ی tool-call |
| `code-no-dangerous-type-assertions` (۱) | `agentExecutor.ts:496` | متوسط |

### ب) حذف shim

بعد از به‌روزکردن ایمپورت آن دو فایل، `browser/episodeSummarizer.ts` باید **حذف** شود.
کامنت داخل خودش هم همین را می‌گوید.

## طرح پیشنهادی

1. **گام امن (S):** فقط `hasKey` و `catch` ها را بزن — با کامپایل و `test-node`
   راستی‌آزمایی کن. این حدود ۸ هشدار از ۲۷ را می‌بندد بدون هیچ ریسک رفتاری.
2. **گام سنگین (M):** تایپ‌کردن dispatch ابزار. این را جدا و با تست انجام بده؛
   `chatThreadService` مسیر اصلی چت و Ledger است.
3. **پاکسازی:** ایمپورت‌ها به `common/` برود، shim حذف شود، و این تسک بسته شود.

## معیارهای پذیرش

- [ ] `npx eslint <هر دو فایل>` صفر مشکل بدهد
- [ ] `browser/episodeSummarizer.ts` دیگر وجود نداشته باشد
- [ ] `npm run compile` و `npm run test-node` هر دو سبز بمانند (۱۱٬۹۱۳ تست پایه)
- [ ] هیچ `eslint-disable` جدیدی در این دو فایل اضافه نشده باشد

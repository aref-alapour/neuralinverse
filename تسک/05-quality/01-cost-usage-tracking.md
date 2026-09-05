# Q1 — ردیابی هزینه و داشبورد مصرف (Usage)

- **اولویت:** P0 | **برآورد:** S/M | **وضعیت:** 🔴 (هاردکد `$0.0000`) | **وابستگی:** —
- **هم‌ارز در Cursor:** پنل Usage — مصرف به ازای روز/ویژگی/مدل

## هدف
هزینه‌ی واقعی: جدول قیمت در `modelCapabilities.ts` هست، usage توکن از provider برمی‌گردد،
`budgetTracker` برای workflow هست — فقط وصل نشده‌اند. بعد از این تسک: هزینه‌ی per-thread،
per-run، per-day و داشبورد در agentManagerPart.

## وضعیت فعلی در کد
- `chatThreadService.ts:305` — `getSessionCost()` هاردکد `$0.0000`
- `modelCapabilities.ts` — قیمت‌های per-model (با چند `TODO!!! double check`)
- `sendLLMMessage` — usage (prompt/completion tokens) از provider می‌آید (فیلدها
  بسته به provider متفاوت — نرمال‌سازی لازم)
- `executor/budgetTracker.ts` — بودجه‌ی توکن/cost برای run های workflow (توکن دارد،
  پول نهایی ندارد)

## طرح پیاده‌سازی
1. **نرمالایزر usage:** در مسیر `onFinalMessage`، استخراج
   `{promptTokens, completionTokens, cacheReadTokens?, reasoningTokens?}` از هر
   provider به یک شکل واحد (map برای anthropic/openai/gemini/…)
2. **حسابدار:** سرویس `usageTrackingService` — رکورد به ازای هر LLM call:
   `{feature (Chat/CtrlK/Apply/…), threadId|runId, model, tokens, costUSD, ts}`
   — ذخیره در IStorageService (جدول ماهانه، aggregate روزانه)
3. **نمایش:**
   - هزینه‌ی thread در هدر sidebar (کنار gauge از C2)
   - هزینه‌ی run در run history (workflow) + جمع budgetTracker
   - تب «Usage» در agentManagerPart: نمودار ۳۰ روزه، تفکیک per-feature و per-model،
     export CSV
4. **پاکسازی داده‌های قیمت:** مرور TODO های قیمت در modelCapabilities (جدا به‌صورت
   PR کوچک upstream-able)
5. مدل‌های رایگان (niFreeModels) → هزینه ۰ با برچسب «free»

## معیارهای پذیرش
- [ ] یک گفتگوی واقعی: هزینه‌ی محاسبه‌شده با قیمت provider سازگار است (چک دستی)
- [ ] داشبورد Usage جمعش با مجموع رکوردها برابر است
- [ ] export CSV کار می‌کند
- [ ] مدل بدون قیمت شناخته‌شده → «~» به‌جای عدد غلط

# F2 — فشرده‌سازی مکانیکی Context با تریگر cache-aware

- **اولویت:** P0 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** مکمل C7 (نه جایگزین آن)
- **منبع الگو:** freebuff — `packages/agent-runtime/src/compact-history.ts` (۹۹۲ خط، راستی‌آزمایی‌شده)

## چیزی که freebuff متفاوت انجام می‌دهد
compaction ما (`conversationCompactor.ts` از کامیت `ee5e39f`) **LLM-based** است:
کیفیت خلاصه بالا ولی هزینه‌ی یک LLM call اضافه + مسیر خطای provider.
freebuff **مکانیکی و deterministic** است — بدون هیچ LLM call:
- بودجه‌های جداگانه بر اساس نقش: پیام‌های **user: 50k** توکن، **assistant+tool: 20k**
  (L60/L63: `DEFAULT_ASSISTANT_TOOL_BUDGET=20_000`, `DEFAULT_USER_BUDGET=50_000`) —
  سیلِ نتیجه‌ی ابزارها هرگز دستورهای کاربر را بیرون نمی‌اندازد
- خلاصه‌ی یک‌خطی به ازای هر tool call: `summarizeToolCall` (L134)،
  `summarizeToolResult` (L505 — نتایج حذف، فقط خطاها و پیام‌های ویرایش می‌مانند)
- truncation با ۸۰٪ head / ۲۰٪ tail (`truncateLongText` L96)
- پیام continuation (`CONTINUATION_TEXT` L72) تا مدل وسط-turn تمیز ادامه دهد
- انتخاب بودجه newest-first با force-include آخرین ورودی (`selectEntriesWithinBudget` L637)

**تریگر دوم (نکته‌ی طلایی):** غیر از حد context، تریگر «کشِ منقضی»:
`compaction-policy.ts` (خودم خط‌به‌خط چک کردم): اگر فاصله‌ی زمانی بین ارسال‌ها از
`cacheExpiryMs` بیشتر بود **و** تاریخچه بالای `cacheExpiryMinTokens` بود → فشرده‌سازی
«مجانی» است چون درخواست بعدی به‌هرحال کل تاریخچه را با قیمت کامل می‌خواند.
پیش‌فرض: ۶۰ دقیقه / ۱۴۰k توکن (استدلالش در کامنت‌های فایل: زیر یک سقف، budget walk
هیچ چیزی حذف نمی‌کند). ما همین heuristic زمانی را می‌توانیم بزنیم — به API کش
provider نیازی نیست.

**اصلاح نسبت به گزارش handoff:** پیام placeholder برای ورودی‌های حذف‌شده وجود ندارد
(drop بی‌صدا)؛ فقط دو policy تعریف شده (پیش‌فرض + DeepSeek Flash 15min/40k)، نه جدول
per-model کامل.

## طرح پیاده‌سازی (استراتژی دولایه)
1. **لایه ۱ — مکانیکی (همیشه، قبل از هر ارسال):** پورت `compact-history.ts` به
   `context/compaction/mechanicalCompactor.ts` (منطق، بدون وابستگی — نه Zod نه Bun):
   - بودجه نقش‌محور + خلاصه‌های یک‌خطی ابزار + 80/20
   - پارامترها در `common/compactionPolicy.ts` ما؛ `sentAt` روی پیام‌های تاریخچه
     اضافه شود (برای تریگر کش)
2. **لایه ۲ — LLM (موجود):** `conversationCompactor.ts` فعلی فقط وقتی بعد از لایه ۱
   هنوز بالای ۷۲٪ هست، یا برای thread های long-lived که خلاصه‌ی غنی می‌ارزد (حالت
   «rich» قابل تنظیم). یعنی: ارزان و قطعی اول، غنی و پرهزینه بعد
3. ادغام با C7: `/compact` دستی = هر دو لایه؛ خودکار = لایه ۱ همیشه + لایه ۲ شرطی
4. گزینه‌ی per-model policy (الگوی `compactionPolicyForModel`): مدل‌های ارزان/سریع →
   سیاست تهاجمی‌تر؛ در `modelCapabilities.ts` فیلد اضافه شود
5. متریک: توکن صرفه‌جویی‌شده به ازای هر فشرده‌سازی (در gauge از C2 نمایش)

## معیارهای پذیرش
- [ ] thread پر از نتیجه‌ی ابزار (مثلاً ۸۰k) بدون LLM call به ~۲۵k می‌رسد و پیام‌های
      user دست‌نخورده می‌مانند
- [ ] با قطع provider شبکه، فشرده‌سازی مکانیکی همچنان کار می‌کند (deterministic)
- [ ] تریگر کش: وقتی ۶۰+ دقیقه فاصله افتاده و تاریخچه بالای کف است، قبل از ارسال
      بعدی فشرده می‌شود
- [ ] حالت rich (LLM) فقط تحت شرط اجرا می‌شود (شمارنده‌ی call ها در run history)
- [ ] مدل وسط-turn بعد از continuation پیام، مسیر کار را گم نمی‌کند (تست دستی)
- [ ] attribution در هدر فایل پورت‌شده + ThirdPartyNotices

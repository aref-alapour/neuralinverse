# C2 — نمایشگر مصرف Context (Context Gauge)

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🟡 اجرای موج ۳ (۰۹-۰۸): gauge سایدبار ساخته و بیلد شد؛ پورت live-patch و تست owner باز | **وابستگی:** —
- **هم‌ارز در Cursor:** نوار «Context: 34k / 200k» + دیدن اینکه دقیقاً چه چیزهایی داخل است

> **اجرای موج ۳ (۲۰۲۶-۰۹-۰۸):**
>
> - کامپوننت جدید `react/src/sidebar-tsx/ContextGauge.tsx` — عدد
>   `Context: 34.2k / 200k` با رنگ آستانه (سبز < ۶۰٪ / زرد ۶۰-۷۲٪ / قرمز > ۷۲٪
>   + ⚠) و کلیک → پاپ‌آور breakdown (system/brief/pinned/recalled/notice/tail با
>   نوار نسبت، availableInput، reserved-output، هشدار cache-unstable).
> - سوار در **هدر سایدبار** (`Sidebar.tsx`) — طبق همین تسک («در هدر sidebar chat»)؛
>   سایدبارچت و سرویس‌ها دست **نخوردند**: گزارش از `getLedgerUsageReport` موجود
>   در زمان render خوانده می‌شود و re-render های مکرر thread-state تازگی را
>   می‌دهند (هر پیام/tick استریم). هیچ event یا state جدیدی لازم نشد.
> - **چرا بدون تغییر سرویس:** سه فایل مسیر طبیعی (chatThreadService ۹۴۶ هشدار،
>   SidebarChat.tsx ۱۵۲۲، services.tsx ۲۸۱) بدهی لینت سنگین دارند که پرداختش
>   تسک Q11/مالک است؛ مسیر بدون‌بدهی همان رفتار را با هزینه‌ی صفر می‌دهد.
>   باندل‌های `react/out/` طبق سابقه همراه سورس بازسازی و کامیت شدند.
> - ویجت بومی چت (chatContextUsageWidget) از کامیت 4c1e1c16b56 توسط پل تغذیه
>   می‌شود — آنجا کاری نمانده و دست نخورد.
> - عدد روی desktop از usage واقعی (Q12) می‌آید؛ روی وب صفر دیدی، باگ نیست.

## وضعیت راستی‌آزمایی‌شده (۲۰۲۶-۰۹-۰۷)

**مارکر قبلی 🔴 کهنه بود** — گام ۱ طرح (ساخت `ContextUsageReport`) در جریان کار
M5 عملاً انجام شده است.

**انجام‌شده:**
- `IContextUsageReport` تعریف شده: `void/common/ledgerTypes.ts:148`
- assembler گزارش را با بخش‌های `brief/pinned/recalled/notice/tail` تولید می‌کند:
  `void/common/contextAssembler.ts:193` (و `:183` برای بخش‌ها)
- `chatThreadService` آن را per-thread نگه می‌دارد و expose می‌کند:
  `:244` (map)، `:372` (نوشتن)، `:469` `getLedgerUsageReport()` — که کامنت خودش
  می‌گوید «consumed by the context gauge (C2)»

## هدف
در هدر sidebar chat نمایش: `Context: 34.2k / 200k` با کلیک → breakdown کامل اینکه
هر توکن کجا رفته (system prompt / rules / memories / repo map / فایل‌های سنجاق‌شده /
بسته‌ی context / تاریخچه / رزرو خروجی). هشدار زرد/قرمز قبل از compaction.

## چرا مهم است
کاربر حرفه‌ای باید بداند مدل «چه چیزی را می‌بیند». Cursor این شفافیت را با gauge و
پنل context داده؛ ما موتورش را داریم (compaction + trimming در `prepareOpenAIOrAnthropicMessages`)
ولی عددش را به UI نمی‌دهیم. این تسک ارزان‌ترین «حس حرفه‌ای» را می‌سازد.

## وضعیت فعلی در کد
- `convertToLLMMessageService.ts` پیام‌ها را می‌سازد و `prepareOpenAIOrAnthropicMessages`
  آن‌ها را برای جا شدن در پنجره trim می‌کند — ولی اعداد بعد از trim گم می‌شوند
- آستانه‌ی compaction: ۷۲٪ پنجره‌ی موجود (`conversationCompactor.ts`)
- `modelCapabilities.ts` برای هر مدل `contextWindow` و `reservedOutputTokenSpace` دارد

## طرح پیاده‌سازی
1. ~~در مسیر pre-send، یک `ContextUsageReport` بساز~~ (M5 انجام داد)
2. کامپوننت React کوچک در هدر سایدبار: عدد جاری/پنجره + رنگ (سبز < 60٪ /
   زرد 60-72٪ / قرمز > 72٪ که یعنی compaction قریب‌الوقوع) — **انجام شد**
3. کلیک روی gauge → پاپ‌آور breakdown — **انجام شد** (بدون jump-لینک‌ها؛ نسخه بعدی)
4. بعد از هر compaction خودکار: پیام سیستمی کوچک «تاریخچه فشرده شد (ـXk توکن صرفه‌جویی)» — باز (C7 هم‌پوشان)
5. گزارش در executor run ها هم ذخیره شود (ستون context در run history) — باز

## معیارهای پذیرش
- [ ] عدد gauge با محاسبه‌ی دستی (chars/4) هم‌خوان است — **تست owner**
- [x] breakdown جمعش با total برابر است (reserved-output اطلاعاتی و جداست — مطابق قرارداد M6)
- [ ] در ۷۲٪ هشدار compaction دیده می‌شود (رنگ قرمز + ⚠ آماده؛ رفتار پس از compaction — تست owner)
- [x] برای مدل‌های با پنجره‌ی کوچک هم درست کار می‌کند (مخرج از گزارشِ همان مدل می‌آید؛ تعویض مدل → ارسال بعدی → مخرج جدید)
- [x] ledger خاموش/ترد تازه → gauge نمایش داده نمی‌شود («نامشخص»، نه صفر)

## مانده برای owner (بعد از پورت live-patch)
- تست زنده روی نسخه‌ی نصبی: چند نوبت چت → عدد بالا می‌رود؛ کلیک → breakdown؛
  تعویض مدل با پنجره‌ی کوچک‌تر → مخرج عوض می‌شود.
- برای دیدن عدد روی دسکتاپ، usage واقعی Q12 لازم است (از 213acb14709).`

## هدف
در هدر sidebar chat نمایش: `Context: 34.2k / 200k` با کلیک → breakdown کامل اینکه
هر توکن کجا رفته (system prompt / rules / memories / repo map / فایل‌های سنجاق‌شده /
بسته‌ی context / تاریخچه / رزرو خروجی). هشدار زرد/قرمز قبل از compaction.

## چرا مهم است
کاربر حرفه‌ای باید بداند مدل «چه چیزی را می‌بیند». Cursor این شفافیت را با gauge و
پنل context داده؛ ما موتورش را داریم (compaction + trimming در `prepareOpenAIOrAnthropicMessages`)
ولی عددش را به UI نمی‌دهیم. این تسک ارزان‌ترین «حس حرفه‌ای» را می‌سازد.

## وضعیت فعلی در کد
- `convertToLLMMessageService.ts` پیام‌ها را می‌سازد و `prepareOpenAIOrAnthropicMessages`
  آن‌ها را برای جا شدن در پنجره trim می‌کند — ولی اعداد بعد از trim گم می‌شوند
- آستانه‌ی compaction: ۷۲٪ پنجره‌ی موجود (`conversationCompactor.ts`)
- `modelCapabilities.ts` برای هر مدل `contextWindow` و `reservedOutputTokenSpace` دارد

## طرح پیاده‌سازی
1. در مسیر pre-send، یک `ContextUsageReport` بساز و در کنار request نگه دار:
   `{ total, window, breakdown: { system, rules, memories, repoMap, pinned, contextPack, history, reservedOutput } }`
   (توکن‌ها با همان تقریب chars/4 + 8 که compactor استفاده می‌کند — سازگاری کامل)
2. کامپوننت React کوچک در هدر `SidebarChat.tsx`: عدد جاری/پنجره + رنگ (سبز < 60٪ /
   زرد 60-72٪ / قرمز > 72٪ که یعنی compaction قریب‌الوقوع)
3. کلیک روی gauge → پاپ‌آور breakdown با قابلیت jump (مثلاً «History 12k → مدیریت thread»)
4. بعد از هر compaction خودکار: پیام سیستمی کوچک «تاریخچه فشرده شد (ـXk توکن صرفه‌جویی)»
5. گزارش در executor run ها هم ذخیره شود (ستون context در run history)

## معیارهای پذیرش
- [ ] عدد gauge با محاسبه‌ی دستی (chars/4) هم‌خوان است
- [ ] breakdown جمعش با total برابر است (rounded)
- [ ] در ۷۲٪ هشدار compaction دیده می‌شود و بعد از compaction عدد می‌افتد
- [ ] برای مدل‌های با پنجره‌ی کوچک (مثلاً 8k لوکال) هم درست کار می‌کند

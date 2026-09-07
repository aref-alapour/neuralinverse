# C2 — نمایشگر مصرف Context (Context Gauge)

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🟡 بک‌اند کامل، صفر UI | **وابستگی:** —
- **هم‌ارز در Cursor:** نوار «Context: 34k / 200k» + دیدن اینکه دقیقاً چه چیزهایی داخل است

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

**باقی‌مانده — تمام کار UI است:**
- [ ] `getLedgerUsageReport()` **صفر مصرف‌کننده** دارد (`grep` بیرون از
      `chatThreadService.ts` هیچ نتیجه‌ای ندارد) → هیچ gauge ای در UI نیست
- [ ] پاپ‌آور breakdown، رنگ آستانه، پیام بعد از compaction

**دو قید که قبل از شروع باید دید:**
1. گزارش فقط در **مسیر ledger** تولید می‌شود (`_assembleLedgerThread`). در مسیر
   legacy compactor هیچ گزارشی ساخته نمی‌شود — یا باید آنجا هم تولید شود یا gauge
   وقتی ledger خاموش است باید حالت «نامشخص» داشته باشد.
2. `contextLedgerEnabled` پیش‌فرض `true` است (`voidSettingsTypes.ts:548`)، پس در
   حالت عادی مسیر ledger فعال است.

**دستور بازتولید:**
```bash
grep -rn "getLedgerUsageReport" src/ | grep -v chatThreadService.ts   # → خالی
```

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

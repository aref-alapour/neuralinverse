# C2 — نمایشگر مصرف Context (Context Gauge)

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🔴 | **وابستگی:** —
- **هم‌ارز در Cursor:** نوار «Context: 34k / 200k» + دیدن اینکه دقیقاً چه چیزهایی داخل است

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

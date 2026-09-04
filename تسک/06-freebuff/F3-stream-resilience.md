# F3 — مقاوم‌سازی جریان: بازیابی قطع stream + بهداشت پیام + شمارش توکن محلی

- **اولویت:** P0 (بخش الف/ب) / P1 (بخش ج) | **برآورد:** M | **وضعیت:** 🟡 بخشی هست | **وابستگی:** —
- **منبع الگو:** freebuff — `packages/agent-runtime/src/tools/stream-parser.ts` + `common/src/util/messages.ts` + `util/token-counter.ts` (راستی‌آزمایی‌شده)

## الف) بازیابی قطعِ stream — «قدم بعدی، خود retry است»

**منبع:** `stream-parser.ts`:
- تگ‌های `STREAM_INTERRUPTED_TAG` / `OUTPUT_LIMIT_TAG` (L47-48): بعد از قطع اتصال یا
  رسیدن به حد خروجی، یک پیام **تگ‌دار** system/user به تاریخچه اضافه می‌شود که وقفه را
  توصیف می‌کند و step بعدی اجباری می‌شود — مدل خروجی ناتمام خودش را می‌بیند و ادامه می‌دهد
- سقف تلاش: `MAX_CONSECUTIVE_STREAM_RECOVERIES = 3` (L55)؛ شمارش با پایه‌روی دنباله‌ی
  تاریخچه (`trailingStreamRecoveryStreak` L106-122): پیام tool و STEP_PROMPT رشته را
  نمی‌شکنند، هر پیام واقعی user می‌شکند — بعد از ۳ تکرار متوالی، fail بلند

**وضعیت ما:** watchdog ها و retry های خطای گذرا (429/5xx) از کامیت `ee5e39f` را داریم؛
ولی «ادامه‌ی خروجی ناتمام با پیام تگ‌دار» و سقف streak را نداریم. این بخش upgrade
مسیر `executor/retryPolicy.ts` + `onError` در sendLLMMessage است.

## ب) بهداشت پیام در یک نقطه (chokepoint)

**منبع:** `common/src/util/messages.ts` — `convertCbToModelMessages` (L338) قبل از هر
درخواست:
1. `dropUnansweredToolCalls` (L505) — فراخوانی ابزار بی‌جواب = خطای 400 provider های
   سخت‌گیر؛ قبل از request بعدی حذف می‌شوند (این دقیقاً باگ کلاسیکی است که بعد از
   هر abort/interrupt ما را می‌تواند بگیرد)
2. خنثی‌سازی lone surrogate های UTF-16 → U+FFFD (L294) — یک ایموجی نصف‌شده در
   تاریخچه، همه‌ی درخواست‌های بعدی را مسموم می‌کند
3. جابه‌جایی تصاویر داخل tool result به پیام user با حفظ مجاورت call/result

**پیاده‌سازی:** تابع واحد `sanitizeMessagesForProvider(messages)` در مسیر
`prepareOpenAIOrAnthropicMessages` ما (الان trim می‌کند ولی این سه بهداشت را ندارد)؛
فراخوانی هم در chat و هم executor قبل از هر ارسال.

## ج) شمارش توکن محلی + cache breakpoints

**منبع:** `token-counter.ts` (107 خط): tokenizer گپت-4o محلی + ضریب ۱.۳۵ برای
مدل‌های غیر-OpenAI، تصویر = ثابت ۱۶۰۰، `LRUCache(1000)`، سربار ۸ توکن per-message.
آن‌ها round-trip به `count_tokens` provider را حذف کردند («ثانیه‌ها delay سریالی به
هر step اضافه می‌کرد») — درس مهم برای BYOLLM ما.
`common/src/util/tokens.ts`: `totalTokens` شامل cache-read (ضد دو-bar شمردن)،
`freshInputTokens` با تفریق clamp شده.
**Breakpoint های کش Anthropic** (حداکثر ۴): `cache_control: {type:'ephemeral'}` روی
مرزهای تگ‌شده (LAST_ASSISTANT_MESSAGE / USER_PROMPT / STEP_PROMPT + آخرین پیام) —
در `messages.ts` L41-91 و L400-470. برای کاربران Anthropic/OpenRouter ما یعنی
کاهش هزینه‌ی محسوس prefill.

**پیاده‌سازی:** ماژیل token-count محلی برای budgetTracker و gauge (C2) — جایگزین
تقریب chars/4 در نقاط حساس (هم‌چنین تریگرهای F2 دقیق‌تر می‌شوند)؛ breakpoints در
`sendLLMMessage.impl.ts` فقط برای provider های anthropic/openrouter/openaiCompatible.

## معیارهای پذیرش
- [ ] کشیدن stream وسط پاسخ → پیام تگ‌دار ادامه می‌سازد و خروجی ناتمام کامل می‌شود
- [ ] ۳ قطع متوالی → fail صریح با پیام روشن (نه حلقه‌ی بی‌نهایت)
- [ ] abort وسط tool call → request بعدی بدون خطای 400 پاسخ می‌گیرد (dropUnanswered)
- [ ] رشته‌ی شامل ایموجی نصف‌شده در تاریخچه → درخواست بعدی سالم است
- [ ] اختلاف شمارش توکن محلی با گزارش provider < ۱۰٪ روی سه مدل مختلف
- [ ] با مدل Anthropic، cache_read_input_tokens در پاسخ‌ها دیده می‌شود (breakpoint ها کار می‌کنند)

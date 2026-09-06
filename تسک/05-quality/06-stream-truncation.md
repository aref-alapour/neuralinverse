# Q6 — مرگ بی‌صدای agent وسط کار سنگین (stream truncation)

- **اولویت:** P0 | **تاریخ:** 2026-09-06 | **وضعیت:** ✅ رفع شد، منتظر build مالک
- **علامت گزارش‌شده:** «وسط کار سنگین کلا می‌میره؛ برای کار سنگین قطع میشه وسط
  چند بار و هیچی دیگه نمی‌گه» — مدل OSS از طریق endpoint لوکال (omni.local)

## ریشه‌یابی

سه لایه روی هم می‌افتاد:

1. **برنده‌ی اصلی — stream قطع‌شده = پاسخ کامل.** در `_sendOpenAICompatibleChat`
   (نسخه‌ی electron-main که دسکتاپ از آن استفاده می‌کند)، وقتی سرور/proxy وسط
   پاسخ connection را می‌بندد بدون `[DONE]`، iterator بدون throw تمام می‌شود و
   متن ناقص به‌عنوان `onFinalMessage` «کامل» بالا می‌رفت. اگر وسط tool call
   بود، JSON ناقص در `rawToolCallObjOfParamsStr` به null می‌شد و با
   `filter(Boolean)` **بی‌صدا حذف** می‌شد → صفر tool call → حلقه‌ی agent تمایل
   داشت «تمام‌شده» تلقی شود. نه خطا، نه retry، نه پیام. (نسخه‌ی web در
   `common/llmMessage/sendLLMMessage.impl.ts` این گارد را از قبل داشت —
   `gotFinishReason` — ولی الگو به electron-main برنگشته بود؛ دسکتاپ جاموند.)
2. **خطاهای connection اصلاً retry نمی‌شدند.** `isRetryableLlmError` عبارت‌های
   `Connection error.` (پیام `APIConnectionError` در SDK)، `Failed to fetch`،
   `terminated` (undici)، `EPIPE` و مثل آن را نمی‌گرفت → اولین لغزش شبکه کل
   run را می‌کشت با اینکه چت‌لاپ CHAT_RETRIES=3 دارد.
3. **Executor کارهای سنگین هیچ retryای برای خطای transient نداشت.** حلقه‌ی
   `agentExecutor` فقط برای پاسخِ خالی retry می‌کرد؛ هر `onError` دیگری = شکست
   step.

## رفع (همه اعمال شد)

| فایل | تغییر |
|---|---|
| `common/streamIntegrity.ts` (جدید) | تعریف واحد `isContextOverflowError`، `isRetryableLlmError` (گسترش‌یافته با عبارت‌های connection)، `streamEndedPrematurely`، `truncatedStreamMessage` — بدون هیچ وابستگی، قابل‌تست standalone |
| `browser/conversationCompactor.ts` | کلاسیفایرها به streamIntegrity منتقل و re-export شد (مسیر import موجود دست‌نخورده) |
| `electron-main/llmMessage/sendLLMMessage.impl.ts` | گارد truncation در openAI-compatible (هم‌ساختار نسخه‌ی web: ۲ retry داخلی با backoff، بعد `onError` با پیام retryable) + همین گارد در Gemini native با `finishReason` |
| `neuralInverse/.../agentExecutor.ts` | خطاهای transient (`isRetryableLlmError`) در حلقه‌ی LLM با ۲ retry و تأخیر ۲.۵s؛ بقیه مثل قبل fail-fast |
| `tools/typecheck-slice.json` | streamIntegrity و تستش به slice اضافه شد |

پیام truncation عمداً عبارت `dropped mid-response` را دارد تا در چت‌لاپ و
executor به‌عنوان transient دسته‌بندی و retry شود.

## راستی‌آزمایی

```bash
node tools/run-tests-standalone.mjs   # انتظار: 96 passed, 0 failed (۱۲ تست جدید streamIntegrity)
node tools/typecheck-slice.mjs        # انتظار: 0 error(s)
```

تست‌های جدید (`test/node/streamIntegrity.test.ts`) به‌طور خاص می‌سنجند:
پیام truncation retryable است؛ `Connection error.` / `Failed to fetch` /
`terminated` / `EPIPE` retryable شده‌اند؛ 401/کلید نامعتبر/overflow همچنان
fail-fast می‌مانند؛ stream بدون محتوا وارد مسیر empty-response قدیمی می‌شود نه
گارد truncation.

## آنچه عمداً بی‌تغییر ماند

- **stall watchdog سه‌دقیقه‌ای** (chat و executor): وقت prompt-processing
  سنگین روی مدل لوکال ممکن است بی‌چانک از ۳ دقیقه بگذرد — این خطا پیام واضح
  دارد ولی run می‌میرد؛ اگر بعد از این رفع هم علامت داشت، timeout دو مرحله‌ای
  (time-to-first-token بلندتر) کار بعدی است.
- **backoff خیلی کوتاه empty-retry** (۸۰۰ms×n): برای سروری که crash کرده و
  مدل را از نو لود می‌کند کم است؛ تغییرش رفتار همه‌ی provider ها را تکان
  می‌دهد، جداگانه بررسی شود.
- **Bedrock native و Anthropic native:** SDK شان قطع connection را به‌صورت
  error گزارش می‌دهد (Anthropic از طریق رخداد error، نه finalMessage) — نیازی
  به گارد ندارند.
- نسخه‌ی web از قبل گارد داشت و دست نخورد.

## استقرار روی برنامه‌ی نصب‌شده (live-patch)

برنامه از جلسه‌ی قبل گارد truncation مربوط به main-process را از قبل دارد
(task 3 در `live-patch.py`). دلتای این جلسه چهار پچ جدید در `tools/live-patch.py`
است:

1. `chat: retryable regex covers connection failures` — ارتقای regex داخل
   ماژول تزریقی `__niC` (ماژول خودش عمداً دست‌نخورده ماند تا پچ، حامل ارتقا
   باشد و apply/verify برای نصب تازه و موجود یکسان بماند)
2. `executor: transient LLM errors retry instead of failing the step` —
   زنجیره روی خروجی پچ empty-retry دیروز (v1→v2)
3. و 4. گارد `finishReason` برای Gemini native در main.js (هم‌ارز source)

برای زنجیره‌ی v1→v2 (که متنِ خروجی پچ قبلی را جایگزین می‌کند و پچ قبلی را
برای همیشه MISSING می‌کرد) ابزار توسعه یافت: نگاشت `SUPERSEDES` — حضور
`new` جانشین، پچ قدیمی را در apply/verify به‌عنوان «superseded/already»
سبز می‌کند. selftest هم برای عمق زنجیره‌ی جدید (۳ پچ prerequisite-دار روی
pristine) به‌روز شد.

### راستی‌آزمایی (همه سبز)

```bash
python tools/live-patch-selftest.py   # all scenarios passed (شامل parse گیت node --check هر دو bundle)
node tools/run-tests-standalone.mjs   # 96 passed, 0 failed
node tools/typecheck-slice.mjs        # 0 error(s)
```

سناریوی sandbox هم مستقلاً اجرا شد: pristine→apply(42 applied/0 missing)→
verify(43 OK)→ idempotent re-apply(0 applied, 42 already).

### قدم مانده (نیاز به admin — UAC کنسل شد)

```bash
# راست‌کلیک → Run as administrator:
C:\Users\jobal\dev\neuralinverse\tools\repatch-neuralinverse.bat
# بعدش (بدون admin، فقط خواندنی):
python tools/live-patch.py --verify   # انتظار: 43 OK, 0 PENDING, 0 MISSING
```

وضعیت فعلی برنامه‌ی نصب‌شده: `39 OK, 4 PENDING, 0 MISSING` — دست‌نخورده و
سالم؛ چهار پچ جدید منتظر همان apply ادمین هستند. بعد از apply برنامه را
ری‌استارت کن (پچ‌ها فقط موقع بوت لود می‌شوند).

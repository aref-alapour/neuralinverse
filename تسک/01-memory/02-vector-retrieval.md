# M2 — بازیابی برداری حافظه‌ی پایدار (Vector Memory Retrieval)

- **اولویت:** P0 | **برآورد:** M (باقی‌مانده: S) | **وضعیت:** ✅ تست owner سبز (۰۹-۰۹) — بازیابی معنایی روی مسیر تزریق تأیید شد | **وابستگی:** —
- **هم‌ارز در Cursor:** Memories که با معنای کار (نه فقط کلمات) بازیابی می‌شوند
> **تست owner سبز شد (۲۰۲۶-۰۹-۰۹، بیلد `9a520bdfa81`).** شواهد در
> [`00-OWNER-TESTS-ROUND-2.md`](00-OWNER-TESTS-ROUND-2.md) و ژورنال زنده‌ی
> `escapezoom-html/.inverse/ledger/`.

> **اجرای موج ۳ (۲۰۲۶-۰۹-۰۸):**
>
> ۱. **مسیر تزریق (بند ۱ طرح):** `neuralInverseAgentService.getContextSummaryAsync()`
>    جدید — بخش `<persistent_memory>` حالا از `recallForPrompt(query, 1500, 8)`
>    می‌آید (هیبرید + دلیل تطبیق per-line، سقف توکن حفظ شده). کوئری از هدف
>    task فعال + ۵ ورودی آخر working memory ساخته می‌شود. ناهمگامی «تمیز» حل
>    شد: `prepareLLMChatMessages` (مسیر چت سایدبار) و `_decomposeTaskAsync`
>    منتظر می‌مانند؛ FIM/simple مسیرها عمداً همگام ماندند (خلاصه‌ی درجه‌اهمیت،
>    بدون تأخیر). fallback: هر خطای recall یا نتیجه‌ی خالی → همان
>    `getContextSummary(1500)` قبلی؛ هرگز ارسال را نمی‌شکند.
> ۲. **Backfill (بند ۶ طرح):** `backfillEmbeddings(batchSize=20)` روی سرویس +
>    فراخوانی fire-and-forget در `agentMemoryEmbeddingContrib` با تأخیر idle
>    ۵ ثانیه — ورودی‌های قبل از فعال‌شدن provider دوباره embed می‌شوند.
> ۳. **Provider معتبر (بند ۳):** فهرست auto-select در `embeddingService` به
>    provider هایی محدود شد که واقعاً `/v1/embeddings` سازگار-OpenAI دارند
>    (openAI، mistral، githubModels، openRouter، openAICompatible، ollama، vLLM،
>    lmStudio، liteLLM؛ پیش‌فرض ollama → nomic-embed-text). قبلاً صرف وجود
>    config چت (مثلاً deepseek) `_available=true` می‌گذاشت و همه‌ی embed ها
>    بی‌صدا شکست می‌خوردند.
> ۴. **«چرا آمد» (بند ۵):** هر خط تزریق `(matched: vector:0.82, term:pnpm, …)`
>    دارد — همان خروجی reasons موتور.
>
> تست: فایل `agentMemoryHybrid.test.ts` برای اولین بار به رانر standalone
> آمد (۲۱ تست قبلی + ۴ تست جدید برای recallForPrompt/backfill). مجموع سوئیت:
> ۱۴۱. اصلاح E1 هم در همین موج: پل چت بومی rule ها را از
> `getWorkspaceRuleFiles()` جدید می‌گیرد (گپی که موقع M2 دیده شد —
> generateSystemMessage پیش‌تر aiInstructions نمی‌ساخت).

> **اصلاح مارکر ۲۰۲۶-۰۹-۰۸:** از 🔴 به 🟡. موتور hybrid کامل پیاده و تست شده است
> (`agentMemoryService.ts` — سه مود `hybrid`/`lexical-promoted`/`lexical`، وزن‌های
> ۰.۵ برداری + ۰.۲ واژگانی + ۰.۲ تازگی + ۰.۱ بسامد، سقف ۲۰۰۰، pin، دلیل تطبیق
> per-result، ۲۱ تست). **ولی ✅ نیست:** `recallWithReasons` صفر caller خارجی داشت؛
> مسیر تولیدی `getContextSummary(1500)` همگام و واژگانی را صدا می‌زد. (بند ۱ بالا
> این را بست.)
>
> ```bash
> grep -rn "recallWithReasons" src --include=*.ts | grep -v agentMemoryService.ts   # صفر
> grep -n "getContextSummary(1500)" src/vs/workbench/contrib/void/browser/neuralInverseAgentService.ts
> ```
>
> **کار باقی‌مانده تغییر کرد:** نوشتن موتور دوم لازم نیست. فقط (۱) جایگزینی
> `getContextSummary` با `recallWithReasons` در مسیر تزریق، (۲) backfill بردار برای
> ورودی‌های قدیمی، (۳) انتخاب معتبر provider، (۴) نمایش «چرا این حافظه آمد».

## هدف
جست‌وجوی حافظه‌ی پایدار (`agentMemoryService`) از term-match ساده به hybrid
(برداری + واژگانی + تازگی + بسامد) ارتقا یابد — با استفاده از `embeddingService`
و `persistentStore` ای که **از قبل در Context Engine وجود دارد**.

## چرا مهم است
حافظه‌ی پایدار فعلی «به‌خاطر بیا همیشه از pnpm استفاده کن» را وقتی کاربر می‌گوید
«پکیج منیجر رو عوض نکن» پیدا نمی‌کند (هیچ کلمه‌ی مشترکی ندارد). Cursor memories
معنایی بازیابی می‌شوند. تفاوت تجربه‌ی «حرفه‌ای بودن» دقیقاً همین‌جاست.

## وضعیت فعلی در کد
- `src/vs/workbench/contrib/void/browser/agentMemoryService.ts`:
  - ذخیره در `IStorageService` با کلید `ni.agent.memory`، حداکثر ۲۰۰ ورودی
  - انواع: pattern / preference / project-fact / error-fix / tool-usage / file-context
  - امتیازدهی: term-match (0.5) + تازگی (0.995 در روز، کف 0.25) + بسامد دسترسی (0.15) + پایه (0.1)
  - تزریق به system message به‌صورت `<persistent_memory>` از طریق `getContextSummary()`
- از قبل موجود و قابل استفاده: `neuralInverse/browser/search/embeddingService.ts`،
  `persistentStore.ts`، `bm25Index.ts` (در Context Engine)

## طرح پیاده‌سازی
1. موقع نوشتن حافظه: embed شدنِ `summary` ورودی با `embeddingService`؛ ذخیره‌ی بردار
   کنار ورودی در `persistentStore`
2. موقع بازیابی: embed کردن query (پیام‌های اخیر + فایل فعال) → top-30 با cosine →
   ادغام با امتیازهای موجود:
   `final = 0.5·cosine + 0.2·term + 0.2·recency + 0.1·frequency` (وزن‌ها قابل تنظیم در settings)
3. **fallback بدون embedding:** BYOLLM یعنی ممکن است هیچ provider برداری تنظیم نشده باشد
   (ollama بدون مدل embedding و…). در این حالت رفتار فعلی (term-match) حفظ شود و در
   UI یک preflight «حافظه‌ی معنایی غیرفعال» نشان داده شود — degrade تدریجی، هرگز خطا
4. افزایش سقف ۲۰۰ → ۲۰۰۰ ورودی + eviction بر اساس امتیاز fused (نه فقط relevance)
5. تزریق `<persistent_memory>`: top-k (پیش‌فرض ۸) داخل بودجه‌ی توکن (~۱۵۰۰)؛ برای
   دیباگ، هر آیتم علت ورود را داشته باشد (`matched-on: "pnpm, package manager"`)
6. ایندکس گذرا (backfill): اولین باری که embedding فعال شود، ورودی‌های قدیمی به‌صورت
   batch (هر بار ۲۰ تا، idle) embed شوند

## معیارهای پذیرش
- [ ] تست دستی: ۲۰ حافظه ذخیره → سؤال با wording متفاوت → حافظه‌ی درست تزریق می‌شود — **تست owner**
- [x] بدون provider برداری: رفتار فعلی حفظ می‌شود، هیچ خطایی در کنسول نیست (تست standalone + fallback در کد)
- [ ] زمان بازیابی < 50ms برای ۱۰۰۰ ورودی (بدون شبکه — بردارها local کش شده) — **تست owner**
- [x] امتیاز «چرا وارد شد» قابل نمایش است — هر خط تزریق `(matched: …)` دارد (پنل دیباگ جدا فاز بعد)

## مانده برای owner (بعد از پورت live-patch)
- تست زنده با provider برداری واقعی (openai یا ollama/nomic-embed-text): ذخیره‌ی
  چند حافظه → پرسش با واژگان متفاوت → خط `(matched: vector:…)` در
  `<persistent_memory>` دیده شود؛ backfill ورودی‌های قدیمی را بعد از ~۵ ثانیه
  برداری کند.
- preflight UI «حافظه‌ی معنایی غیرفعال» (بند ۳ طرح) — هنوز ساخته نشده.

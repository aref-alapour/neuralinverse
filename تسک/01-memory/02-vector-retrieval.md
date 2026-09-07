# M2 — بازیابی برداری حافظه‌ی پایدار (Vector Memory Retrieval)

- **اولویت:** P0 | **برآورد:** M (باقی‌مانده: S) | **وضعیت:** 🟡 موتور کامل، روی مسیر تزریق نیست | **وابستگی:** —
- **هم‌ارز در Cursor:** Memories که با معنای کار (نه فقط کلمات) بازیابی می‌شوند

> **اصلاح مارکر ۲۰۲۶-۰۹-۰۸:** از 🔴 به 🟡. موتور hybrid کامل پیاده و تست شده است
> (`agentMemoryService.ts` — سه مود `hybrid`/`lexical-promoted`/`lexical`، وزن‌های
> ۰.۵ برداری + ۰.۲ واژگانی + ۰.۲ تازگی + ۰.۱ بسامد، سقف ۲۰۰۰، pin، دلیل تطبیق
> per-result، ۲۱ تست). **ولی ✅ نیست:** `recallWithReasons` صفر caller خارجی دارد؛
> مسیر تولیدی هنوز `getContextSummary(1500)` همگام و واژگانی را صدا می‌زند.
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
- [ ] تست دستی: ۲۰ حافظه ذخیره → سؤال با wording متفاوت → حافظه‌ی درست تزریق می‌شود
- [ ] بدون provider برداری: رفتار فعلی حفظ می‌شود، هیچ خطایی در کنسول نیست
- [ ] زمان بازیابی < 50ms برای ۱۰۰۰ ورودی (بدون شبکه — بردارها local کش شده)
- [ ] emtiaz «چرا وارد شد» در دمو قابل نمایش است (پنل دیباگ context)

# C6 — انتخاب خودکار Context معنایی (معادل دکمه‌ی Codebase در Cursor)

- **اولویت:** P1 | **برآورد:** M/L | **وضعیت:** 🔴 | **وابستگی:** C1، M2
- **هم‌ارز در Cursor:** دکمه‌ی «Codebase» — مدل خودش بخش‌های مرتبط ریپو را در context می‌آورد

## هدف
یک مسیر بازیابی query-time: از متن پیام کاربر → top-k chunk با hybrid search →
گسترش ۱-هoppersای با import graph → rerank با `relevanceScorer` → بسته‌بندی در بودجه‌ی
توکن با attribution (این فایل‌ها به این دلیل وارد شدند). toggle «Codebase» کنار دکمه‌ی
ارسال chat.

## وضعیت فعلی در کد
همه‌ی اجزا موجودند، فقط به‌صورت مسیر query-time برای chat وصل نیستند:
- `hybridSearchService.ts` (BM25 + trigram + embedding) + `persistentStore.ts`
- `dependencyGraph.ts` (گسترش همسایگی) — `relevanceScorer.ts` (rerank)
- `contextPacker.ts` (بسته‌بندی) — `changeTracker.ts` (تازگی)

## طرح پیاده‌سازی
1. سرویس `autoContextService.retrieve(query, {budget, activeFile})`:
   - step 1: hybrid top-20 chunk
   - step 2: افزودن فایل‌های ۱-هopperای import شده/کننده‌ی فایل‌های hit
   - step 3: rerank همه با fusion: `bm25 + vector + recency + proximity(activeFile)`
   - step 4: انتخاب chunk ها تا سقف بودجه (پیش‌فرض 12k)، هر chunk با سربرگ
     `<!-- from: src/... reason: import-neighbor of active file -->`
2. toggle «Codebase» در `SidebarChat` (default: روشن در حالت agent، خاموش در ask)
3. اجرای retrieval قبل از build پیام‌ها در `convertToLLMMessageService`؛ نتیجه به‌صورت
   بلوک `<workspace_context>` + گزارش در breakdown (C2)
4. **حالت بدون embedding:** فقط BM25 + trigram (باز هم قابل استفاده — سازگاری BYOLLM)
5. کش نتیجه به ازای query hash (TTL 5 دقیقه) تا ویرایش پیام هزینه‌ی دوباره ندهد
6. دیباگ: پنل کوچک «what was retrieved & why» (همان attribution) — قابل باز/بسته

## معیارهای پذیرش
- [ ] سؤال درباره‌ی تابعی که اسمش در query آمده → chunk درست در context است
- [ ] با toggle خاموش، هیچ retrieval ای انجام نمی‌شود (عدد context می‌افتد)
- [ ] بدون provider برداری مسیر BM25-only کار می‌کند
- [ ] attribution هر chunk در UI قابل دیدن است

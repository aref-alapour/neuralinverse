# C6 — انتخاب خودکار Context معنایی (معادل دکمه‌ی Codebase در Cursor)

- **اولویت:** P1 | **برآورد:** M/L | **وضعیت:** 🔴 مسیر خودکار نیست؛ معادل دستی هست | **وابستگی:** C1، M2
- **هم‌ارز در Cursor:** دکمه‌ی «Codebase» — مدل خودش بخش‌های مرتبط ریپو را در context می‌آورد

## وضعیت راستی‌آزمایی‌شده (۲۰۲۶-۰۹-۰۷)

راستی‌آزمایی شد: **مسیر بازیابی خودکار وجود ندارد** — `grep autoContextService`
صفر نتیجه، و هیچ toggle «Codebase» در `SidebarChat` نیست.

**اما یک معادل نیمه‌کاره هست که در طرح دیده نشده بود:**
ابزار `context_semantic_search` (`prompts.ts:626`) از `hybridSearchService` استفاده
می‌کند (`toolsService.ts:1213`) و در حالت agent در دسترس مدل است. یعنی همان قابلیت
هست، ولی **مدل باید خودش تصمیم بگیرد صدایش بزند** — نه اینکه قبل از ساخت پیام
خودکار اجرا شود.

**تفاوت واقعی که باقی می‌ماند:**
| طرح C6 | چیزی که الان هست |
|---|---|
| قبل از build پیام، خودکار | فقط اگر مدل ابزار را صدا بزند |
| گسترش ۱-هاپی با import graph + rerank | جست‌وجوی تخت |
| attribution («چرا این فایل آمد») | ندارد |
| هزینه‌ی قابل پیش‌بینی در بودجه | هزینه‌ی یک round-trip ابزار |

**سؤال باز برای مالک:** آیا ارزش C6 (کامل) نسبت به ابزار موجود آن‌قدر هست که
M/L کار بگیرد؟ پیشنهاد: **اول C2 (gauge) ساخته شود**، چون تا وقتی نبینیم مدل چقدر
از ابزار semantic استفاده می‌کند، این تصمیم بی‌داده است.

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

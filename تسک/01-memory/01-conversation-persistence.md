# M1 — ماندگاری گفتگوی Agent ها (Conversation Persistence)

- **اولویت:** P0 — ادامه‌ی مستقیم branch فعلی `feat/agent-conversation-memory`
- **برآورد:** M (باقی‌مانده: S/M) | **وضعیت:** ✅ چت — تست owner سبز (۰۹-۰۹)؛ ادامه‌ی نشست workflow agent باز (نک. پایین) | **وابستگی:** M5
> **تست owner سبز شد (۲۰۲۶-۰۹-۰۹، بیلد `9a520bdfa81`).** شواهد در
> [`00-OWNER-TESTS-ROUND-2.md`](00-OWNER-TESTS-ROUND-2.md) و ژورنال زنده‌ی
> `escapezoom-html/.inverse/ledger/`.

> **اصلاح مارکر ۲۰۲۶-۰۹-۰۸ (بستن دریفت R1 — فایل 🔴 بود، README 🟡):**
> بخش «ذخیره‌سازی» این تسک دیگر باز نیست. سه لایه ماندگاری داریم:
> thread های Void روی `THREAD_STORAGE_KEY` (`chatThreadService.ts:761–775`)،
> ژورنال append-only ledger (M5)، و در استک بومی `ChatSessionStore` +
> `chatSessionOperationLog` + `objectMutationLog` با نوشتن `append` واقعی.
>
> **آنچه واقعاً مانده:** نگاشت agent→`conversationId` هنوز `Map` در RAM است
> (`workflowAgentService.ts:143`) و بعد از restart شناسه‌ی تازه می‌سازد؛ دو run
> هم‌زمانِ یک agent همان شناسه را می‌گیرند؛ فقط turn موفق آرشیو می‌شود
> (`:415`)؛ و فهرست/rename/delete/resume برای گفتگوهای workflow نداریم.
>
> ⚠️ توجه: `workflowAgentService` **زنده است** (ترانزیتی از `toolsService.ts:34`)
> — برخلاف `backgroundAgentService` که ثبت نشده. پس این کار روی کد زنده است.
- **هم‌ارز در Cursor:** ادامه‌ی thread بعد از بستن editor، تاریخچه‌ی گفتگوها، resume

## هدف
حافظه‌ی گفتگوی هر agent به‌جای RAM روی دیسک ذخیره شود؛ بعد از ری‌استارت IDE بتوان گفتگو را
از همان نقطه ادامه داد؛ گفتگوهای گذشته فهرست، قابل resume/delete/rename باشند.

## چرا مهم است
الان `workflowAgentService.ts` حافظه را در یک `Map` درون RAM نگه می‌دارد که با بستن IDE
پاک می‌شود. همین الان هم در `AGENTS.local.md` به‌عنوان limitation ثبت شده که دو agent همزمان
می‌توانند context هم را قاطی کنند — این تسک آن باگ را در سطح source ریشه‌ای حل می‌کند.
Cursor و Claude Code (session resume) و Codex هر سه گفتگو را نگه می‌دارند؛ بدون این، هیچ
جریان کاری جدی روی agent ها ممکن نیست.

## وضعیت فعلی در کد
- `src/vs/workbench/contrib/neuralInverse/browser/workflowAgentService.ts` — حافظه‌ی
  in-memory به ازای هر agent؛ سقف ۲۴ پیام / ۳۲k توکن تخمینی / ۱۶k کاراکتر per-turn؛
  فقط turn های موفق ذخیره می‌شوند؛ `clearAgentConversation()` برای ریست
- `src/vs/workbench/contrib/void/browser/conversationCompactor.ts` — خلاصه‌ساز
  ساختاریافته (Objective / Requirements / Key Decisions / Files / Tool Activity /
  Current State / Next Steps) + کش per-thread — قابل بازاستفاده برای summary موقع بستن
- دسترسی write به `.inverse/` با helper `withInverseWriteAccess` (از ماژول firmware)
- `agentManagerPart.ts` — UI تب Agents (جای افزودن لیست گفتگوها)

## طرح پیاده‌سازی
1. تعریف `IStoredConversation` در `common/workflowTypes.ts`:
   `{ id, agentId, title (auto از اولین پیام), createdAt, updatedAt, messages[], summary?, intakeAnswers? }`
2. سرویس جدید `browser/conversationStoreService.ts`:
   - مسیر: `.inverse/conversations/<agentId>/<convId>.json`
   - نوشتن اتمیک (tmp + rename) با debounce ~2s بعد از آخرین پیام
   - لیست/خواندن/حذف/تغییر نام؛ پاکسازی گفتگوهای بی‌استفاده بعد از ۳۰ روز (opt-out)
3. هنگام باز شدن agent در `agentManagerPart`: آخرین گفتگو به‌صورت خودکار hydridate شود؛
   لیست گفتگوهای قبلی + دکمه‌های New / Resume / Rename / Delete
4. روی resume وقتی پیام‌ها از سقف بیشتر شده: summary + tail (بازاستفاده از summarizer
   موجود در compactor) — رفتار یکسان با `_compactHistoryIfNeeded` در executor
5. **رفع باگ هم‌زمانی:** کلید حافظه = `conversationId` (نه `agentId`) تا دو run همزمان
   از یک agent جدا بمانند
6. ذخیره‌ی پاسخ‌های intake (از کامیت `9bc1183`) همراه گفتگو، تا بعد از resume دوباره
   پرسیده نشوند
7. پورت به `tools/live-patch.py` (pattern های minified) و اجرای elevated

## معیارهای پذیرش
- [ ] ری‌استارت IDE → گفتگوی همان agent با تاریخچه‌ی کامل ادامه پیدا می‌کند
- [ ] دو agent (یا دو run از یک agent) همزمان → context ها کاملاً جدا
- [ ] لیست گفتگوهای گذشته + resume + delete + rename کار می‌کند
- [ ] گفتگوی بلند بعد از resume به‌درستی summary+tail می‌شود نه خطای context window
- [ ] پورت live-patch انجام و marker ها پس از restart معتبر
- [ ] تست owner روی نسخه‌ی نصبی پاس شده (طبق گیت شماره ۲ `AGENTS.local.md`)

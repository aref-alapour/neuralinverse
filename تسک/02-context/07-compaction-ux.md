# C7 — تجربه‌ی کاربری Compaction (شفراف و قابل کنترل)

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🟡 موتور هست، UX دقیقاً صفر | **وابستگی:** C2
- **هم‌ارز در Cursor/Claude Code:** compaction خودکار قابل مشاهده + دستور /compact

## وضعیت راستی‌آزمایی‌شده (۲۰۲۶-۰۹-۰۷)

راستی‌آزمایی شد: **مارکر درست بود** و «UX ندارد» را باید تحت‌اللفظی خواند —
هیچ‌یک از ۵ گام طرح انجام نشده است.

- [ ] `/compact`: هیچ پارسر دستور خطی در ورودی چت نیست.
      `slashCommands: []` در `voidModelProvider.ts:862` خالی است.
- [ ] state `compacting`: تنها اثر compaction در UI یک `ctx.log` در
      `neuralInverse/browser/executor/agentExecutor.ts:597` است — که در چت
      sidebar اصلاً دیده نمی‌شود.
- [ ] `SummaryCard`: `conversation_summary` فقط در `conversationCompactor.ts`
      تولید می‌شود و هیچ رندر اختصاصی ندارد.
- [ ] toast «Xk توکن آزاد شد» و ستون compactions.

**قید مسیر دوگانه (مهم):** حالا دو مسیر فشرده‌سازی موازی وجود دارد —
`_assembleLedgerThread` (ledger، پیش‌فرض روشن) و `_maybeCompactThreadForSend`
(legacy). UX باید **هر دو** را پوشش دهد وگرنه در حالت پیش‌فرض چیزی نشان نمی‌دهد.
این در طرح اصلی نبود چون آن موقع ledger وجود نداشت.

**دستور بازتولید:**
```bash
grep -rn "slashCommand" src/vs/workbench/contrib/void/ | head
```

## هدف
موتور compaction ما (از کامیت `ee5e39f`) از نظر الگوریتم جلوتر از اکثر رقاست؛ ولی
کاربر هیچ‌وقت نمی‌فهمد چه اتفاقی افتاده. این تسک فقط UX است:
1. `/compact` به‌عنوان دستور (خلاصه‌سازی دستی همان لحظه)
2. نمایش وضعیت «در حال فشرده‌سازی…» موقع compaction خودکار
3. رندر متمایز پیام summary (کارت جمع‌شونده با آیکن) + badge «Xk توکن آزاد شد»
4. تنظیم: `keepLastNMessages` (تعداد پیام‌های tail که همیشه دست‌نخورده می‌مانند — الان ۸)

## وضعیت فعلی در کد
- `conversationCompactor.ts` — آستانه ۷۲٪، خلاصه‌ساز LLM با ساختار مشخص، watchdog،
  fallback قطع‌کردن، کش per-thread
- `chatThreadService._maybeCompactThreadForSend` (خط ~364) — فقط request خروجی را
  فشرده می‌کند، thread ذخیره‌شده دست نمی‌خورد
- `compactThread()` (خط ~312) — حالت دستی که thread ذخیره‌شده را بازنویسی می‌کند (بدون UI)
- بازگشت از خطای overflow: یک compaction اجباری + retry

## طرح پیاده‌سازی
1. پارسر دستورهای خطی در ورودی chat: `/compact` (و بعداً `/clear`، `/memory` در تسک M3)
   — قبل از ارسال به LLM intercept شود
2. حالت درخواست: وقتی `_maybeCompactThreadForSend` کار می‌کند، یک state
   `compacting: true` روی thread بگذارد → SidebarChat اسپینر متن «در حال فشرده‌سازی
   تاریخچه…» نشان دهد
3. کامپوننت `SummaryCard`: رندر `<conversation_summary>` به‌صورت کارت با
   expand/collapse (سرفصل‌های Objective/…/Next Steps به‌صورت لیست)
4. بعد از compaction موفق: toast «تاریخچه فشرده شد — ~Xk توکن آزاد شد» + پیوند به
   breakdown (C2)
5. ستون «compactions» در اطلاعات thread (چند بار، کی، چقدر آزاد شد)

## معیارهای پذیرش
- [ ] `/compact` همان لحظه thread را خلاصه و کارت summary را نشان می‌دهد
- [ ] compaction خودکار بدون «قطع ناگهانی» رخ می‌دهد و کاربر پیام/اسپینر می‌بیند
- [ ] summary قابل باز/بسته شدن است و محتوایش ساختاردار است
- [ ] تنظیم keepLastN از settings خوانده می‌شود

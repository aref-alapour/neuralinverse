# M4 — ایندکس مستندات و Knowledge Base (Cursor Docs)

- **اولویت:** P2 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** M2 (زیرساخت برداری)
- **هم‌ارز در Cursor:** @Docs — ایندکس مستندات وب (React docs، API داخلی، …) و تزریق در context

## هدف
کاربر بتواند مجموعه‌ای از منابع مستندات (URL های وب یا فایل‌های markdown محلی) برای
workspace تعریف کند؛ سیستم آن‌ها را fetch → chunk → embed کند و به‌عنوان منبع context
در chat و agent قابل بازیابی باشد.

## وضعیت فعلی در کد
- Context Engine با `embeddingService` + `persistentStore` + `hybridSearchService`
  آماده‌ی پذیرش منبع جدید است (الان فقط کد workspace را ایندکس می‌کند)
- ماژول modernisation یک «Knowledge Base» داخلی دارد (جدا از این مسیر)
- chat ابزار `openUrl` دارد ولی هیچ بازیابی docs ای وجود ندارد

## طرح پیاده‌سازی
1. تنظیمات per-workspace: `.inverse/docs.json` → `{ sources: [{id, url|path, maxDepth, refreshHours}] }`
2. سرویس `docsIndexService`:
   - fetch صفحه‌های وب (همان policy های network که برای httpRequest برقرار است)
   - تبدیل HTML → markdown ساده، chunk (سایز ~1200 کاراکتر با overlap)، embed، ذخیره
     در `persistentStore` با namespace جدا (`docs:`) تا از ایندکس کد جدا بماند
   - refresh زمان‌بندی‌شده با trigger infrastructure موجود
3. ابزار جدید برای chat و executor: `search_docs(query)` — بازیابی از namespace docs
4. تزریق در UI: منشن `@docs` (بعد از C3) و بلوک مستندات در gauge گزارش context (C2)
5. محدودیت‌ها: بدون اجرای JS در صفحات (fetch ساده)، سقف ۵۰۰ chunk به ازای هر منبع

## معیارهای پذیرش
- [ ] افزودن مستندات یک فریم‌ورک → پرسیدن سؤال API از آن → پاسخ بر پایه‌ی chunk درست
- [ ] refresh دوره‌ای محتوای تغییرکرده را به‌روز می‌کند
- [ ] حافظه و ایندکس docs هیچ‌وقت با ایندکس کد قاطی نمی‌شود

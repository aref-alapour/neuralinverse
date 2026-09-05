# G6 — صف، چرخه‌ی اجرا و پروتکل رویداد (پورت A6)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P1 (Wave 4) | **برآورد:** M | **وضعیت:** 🟡 زیرساخت صف ما جور دیگر هست | **وابستگی:** G3
- **منبع (راستی‌آزمایی‌شده):** `execution.py:1251-1411` (PromptQueue)، `main.py:351-446` (prompt_worker)، رویدادها پراکنده (فهرست پایین)، `comfy_execution/progress.py`

## تصحیح‌های مهم نسبت به handoff

1. **front-jump داخل PromptQueue نیست!** در `server.py:1078-1086` (POST /prompt) است:
   `"front": true` → **قدرمطلقِ number را منفی می‌کند** (و number ارسالی client عیناً
   پذیرفته می‌شود)؛ ترتیب heap بقیه‌اش را می‌کند. آیتم صف ۶تایی است:
   `(number, prompt_id, prompt, extra_data, outputs_to_execute, sensitive)` (server.py:1131).
2. **رویدادها یک‌جا نیستند** (server.py:269-327 فقط connection handler + مذاکره‌ی
   feature-flags است 292-317): `execution_start` execution.py:742، `executing` 496
   (و نشانگر پایان `{"node": null}` در main.py:406)، `executed` 436/578،
   `execution_cached` 770-772، `execution_success` 824، `execution_error` 712/536،
   `execution_interrupted` 699، `progress` از main.py:472 (`hijack_progress` 457-484)،
   `progress_state` از progress.py:183-185، `status` روی هر تغییر صف (server.py:1396).
   رویدادهای باینری در `protocol.py` (`BinaryEventTypes`: PREVIEW_IMAGE=1، TEXT=3، …)
   با مذاکره‌ی feature-flag.
3. **payload خطا:** `{prompt_id, node_id, node_type, exception_message,
   exception_type, executed, current_inputs, current_outputs}` (700-712) — canvas با
   `current_inputs` ویجت خطادار را هایلایت می‌کند. (خط 743 `execution_start` است نه
   error — تصحیح handoff.)

## پورت TS

1. **runner سریال:** worker-thread پایتون + `asyncio.run` per-prompt → در VS Code یک
   runner async سریال در event loop (`while (item = queue.take()) await executor…`)؛
   CPU-heavy داخل نودها → web worker. اینواریانت: **یک پرامپت در لحظه** + تغییرات
   صف قابل‌مشاهده.
2. **صف:** heapq → آرایه‌ی مرتب‌شده کوچک (اندازه‌ها کوچک‌اند؛ `front:true` درست عمل
   کند مهم‌تر از big-O)؛ عملیات `delete(ids)`/`clear()`؛ **slot حساس** (secrets جدا
   از payload و از history/queue listings — ببین G8-د).
3. **Interrupt با AbortSignal:** چک در شروع هر نود + هر progress tick؛
   `AbortError` را rethrow کن (معادل BaseException — catch های نود نتوانند قورتش
   دهند)؛ **اتمیک per-prompt** (پرچم سراسری در شروع هر پرامپت پاک می‌شود — 733؛
   `interrupt_if_running` 1323-1340 زیر mutex) و خروجی‌های جزئی حفظ می‌شوند.
4. **پروتکل رویداد** روی event bus موجود canvas/agent با همان نام‌ها + نگاشت به
   UX: `executing{node:null}` همیشه ترمینال است؛ `execution_cached` → کم‌نورسازی
   نودها؛ `progress`/`progress_state` → نوار پیشرفت نود.
5. **interrupt هدفمند:** `/interrupt` با `prompt_id` پشتیبانی می‌شود (targeted) —
   صف ما هم per-run cancel داشته باشد.
6. **flags صف (از قلم‌افتاده):** `set_flag/get_flags` (1399-1411) — کانال جانبی
   `free_memory`(=ریست کامل کش)/`unload_models` — معادل TS: flag «clearCaches».

## معیارهای پذیرش
- [ ] دو run در صف؛ interrupt وسط نودِ اول → `execution_interrupted` با خروجی جزئی؛
      run دوم سالم؛ `executing{node:null}` ترمینال است
- [ ] `front:true` واقعاً می‌پرد جلو (تست با سه آیتم)
- [ ] رویدادها به همان ترتیب پروتکل emit می‌شوند (تست ترتیب)
- [ ] interrupt نمی‌تواند روی run بعدی نشت کند (تست اتمیکی)

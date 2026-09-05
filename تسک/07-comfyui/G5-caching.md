# G5 — زیرسیستم کش (پورت A5 — پرچم‌دارِ ارزش کار)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P0 (Wave 3 — دمو اصلی) | **برآورد:** M/L | **وضعیت:** 🔴 | **وابستگی:** G3
- **منبع (راستی‌آزمایی‌شده):** `comfy_execution/caching.py` (613 خط)، `execution.py:60-101` (IsChangedCache)

## معناشناسی دقیق (از کد)

1. **دو کش:** خروجی‌ها (کلید = input signature) و آبجکت‌ها (کلید = `(node_id,
   class_type)` — caching.py:79 — از ویرایش ورودی‌ها **نجات می‌یابد**؛ آبجکت زنده‌ی
   نود را نگه می‌دارد). `CacheSet` 116-155.
2. **signature:** `get_immediate_node_signature` 109-127 = `[classType, isChanged,
   (nodeId در صورت لزوم)] + (inputName, value | ("ANCESTOR", index, socket))` —
   **تصحیح:** تاپل ANCESTOR **۳ عنصر** دارد (index + `ancestor_socket`)، نه ۲.
   ایندکس از `get_ordered_ancestry` 131-148: پیمایش بازگشتی روی `sorted(inputs.keys())`
   → DFS deterministic — زیرگراف rename-شده اما یکسان، کش می‌خورد.
3. **nodeId در signature فقط وقتی:** `NOT_IDEMPOTENT` یا hidden-`UNIQUE_ID` مصرف
   شده باشد (19-24, 117).
4. **سم‌زنی unhashable:** پایتون با `NaN != NaN` (Unhashable در 50-52، NaN روی
   exception در IsChangedCache — execution.py:98). در TS: **sentinel اختصاصی
   `UNHASHABLE`** با equals همیشه-false — هرگز به `Object.is(NaN,NaN)===false`
   عمیق در Map تکیه نکن (درس ترجمه شماره ۴ handoff).
5. **IS_CHANGED:** فقط با ثابت‌ها اجرا می‌شود (کامنت execution.py:90)، memo روی
   **node dict پرامپت** ذخیره می‌شود (95-100) — در TS به side-table جدا منتقل کن
   ( mutated کردن DynamicPrompt تمیز نیست)؛ نتیجه‌ی ExecutionBlocker → None (95).
6. **Eviction به‌صورت interface قابل‌تعویض:** `HierarchicalCache` 361-408 (subcache
   per parent chain — برای زیرگراف‌های expand شده)، `LRUCache` 439-493 (شمارنده‌ی
   generation)، `RAMPressureCache` 522-613 (**بازطراحی**: به torch/psutil گره خورده —
   پورت نکن مگر موتور در worker با خروجی‌های بزرگ اجرا شود). برای ما: **LRU +
   invalidation با signature** کافی و لازم است. `clean_unused` (175-197): پاک کردن
   کلیدهای غایب از پرامپت جدید.
7. **اجرای مجدد جزئی:** فقط زیرگراف‌های تغییرشده دوباره اجرا می‌شوند؛ بقیه به‌عنوان
   `execution_cached` گزارش می‌شوند (UI کم‌نورشان می‌کند). `partial_execution_targets`
   (server.py:1106).
8. **از قلم‌افتاده‌های مهم handoff (پورت شود):**
   - **`comfy_execution/cache_provider.py`** (138 خط): cache provider خارجی قابل‌اتصال
     (`should_cache/on_lookup/on_store` + prompt lifecycle) — اینترفیس را نگه دار؛
     بعداً کش Redis/دیسک برای background agents (A1) ممکن می‌شود
   - **semantics قطع × کش:** خروجی هر نود **همان لحظه‌ی تکمیلش** کش می‌شود
     (execution.py:617) → خروجی‌های جزئی بعد از interrupt زنده‌اند و در run بعدی
     `execution_cached` برمی‌گردند؛ نود در-دست-اجرا هرگز کش نمی‌شود. کش‌ها بین
     پرامپت‌ها می‌مانند و فقط با flag `free_memory` کامل ریست می‌شوند (main.py:422-433)
   - **پیشوندهای deterministic ephemeral** (G1-5) پیش‌شرط کشِ زیرگراف‌هاست

## معیارهای پذیرش
- [ ] گراف diamond ده‌نودی: تغییر یک widget → فقط مسیر وابسته دوباره اجرا می‌شود،
      بقیه `execution_cached` (دموی اصلی Wave 3)
- [ ] حذف یک شاخه → کلیدهای کشش پاک می‌شوند (clean_unused)
- [ ] rename نود بدون تغییر ساختار → همان کش (اثبات ایندکس اجدادی)
- [ ] IS_CHANGED با exception → کش آن نود برای همیشه miss (سم‌زده)
- [ ] interrupt وسط اجرا → خروجی‌های کامل‌شده در run بعدی از کش می‌آیند
- [ ] تست‌های آینه: `test_execution.py` (full/partial cache + custom IS_CHANGED) و
      `tests-unit/execution_test/test_cache_provider.py`

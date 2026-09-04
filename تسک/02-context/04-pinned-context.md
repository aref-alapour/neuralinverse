# C4 — Context سنجاق‌شده و Notepads (Pinned Files + Notepad Blocks)

- **اولویت:** P1 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** C3
- **هم‌ارز در Cursor:** فایل‌های Pinned که همیشه در context می‌مانند + Notepads
  (بلاک‌های context قابل استفاده‌ی مجدد)

## هدف
دو مکانیزم «چسباندن» context:
1. **Pinned:** فایل/پوشه‌ای که کاربر سنجاق می‌زند در **هر** درخواست (تا وقتی سنجاق است)
   تزریق می‌شود و از compaction هم مصون است.
2. **Notepad:** بلاک متنی (نام + محتوا) که مثل یک منبع context قابل attach/detach است —
   برای spec ها، конوانسیون‌ها، توضیح API که هر بار نمی‌خواهد تایپ شود.

## وضعیت فعلی در کد
- فایل‌های باز + فایل فعال تزریق می‌شوند ولی نه ماندگار و نه مصون از compaction
- `agentScratchpadService.ts` زیرساخت ذخیره‌ی متنی per-agent دارد (قابل توسعه)
- compaction در مرز user-message جمع می‌کند و به pinned کاری ندارد

## طرح پیاده‌سازی
1. **مدل:** `IPinnedItem { type: file|folder|notepad, uri?, name, content?, createdAt }`
   — ذخیره per-workspace در `IStorageService`
2. **ورودی‌های سنجاق:**
   - منوی context ادیتور: «Add to Chat Context» (pin فایل)
   - از chip منشن (C3): دکمه‌ی pin روی chip
   - Notepad: دکمه «+ Notepad» در sidebar → ادیتور کوچک (name + body)
3. **تزریق:** بلوک `<pinned_context>` بعد از system prompt و قبل از history؛
   سقف: ۸ آیتم / ۲۰k توکن (فراتر رفت → قدیمی‌ترین غیر-pin حذف + هشدار در gauge)
4. **مصونیت از compaction:** `conversationCompactor` هرگز محتوای pinned را جمع نمی‌کند؛
   اگر مجموع pinned + system > نیمی از پنجره شد → هشدار صریح به کاربر
5. UI: بخش «Pinned» در زیر ورودی chat با chip های قابل حذف

## معیارهای پذیرش
- [ ] فایل سنجاق‌شده بعد از ۳ compaction همچنان در context است (با breakdown اثبات می‌شود)
- [ ] Notepad ساخته/ویرایش/attach/detach می‌شود و محتوایش تزریق می‌شود
- [ ] سقف‌ها با هشدار درست کار می‌کنند
- [ ] pin ها بین session ها می‌مانند

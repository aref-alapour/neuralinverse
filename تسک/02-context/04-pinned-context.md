# C4 — Context سنجاق‌شده و Notepads (Pinned Files + Notepad Blocks)

- **اولویت:** P1 | **برآورد:** M (باقی‌مانده: M) | **وضعیت:** 🟡 مسیر تزریق آماده، مصرف‌کننده ندارد | **وابستگی:** C3
- **هم‌ارز در Cursor:** فایل‌های Pinned که همیشه در context می‌مانند + Notepads
  (بلاک‌های context قابل استفاده‌ی مجدد)

## وضعیت راستی‌آزمایی‌شده (۲۰۲۶-۰۹-۰۷)

**مارکر قبلی 🔴 کهنه بود** — گام ۳ و ۴ طرح (تزریق + مصونیت از فشرده‌سازی) در
جریان M5 از قبل ساخته شده‌اند.

**انجام‌شده:**
- `assemble()` ورودی `pinnedBlocks?: string[]` می‌گیرد (`contextAssembler.ts:55`)
  و آن‌ها را به‌صورت `<pinned_context>…</pinned_context>` رندر می‌کند (`:158`)
- ترتیب پایدار `brief → pinned → recalled → tail` تضمین شده (`:153`) و pinned در
  محاسبه‌ی بودجه لحاظ می‌شود (`:121,135`)
- **مصونیت از compaction ذاتی است**: pinned جزء head است و فقط tail کوتاه می‌شود
- تست‌ها موجودند: `test/node/contextAssembler.test.ts:199,235`

**باقی‌مانده — هیچ‌چیز در production این را پُر نمی‌کند:**
- [ ] `IPinnedItem` و ذخیره‌ی per-workspace در `IStorageService` — وجود ندارد
- [ ] ورودی‌های UI (منوی ادیتور، دکمه‌ی pin روی chip، Notepad)
- [ ] وصل کردن به فراخوانی `assemble()` در `chatThreadService.ts:357`
- [ ] سقف ۸ آیتم / ۲۰k توکن + هشدار

**نکته:** `grep pinnedBlocks` بیرون از `contextAssembler.ts` **فقط فایل تست** را
برمی‌گرداند — یعنی قابلیت ساخته و تست شده ولی هرگز در مسیر واقعی صدا زده نمی‌شود.
برآورد کار از M به «M ولی بدون کار assembler» کاهش می‌یابد.

**دستور بازتولید:**
```bash
grep -rn "pinnedBlocks" src/ | grep -v contextAssembler.ts   # → فقط فایل تست
```

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

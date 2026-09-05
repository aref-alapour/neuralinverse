# C3 — منشن‌ها در ورودی چت (@file / @folder / @symbol / @agent / @web)

- **اولویت:** P1 | **برآورد:** M/L | **وضعیت:** 🔴 | **وابستگی:** C2 (نمایش در gauge)
- **هم‌ارز در Cursor:** @Files @Folders @Code(symbol) @Web @Docs — قلب UX کنترل context

## هدف
در ورودی chat با تایپ `@` یک منوی fuzzy باز شود؛ انتخاب‌شده به chip تبدیل شود؛ chip ها
در convert به context واقعی translate شوند. این دقیقاً همان تجربه‌ای است که کاربران
Cursor برای «قفل کردن» context استفاده می‌کنند.

## وضعیت فعلی در کد
- ورودی chat: `react/src/sidebar-tsx/SidebarChat.tsx` (الان انتخاب متن/فایل فعال stage می‌شود
  ولی UX منشن ندارد)
- `workspaceSymbolIndex.ts` آماده‌ی سرویس‌دهی @symbol
- `neuralInverseSubAgentService` + ابزارهای `ask_powermode` / `query_ni_agent` از قبل
  امکان delegate دادن به sub-agent را دارند (فقط باید به شکل منشن expose شوند)
- fuzzy matching: از quick input provider های VS Code می‌توان کمک گرفت

## طرح پیاده‌سازی
1. **پارسر ورودی:** تشخیص توکن `@...` در `SidebarChat` موقع تایپ (قبل از submit)؛
   رندر chip: `{type, label, uri?}` — chip ها بخشی از state پیام می‌شوند
2. **منابع منشن (به ترتیب پیاده‌سازی):**
   - `@file` / `@folder` — جست‌وجوی fuzzy روی workspace files (quick input)
   - `@symbol` — `workspaceSymbolIndex` (کلاس/تابع → فایل + رنج)
   - `@agent` — delegate به sub-agent (نقش‌ها: explorer/reviewer/tester/…)؛ نتیجه به‌صورت
     نتیجه‌ی tool-call در thread می‌آید (زیرساخت موجود)
   - `@docs` — بعد از M4
   - `@web` — جست‌وجوی وب (فقط وقتی provider تنظیم شده؛ در غیر این‌صورت مخفی)
3. **تبدیل به context:** در `convertToLLMMessageService`، chip ها به بلوک‌های
   `<file uri=...>` با بودجه‌ی توکن مشخص (per-type: file=4000، symbol=1500) تبدیل شوند؛
   سهمشان در gauge (C2) جدا گزارش شود
4. رفتار: chip تا وقتی کاربر حذفش نکند می‌ماند (پین شدن خودکار در طول thread)
5. autocomplete منشن با کیبورد (↑↓ + Enter) و نمایش مسیر کامل در کنار نام

## معیارهای پذیرش
- [ ] `@` → منو باز می‌شود، تایپ فیلتر می‌کند، Enter انتخاب می‌کند، chip رندر می‌شود
- [ ] `@file` محتوای فایل را داخل context می‌آورد (در breakdown دیده می‌شود)
- [ ] `@symbol` تعریف symbol را می‌آورد نه کل فایل را
- [ ] `@agent` یک sub-agent واقعی اجرا و نتیجه را برمی‌گرداند
- [ ] حذف chip = حذف از context (عدد gauge می‌افتد)

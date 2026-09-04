# A2 — Native Tool Calling در Workflow Executor

- **اولویت:** P1 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** —
- **هم‌ارز در Cursor:** تماس ابزار بومی (بدون خطای parse) — پایداری agent

## هدف
executor الان ابزارها را با پروتکل «JSON داخل markdown» تبلیغ می‌کند و خروجی را با
`toolCallParser` می‌خواند. برای مدل‌های قوی (Anthropic/OpenAI/Gemini/…) تماس ابزار
بومی (function calling) پایدارتر است — خطای فرمت صفر می‌شود. JSON-block به‌عنوان
fallback برای مدل‌های ضعیف/OSS می‌ماند (لازم‌اش داریم).

## وضعیت فعلی در کد
- `agentExecutor.ts` — پروتکل JSON-block؛ عمداً `chatMode: null, allowedToolNames: []`
  می‌فرستد تا لایه‌ی Void ابزار دوم تزریق نکند
- `chatThreadService` از قبل تماس ابزار native را (با فرمت‌های openai/anthropic/gemini)
  از طریق `specialToolFormat` در `modelCapabilities.ts` پشتیبانی می‌کند — مسیر آماده است
- `toolCallParser.ts` + لایه‌ی `ossModelEnhancement` (retry اصلاحی) برای حالت fallback

## طرح پیاده‌سازی
1. تنظیم per-agent یا مرکزی: `"toolProtocol": "native" | "json" | "auto"` (پیش‌فرض auto)
2. `auto`: اگر مدل `specialToolFormat != none` → native؛ وگرنه JSON-block فعلی
3. در حالت native: تبدیل schema های ScopedToolRegistry به فرمت provider (همان تبدیلی
   که chat انجام می‌دهد) و پارس tool_calls از پاسخ به جای regex روی markdown
4. برای حلقه‌ی اجرا: پشتیبانی از tool_use_id های provider برای جفت‌کردن نتیجه
   (به‌جای ترتیب ظاهری)
5. متریک: نرخ خطای parse ابزار (شمارنده‌ی ساده در run history) — برای مقایسه‌ی قبل/بعد
6. **تست رگرسیون:** همان تسک روی یک مدل OSS ضعیف با auto → مسیر JSON-block بدون تغییر

## معیارهای پذیرش
- [ ] با مدل native-capable: هیچ `tool parse error` در run history ثبت نمی‌شود
- [ ] با مدل ضعیف: رفتار فعلی عیناً حفظ می‌شود
- [ ] اجرای موازی ابزار (`maxParallelToolCalls`) در حالت native هم کار می‌کند
- [ ] متریک نرخ خطا در UI run history دیده می‌شود

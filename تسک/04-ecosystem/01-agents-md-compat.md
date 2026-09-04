# E1 — سازگاری با AGENTS.md / CLAUDE.md / .cursorrules

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🔴 | **وابستگی:** —
- **هم‌ارز در Cursor:** خواندن rules فایل‌های استاندارد صنعت

## هدف
سریع‌ترین بردِ این backlog: هر ریپویی که برای Claude Code / Codex / Cursor تنظیم
شده، بی‌دردسر با NeuralInverse هم کار کند. الان فقط `.neuralinverserules` خوانده
می‌شود.

## وضعیت فعلی در کد
- `convertToLLMMessageService.ts` (خطوط ~۳۷۷ و ~۸۲۴-۸۶۶) — خواندن
  `.neuralinverserules` از هر پوشه‌ی workspace و تزریق به‌عنوان «GUIDELINES»
- هیچ پشتیبانی از AGENTS.md / CLAUDE.md / .cursorrules وجود ندارد

## طرح پیاده‌سازی
1. فهرست discovery به ترتیب اولویت (اولین موجود از هر سطح خوانده می‌شود + merge):
   - سطح workspace root: `AGENTS.md` > `CLAUDE.md` > `.cursorrules`
   - دایرکتوری Cursor: `.cursor/rules/*.mdc` (phase 2 — پارس frontmatter با glob های
     alwaysApply/auto-attached؛ phase 1: فقط فایل‌های همیشه‌فعال به‌صورت متن ساده)
   - همیشه: `.neuralinverserules` (حفظ سازگاری — اگر هر دو باشند، هر دو با سرفصل جدا)
2. سقف تزریق: مجموع rules تا ~۳۰۰ خط (truncate با نشانگر) — هم‌راستا با رفتار فعلی
3. دیده‌بانی: در breakdown context (C2) منبع «rules» با نام فایل نمایش داده شود
   تا کاربر بفهمد چه چیزی خوانده شده
4. سند: یک خط در README محصول (پس از upstream شدن) که AGENTS.md پشتیبانی می‌شود —
   برای SEO و onboarding مهم است

## معیارهای پذیرش
- [ ] ریپویی که فقط CLAUDE.md دارد → محتوایش در system prompt تزریق می‌شود
- [ ] هر سه فایل موجود → همه با سرفصل جدا و بدون duplication تزریق می‌شوند
- [ ] فایل غول‌پیکر (۱۰۰۰+ خط) truncate با نشانگر می‌شود
- [ ] نام فایل فعال در breakdown دیده می‌شود

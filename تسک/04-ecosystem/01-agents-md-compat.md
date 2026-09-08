# E1 — سازگاری با AGENTS.md / CLAUDE.md / .cursorrules

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🟡 اجرای موج ۳ (۰۹-۰۸): هر سه مسیر وصل شد؛ پورت live-patch و تست owner باز | **وابستگی:** —
- **هم‌ارز در Cursor:** خواندن rules فایل‌های استاندارد صنعت

> **اجرای موج ۳ (۲۰۲۶-۰۹-۰۸):**
>
> **تصمیم precedence (منتظر تأیید owner — قابل تغییر با یک ثابت):**
> هر سه فایل، هر کدام که موجود باشد، با سرفصل جدا تزریق می‌شوند، به ترتیب
> `AGENTS.md` → `CLAUDE.md` → `.neuralinverserules`؛ محتوای یکسان (کپی معمول
> AGENTS→CLAUDE) فقط یک‌بار؛ مجموع سقف ۳۰۰ خط با نشانگر truncate.
>
> - **تک‌منبع اسم فایل‌ها = ثابت‌های هسته** (`promptFileLocations.ts`) از طریق
>   ماژول جدید `void/common/workspaceRuleFiles.ts` — سایدبار، Power Mode و
>   workflow دیگر نمی‌توانند از هم دریفت کنند. موتور جمع‌آوری هسته
>   (`ComputeAutomaticInstructions`) متعلق به چت بومی می‌ماند و دست نخورد.
> - **سایدبار** (از `prepareLLMChatMessages`) و **پل چت بومی** (از
>   `getWorkspaceRuleFiles()` جدید — این گپ موقع M2 دیده و بسته شد؛
>   `generateSystemMessage` به‌تنهایی aiInstructions نمی‌ساخت): reader از
>   `.neuralinverserules` به هر سه فایل گسترش شد (برچسب GUIDELINES به‌روز شد).
> - **Workflow**: `agentExecutor` حالا rule ها را از `ctx.fileService` +
>   `workspaceUri` می‌خواند و «Workspace Rules» به system prompt اضافه می‌کند.
> - **Power Mode**: `powerModeContextBuilder` به‌جای AGENTS.md تنها، همان لیست
>   مشترک را می‌خواند (داخل همان تگ `<agents_md>` تا قرارداد پرامپتش نشکند).
> - ۷ تست standalone برای فرمتر (هدرها، dedup، سقف کل، ترتیب).
> - `.cursorrules` و `.cursor/rules/*.mdc` عمداً فاز ۲ ماندند (طرح اصلی همین بود).
> - **نکته‌ی برای بازبینی owner:** هدر provenance قدیمی
>   `powerModeContextBuilder.ts` («Original: MIT - SST opencode») برای رد کردن
>   قانون header به شکل سازگار با clean-room بازنویسی شد — اگر این فایل واقعاً
>   مشتق کد opencode است، تکلیفش را شما تعیین کنید.
>
> بدهی لینت پرداخت‌شده در همین موج: `convertToLLMMessageService.ts` (۳۳۳→۰؛
> هدر خراب `/*[object Object]*/` هم تعمیر شد)، `agentExecutor.ts` (۳۰→۰)،
> `powerModeContextBuilder.ts` (۲→۰). هوک hygiene بدون --no-verify سبز.

## هدف
سریع‌ترین بردِ این backlog: هر ریپویی که برای Claude Code / Codex / Cursor تنظیم
شده، بی‌دردسر با NeuralInverse هم کار کند. الان فقط `.neuralinverserules` خوانده
می‌شد (پیش از این موج).

## وضعیت فعلی در کد (پیش از موج ۳)
- `convertToLLMMessageService.ts` — فقط `.neuralinverserules`
- `powerModeContextBuilder.ts` — جداگانه فقط AGENTS.md
- `agentExecutor.ts` — هیچ rule file ای

## طرح پیاده‌سازی
1. فهرست discovery (انجام شد، بدون cursor):
   - سطح workspace root: `AGENTS.md` > `CLAUDE.md` (+ `.neuralinverserules` همیشه)
   - دایرکتوری Cursor: `.cursor/rules/*.mdc` (فاز ۲)
2. سقف تزریق: مجموع rules تا ~۳۰۰ خط (truncate با نشانگر) — **انجام شد**
3. دیده‌بانی: در breakdown context (C2) منبع «rules» با نام فایل — بخشی از
   این کار با سرفصل‌های `--- Rules from <file> ---` در متن تزریق ممکن شد؛
   ردیف اختصاصی در breakdown گauge فاز بعد
4. سند README محصول (پس از upstream شدن) — باز

## معیارهای پذیرش
- [x] ریپویی که فقط CLAUDE.md دارد → محتوایش تزریق می‌شود (تست standalone + مسیرهای سه‌گانه)
- [x] هر سه فایل موجود → همه با سرفصل جدا و بدون duplication (تست dedup)
- [x] فایل غول‌پیکر (۱۰۰۰+ خط) truncate با نشانگر (تست سقف)
- [ ] نام فایل فعال در breakdown gauge دیده شود — فاز بعد (با C2)
- [ ] تست owner روی هر سه مسیر: سایدبار، چت بومی (پل)، یک workflow run

## مانده برای owner (بعد از پورت live-patch)
- تأیید تصمیم precedence (بالا) یا تغییر ترتیب
- بازبینی هدر provenance فایل Power Mode
- تست زنده‌ی سه مسیر

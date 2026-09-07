# A7 — سخت‌سازی پل چت بومی (`voidModelProvider`) به‌عنوان سطح اصلی محصول

- **اولویت:** **P0 — پرلوریج‌ترین تسک این بک‌لاگ** | **برآورد:** M | **وضعیت:** 🔴
- **کشف:** ۲۰۲۶-۰۹-۰۸، [ممیزی سه‌گانه](../05-quality/task-vs-code-audit-2026-09-08.md)
- **باز می‌کند:** A3، A4، A5، C2، C3، C7، E1، E2، F5 — همه با «وصل‌کردن» به‌جای «ساختن»

## چرا این تسک وجود دارد

نقشه‌ی تسک‌ها فرض کرده سطح محصول ما سایدبار Void است. ولی
`contrib/void/browser/voidModelProvider.ts` (۱۰۵۶ خط، ثبت‌شده در
`void.contribution.ts:68`، فاز `BlockRestore`) مدل‌های BYOLLM ما را
**به‌عنوان agent پیش‌فرض چت بومی VS Code ۱.۱۲۷** ثبت می‌کند:

```bash
grep -n "registerAgentImplementation\|registerLanguageModelProvider" \
  src/vs/workbench/contrib/void/browser/voidModelProvider.ts
# :842 registerLanguageModelProvider('neuralInverse', this)
# :867 registerAgentImplementation(NI_AGENT_ID, agentImpl)   ← isDefault: true
```

با مودهای Ask/Edit/Agent، حلقه‌ی agentic کامل با tool-call (`:552–731`)، و
برداشتن ابزارهای MCP از `ILanguageModelToolsService` (`:482`).

**نتیجه:** هر چیزی که استک بومی دارد — checkpoint فایلی، gauge مصرف context،
plan، مجوز، AGENTS.md/CLAUDE.md، skills، hooks، todo، سؤال ساختاریافته، صف
پیام — بالقوه با موتور خودمان کار می‌کند. این پل تنها نقطه‌ای است که آن «بالقوه»
را به «بالفعل» تبدیل می‌کند. هر روزی که سخت نشود، ما داریم نسخه‌ی ضعیف‌تر همان
قابلیت‌ها را در سایدبار از صفر می‌نویسیم.

## پنج شکافِ تأییدشده در پل

### الف) mode و فهرست ابزار enforce نمی‌شوند — 🔴 ایمنی
پل فهرست کامل ابزارهای ثبت‌شده را برمی‌دارد و انتخاب ابزارِ کاربر و محدودیت
mode را کامل اعمال نمی‌کند. کنار [A5](05-plan-mode.md) — که در آن
`getThreadPlanMode` صفر caller دارد — یعنی **Plan mode در هیچ‌کدام از دو مسیر
واقعاً read-only نیست**. این اولین چیزی است که باید بسته شود.

### ب) بعضی ابزارها از `invokeTool` هسته رد می‌شوند، بعضی مستقیم route
`:670` از `_lmToolsService.invokeTool` استفاده می‌کند ولی `:572` یک مسیر
نوشتن-فایلِ مستقیم دارد. هر ابزاری که مسیر دوم را برود، از confirmation،
checkpoint و ثبت عملیات هسته **رد می‌شود** — یعنی A3 و A4 روی آن اثر ندارند.

### ج) Ledger به این مسیر وصل نیست
`VoidChatAgentImpl` حلقه‌ی خودش را دارد و `contextAssembler`/ledger را صدا
نمی‌زند. یعنی گفتگوی چت بومی نه بایگانی می‌شود، نه compaction می‌خورد، نه در
recall دیده می‌شود — دقیقاً همان چیزی که M5 قرار بود حل کند.

### د) رویداد usage نمی‌فرستد
gauge بومی (`chatContextUsageWidget.ts`) آماده است ولی چیزی تغذیه‌اش نمی‌کند.
با [Q12](../05-quality/12-desktop-usage-parity.md) با هم بسته شوند.

### ه) تبدیل پارامتر ابزار فایل یکدست نیست
قراردادهای `filePath`/`old_string`/`new_string` بین پل و ابزارهای هسته هم‌ریخت
نیستند — مرتبط با [F1](../06-freebuff/F1-edit-primitives.md).

## معیار پذیرش

1. **Plan واقعاً read-only است.** در mode ی که ابزار نوشتن ندارد، تلاش مدل برای
   نوشتن رد می‌شود — تست خودکار، نه بازرسی چشمی.
2. **یک مرز واحد برای اجرای ابزار.** هیچ ابزاری مسیر مستقیم `:572` را نرود؛ همه
   از `invokeTool` عبور کنند تا confirmation و checkpoint یک‌بار و در یک‌جا اعمال شوند.
3. **checkpoint خودکار.** هر نوبت agent که فایل تغییر می‌دهد یک checkpoint ثبت
   می‌کند و دکمه‌ی Restore کار می‌کند (منبعش طبق تصمیم [A3](03-file-checkpoints.md)).
4. **gauge عدد واقعی نشان می‌دهد** بعد از هر نوبت، و بعد از تعویض مدل درست
   به‌روز می‌شود.
5. **گفتگوی چت بومی در ledger می‌نشیند** — journal پر می‌شود، compaction اجرا
   می‌شود، و `recall_history` همان گفتگو را پیدا می‌کند.
6. **AGENTS.md/CLAUDE.md و skills به prompt می‌رسند** — با یک تست که فایل قاعده
   می‌سازد و اثرش را در پیام ارسالی می‌بیند. (توجه به تنظیم
   `chat.collectInstructionsInExtension` که تعیین می‌کند جمع‌آوری در هسته بماند
   یا به extension برود.)

## تصمیم محصولی که این تسک اجباری می‌کند

**سایدبار Void و چت بومی هر دو می‌مانند، یا یکی سطح اصلی می‌شود؟** تا این روشن
نشود، هر تسک UI دوبار برآورد می‌خورد. توصیه‌ی ممیزی: **چت بومی سطح اصلی**
(چون checkpoint، gauge، plan، skills، hooks و صف را رایگان می‌دهد) و سایدبار به
تدریج به همان agent مهاجرت کند. این تصمیم ورودی مستقیم
[Q3](../05-quality/03-unify-agent-stacks.md) است — که با کشف این پل حالا
**چهار** حلقه‌ی اجرا دارد نه سه: سایدبار Void، executor workflow، Power Mode،
و `VoidChatAgentImpl`.

## وابستگی‌ها

- بعد از این تسک، دامنه‌ی A3/A4/A5/C2/C7 به «وصل‌کردن» کوچک می‌شود.
- [Q12](../05-quality/12-desktop-usage-parity.md) پیش‌نیاز بند ۴ است.
- [F1](../06-freebuff/F1-edit-primitives.md) با بند ۵ شکاف «ه» هم‌پوشانی دارد.

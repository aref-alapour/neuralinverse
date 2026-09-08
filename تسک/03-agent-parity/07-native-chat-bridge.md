# A7 — سخت‌سازی پل چت بومی (`voidModelProvider`) به‌عنوان سطح اصلی محصول

- **اولویت:** **P0 — پرلوریج‌ترین تسک این بک‌لاگ** | **برآورد:** M | **وضعیت:** 🟡 بندهای الف و ب بسته (`f332502e5dc`)؛ ج/د/ه باز
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

### الف) ~~mode و فهرست ابزار enforce نمی‌شوند~~ ✅ بخش فهرست ابزار بسته شد

پل فهرست کامل ابزارهای ثبت‌شده را برمی‌داشت و به `invokeTool` هم
`userSelectedTools: undefined` می‌داد — یعنی ابزاری که کاربر در tool picker
خاموش کرده بود همچنان قابل صدا زدن بود. **رفع (`f332502e5dc`):** هر دو نقطه
`request.userSelectedTools` را رعایت می‌کنند؛ نقشه‌ی خالی/غایب یعنی «کاربر
چیزی را محدود نکرده» تا رفتار فعلی کسانی که picker را به کار نمی‌برند عوض نشود.

**درباره‌ی plan mode:** با گارد [A5](05-plan-mode.md) (کامیت `feffd9a3285`) این
مسیر هم پوشش پیدا کرد — تأیید شد که `voidModelProvider.ts:711` از همان نقشه‌ی
`callTool` می‌گذرد که گارد رویش نشسته. پس Plan در هر دو مسیر واقعاً read-only
است. باقی‌مانده: نگاشت mode های بومی (Ask/Edit/Agent) به فهرست ابزار متناظر.

### ب) ~~بعضی ابزارها از `invokeTool` هسته رد می‌شوند، بعضی مستقیم route~~ ✅ بسته شد

> **تصحیح ۲۰۲۶-۰۹-۰۸ حین اجرا — توصیف اولیه غلط بود.** `:572` «مسیر مستقیم
> نوشتن فایل» نیست؛ یک بلاک **remap** است که نام ابزارهای void را به id های
> ابزار هسته می‌نگارد (`vscode_editFile_internal`، `run_in_terminal`،
> `vscode_fetchWebPage_internal`، `vscode_askQuestions`) و دقیقاً همان چیزی است
> که به ویرایش‌ها diff و approval هسته را می‌دهد. یعنی این بلاک بخشی از راه‌حل
> بود، نه مسئله.
>
> **شکاف واقعی یک لایه پایین‌تر بود:** شاخه‌ی fallbackِ «harness ویلد» که
> `ConfirmationNotNeeded` را بی‌قید pass می‌کرد. سایدبار قبل از اجرای هر ابزار
> builtin به `approvalTypeOfBuiltinToolName` نگاه می‌کند و حلقه را برای تأیید
> کاربر نگه می‌دارد (`chatThreadService.ts:1018`)؛ پل همان ابزار را **بدون
> هیچ تأییدی** اجرا می‌کرد. یعنی یک `bash` یا `edit` صرفاً به‌خاطر اینکه از چت
> بومی آمده بود، بی‌نظارت می‌رفت.
>
> **رفع (`f332502e5dc`):** پل حالا همان map و همان تنظیم `autoApprove` را
> می‌خواند، invocation را در `WaitingForConfirmation` نگه می‌دارد تا دکمه‌های
> تأیید بومی رندر شوند، و منتظر می‌ماند. رد کردن کاربر به‌عنوان «refusal» به مدل
> برمی‌گردد نه خطا، تا مدل مسیر دیگری انتخاب کند به‌جای retry.

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

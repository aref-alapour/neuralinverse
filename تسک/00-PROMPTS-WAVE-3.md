# 00 — پرامپت‌های موج ۳ (بعد از بسته‌شدن A7 بندهای الف–د)

> پایه: `4c1e1c16b56`. مرجع: [ممیزی](05-quality/task-vs-code-audit-2026-09-08.md)
> و [پرامپت‌های موج ۱/۲](00-PROMPTS-2026-09-08.md) (بخش «الف» آن فایل — پرامپت
> شروع — بدون تغییر برای هر session زیcode لازم است).

## چرا این موج الان ممکن شد

A7 بندهای الف تا د بسته شدند، و همان چیزی که پیش‌بینی شده بود اتفاق افتاد:
**پنج تسک از «ساختن» به «وصل‌کردن» تبدیل شدند.** حالا در پل چت بومی:

- مرز واحد اجرای ابزار با approval واقعی وجود دارد → A4 دیگر «چهار مدل را یکی کن» نیست
- gauge تغذیه می‌شود → C2 دیگر «UI بساز» نیست
- ledger وصل است → C7 مسیر دومش را دارد
- plan واقعاً read-only است → A5 قدم‌های بعدی روی پایه‌ی سالم می‌نشیند

## قاعده‌ی موازی‌سازی این موج

| گروه | تسک | فایل اصلی | تداخل |
|---|---|---|---|
| **۳-الف** | A3 | `agentRollbackService.ts` + `checkpointService.ts` (firmware) | — |
| **۳-ب** | C2 | `chatThreadService.ts` + react سایدبار | — |
| **۳-ج** | E1 | `convertToLLMMessageService.ts` | — |
| **۳-د** | M2 | `agentMemoryService.ts` + `neuralInverseAgentService.ts` | — |

هر چهار موازی‌اند. **M1** (`workflowAgentService.ts`) هم موازی است ولی بزرگ‌تر —
اگر ظرفیت پنجمی داری بده، وگرنه موج ۴.

⚠️ **A4 را در این موج نده.** بعد از A7 دامنه‌اش عوض شده و باید اول بازنویسی شود
(بخش پایین همین فایل).

---

## پرامپت ۳-الف — A3: چک‌پوینت فایل (انتخاب منبع، نه ساختن)

```text
تسک: تسک/03-agent-parity/03-file-checkpoints.md را بخوان — مخصوصاً کادر
«اصلاح مارکر ۲۰۲۶-۰۹-۰۸».

این تسک «ساختن» نیست. سه پیاده‌سازی در درخت هست و باید یکی را منبع حقیقت کنی:

1. contrib/neuralInverseFirmware/browser/engine/projectConfig/checkpointService.ts
   کامل: createCheckpoint/rewindTo/forkFrom، fileSnapshots، .inverse/checkpoints/،
   سقف ۵۰، ابزار fw_checkpoint_create. contrib firmware ثبت‌شده است.
2. contrib/chat/browser/chatEditing/chatEditingCheckpointTimeline.ts (+Impl)
   upstream، با undo/redo و persistence.
3. contrib/void/browser/agentRollbackService.ts — فقط messageIndex.
   این باید بازنشسته شود، نه اینکه چهارمی ساخته شود.

اول هر سه را بخوان و **توصیه‌ات را با دلیل بگو**، بعد اجرا کن. توصیه‌ی ممیزی:
upstream برای چت بومی، firmware برای مسیر firmware، بازنشستگی agentRollbackService.

نکته‌ی مهمِ تازه: پل چت بومی حالا مرز واحد اجرای ابزار دارد (کامیت f332502e5dc) —
هر ابزار builtin از approval می‌گذرد. **همان‌جا نقطه‌ی طبیعی ثبت checkpoint است.**
سایدبار این کار را در chatThreadService.ts:1014 برای rewrite_file می‌کند؛ پل هنوز
هیچ checkpoint ای ثبت نمی‌کند. این معیار پذیرش ۳ از تسک A7 است و به این تسک
واگذار می‌شود.

معیار پذیرش: هر نوبت agent که فایل تغییر می‌دهد checkpoint دارد؛ دکمه‌ی Restore
کار می‌کند؛ فایل untracked و باینری در تست پذیرش هستند.
```

## پرامپت ۳-ب — C2: gauge برای سایدبار

```text
تسک: تسک/02-context/02-context-gauge-ui.md را بخوان.

خبر خوب: **نیمی از این تسک دیگر لازم نیست.** برای چت بومی، ویجت
chatContextUsageWidget.ts از قبل وجود دارد و از کامیت 4c1e1c16b56 توسط پل تغذیه
می‌شود. آنجا کاری نمانده.

دامنه‌ی باقی‌مانده فقط **سایدبار Void** است:
- بک‌اند آماده است: getLedgerUsageReport (chatThreadService.ts:469) و
  IContextUsageReport در contextAssembler.
- مصرف‌کننده ندارد.

کار: یک نمایشگر در سایدبار که همان گزارش را نشان دهد. **ویجت بومی را کپی نکن** —
یا از همان کلاس استفاده کن، یا اگر لایه‌بندی اجازه نداد یک نمایش ساده‌ی react با
همان اعداد بساز و در فایل تسک بنویس چرا نشد.

⚠️ عدد روی desktop از Q12 (213acb14709) می‌آید. اگر روی وب تست کردی و عدد صفر بود،
این باگ نیست.

معیار پذیرش: بعد از هر نوبت، درصد پر بودن پنجره درست است؛ بعد از تعویض مدل
مخرج به‌روز می‌شود؛ breakdown (system/rules/tail/pinned) قابل دیدن است.
```

## پرامپت ۳-ج — E1: قواعد AGENTS.md/CLAUDE.md

```text
تسک: تسک/04-ecosystem/01-agents-md-compat.md را بخوان.

**parser ننویس.** هسته‌ی VS Code 1.127 کشف قواعد را کامل دارد:
- promptSyntax/config/promptFileLocations.ts خطوط ۵۲ و ۵۷ و ۷۷:
  AGENTS.md، CLAUDE.md، copilot-instructions.md
- promptSyntax/computeAutomaticInstructions.ts
- سرویس: promptsServiceImpl.ts

الان Void فقط .neuralinverserules را می‌خواند
(convertToLLMMessageService.ts:377). Power Mode جدا AGENTS.md را می‌خواند
(powerModeContextBuilder.ts:65) — یعنی سه پیاده‌سازی موازی.

کار: یکی‌شان کن روی سرویس هسته، و .neuralinverserules را به‌عنوان منبع اضافه
نگه دار (سازگاری عقب‌رو). precedence را صریح مستند کن — متن فعلی تسک در این مورد
متناقض است، پس اول تصمیم را بنویس و تأیید بگیر.

⚠️ تنظیم chat.collectInstructionsInExtension (chat.shared.contribution.ts:1869)
تعیین می‌کند جمع‌آوری در هسته بماند یا به extension برود. قبل از طراحی ببین
پیش‌فرضش چیست و در تصمیمت لحاظ کن.

معیار پذیرش: یک تست که فایل قاعده می‌سازد و اثرش را در پیام ارسالی می‌بیند —
برای هر سه مسیر (سایدبار، چت بومی، workflow).
```

## پرامپت ۳-د — M2: وصل‌کردن recall به مسیر تزریق

```text
تسک: تسک/01-memory/02-vector-retrieval.md — کادر «اصلاح مارکر ۲۰۲۶-۰۹-۰۸».

موتور hybrid کامل و تست‌شده است. مسئله فقط این است که روی مسیر تزریق نیست:
  grep -rn "recallWithReasons" src --include=*.ts | grep -v agentMemoryService.ts
صفر نتیجه. مسیر تولیدی getContextSummary(1500) همگام و واژگانی را صدا می‌زند
(neuralInverseAgentService.ts:320).

کار:
1. جایگزینی getContextSummary با recallWithReasons در مسیر تزریق، با حفظ سقف
   توکن. recallWithReasons ناهمگام است و caller فعلی همگام — این را تمیز حل کن،
   نه با یک .then معلق.
2. backfill بردار برای ورودی‌های قدیمی بدون embedding.
3. انتخاب معتبر provider (الان صرفاً از روی وجود شیء config تصمیم گرفته می‌شود).
4. نمایش «چرا این حافظه آمد» — دلیل تطبیق per-result از قبل در خروجی موتور هست.

اگر بند ۱ باعث شد مسیر همگام بشکند، **دامنه را کوچک کن و فقط بند ۱ را درست
انجام بده**؛ بقیه تسک جدا می‌شود. تایپ‌چک با دستور ۸GB.
```

---

## تسکی که باید قبل از اجرا بازنویسی شود

### A4 — مجوز یکپارچه

دامنه‌ی نوشته‌شده («سه مدل مجوز را یکی کن») دیگر درست نیست:

| مسیر | وضعیت بعد از موج ۱ و ۲ |
|---|---|
| سایدبار Void | `approvalTypeOfBuiltinToolName` + `autoApprove` |
| **پل چت بومی** | ✅ حالا **همان** map را می‌خواند (`f332502e5dc`) |
| Power Mode | `askPermission` جدا (`powerModeProcessor.ts:58`) |
| workflow executor | عمدتاً blocklist |
| هسته | `languageModelToolsConfirmationService` |

یعنی دو مسیر اصلی از قبل یکی شده‌اند. دامنه‌ی جدید باید «Power Mode و workflow را
هم به همان مرز بیاور، و تصمیم بگیر مرجع نهایی نقشه‌ی خودمان است یا سرویس هسته»
باشد. **قبل از دادن به zCode بازنویسی شود.**

---

## چک‌لیست پایان هر تسک (بدون تغییر از موج ۱)

```text
قبل از اینکه بگویی تمام شد:
1. NODE_OPTIONS="--max-old-space-size=8192" npx tsc -p src/tsconfig.json --noEmit
2. npx eslint <فایل‌هایی که عوض کردی>  ← اگر هشدار داشت، اول بپرداز
   (سیاست تأییدشده‌ی مالک: بدهی لینت قبل از کامیت پرداخت می‌شود، نه bypass)
3. node tools/verify.mjs
4. چهار شرط «انجام شده»: فایل ✔ / ثبت ✔ / caller واقعی ✔ / سناریوی قابل‌مشاهده ✔
5. کامیت با پیام انگلیسی روشن، بدون --no-verify. push نکن.
6. مارکر فایل تسک را به‌روز کن و بگو چه چیزی برای تست owner مانده.
```

> **نکته‌ی سیاستی (تصمیم مالک، ۲۰۲۶-۰۹-۰۸):** مسیر «اول بدهی لینت را بپرداز، بعد
> کامیت تمیز» انتخاب شد و در عمل یک باگ واقعی پیدا کرد — قانون
> `code-no-dangerous-type-assertions` داشت پنهان می‌کرد که descriptor مدل‌ها سه
> فیلد لازم (`when`، `configuration`، `managementCommand`) ندارد. `--no-verify`
> فقط با تأیید صریح مالک.

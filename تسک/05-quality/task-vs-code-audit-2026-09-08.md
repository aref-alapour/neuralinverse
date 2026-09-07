# ممیزی کامل تسک‌ها در برابر کدِ امروز (۲۰۲۶-۰۹-۰۸)

- **دامنه:** هر ۵۰ فایل تسک (M1–M6، C1–C7، A1–A6، E1–E3، Q1–Q11، F1–F7، G0–G9)
- **پایه:** `ee636b38a52`، شاخه‌ی `feat/context-ledger`، VS Code **۱.۱۲۷.۰**
- **پرسش مالک:** «کدام تسک‌ها را الان داریم، و کدامشان همین حالا در پروژه به شکل
  **حرفه‌ای‌تر** موجود است؟»

> این سند **منبع سوم حقیقت نمی‌سازد** (قاعده‌ی Q8). مارکر رسمی هر تسک در فایل
> خودش می‌ماند؛ اینجا فقط «واقعیت کد» ثبت می‌شود تا مارکرها اصلاح شوند.

---

## ۰) خلاصه در سه جمله

1. پروژه روی **VS Code 1.127** نشسته و استک چت بومی این نسخه، **۱۳ تسک از ۵۰ تسک
   ما را از قبل و بهتر پیاده کرده است** — checkpoint فایلی، gauge مصرف context،
   plan mode، مجوز یکپارچه، AGENTS.md/CLAUDE.md، skills و hooks، sub-agent، todo،
   ماندگاری append-only گفتگو، و پوسته‌ی background agents.
2. یک پل ثبت‌نشده در نقشه‌ی تسک‌ها وجود دارد: `voidModelProvider.ts` مدل‌های BYOLLM
   ما را **به‌عنوان agent پیش‌فرضِ همان چت بومی** ثبت می‌کند. یعنی آن ۱۳ قابلیت
   بالقوه با موتور خودمان کار می‌کنند، نه با Copilot.
3. در مقابل، `contrib/neuralInverse/` (۱۳۴ فایل) **اصلاً در بیلد ثبت نشده**؛ پس
   چند تسکی که فرض کرده‌اند «زیرساختش هست» (A1، A6، Q1، و صورت‌مسئله‌ی M1) روی
   کدی حساب کرده‌اند که در زمان اجرا بارگذاری نمی‌شود.

---

## ۱) یافته‌ی ساختاری الف — پلِ `voidModelProvider` (در هیچ تسکی ثبت نشده)

`src/vs/workbench/contrib/void/browser/voidModelProvider.ts` (۱۰۵۶ خط، ثبت‌شده در
`void.contribution.ts:68`، فاز `BlockRestore`):

| کاری که می‌کند | خط |
|---|---|
| ثبت vendor + provider مدل‌ها برای model picker بومی | ۸۳۷–۸۴۲ |
| ثبت agent پیش‌فرض `isDefault: true` با مودهای Ask/Edit/Agent | ۸۴۹–۸۶۷ |
| حلقه‌ی agentic کامل با tool-call و `ChatToolInvocation` استریم | ۴۵۴–۷۴۵ |
| برداشتن ابزارهای MCP/کوپایلت از `ILanguageModelToolsService` | ۴۸۲ |
| خاموش‌کردن گیت‌های entitlement کوپایلت (BYOK) | ۸۲۳–۸۲۶ |

```bash
grep -n "registerAgentImplementation\|registerLanguageModelProvider" \
  src/vs/workbench/contrib/void/browser/voidModelProvider.ts
```

**معنایش برای نقشه‌ی تسک‌ها:** جدول «Cursor Parity» در README می‌گوید Plan mode ❌،
Checkpoints ⚠️، Skills/Hooks ❌، Usage ❌. این‌ها **برای سایدبار Void** درست است،
ولی برای چتِ بومی — که همین حالا با موتور ما کار می‌کند — نادرست است.

## ۲) یافته‌ی ساختاری ب — `contrib/neuralInverse` در بیلد نیست

```bash
grep -rn "neuralInverse\.contribution" src build out   # → صفر نتیجه در هر سه
```

**این فقط مسئله‌ی سورس نیست:** جست‌وجو در `out/` (خروجی کامپایل‌شده) هم صفر است،
یعنی در باندلِ ساخته‌شده هم بارگذاری نمی‌شود.

`neuralInverse.contribution.ts` تنها نقطه‌ای است که این‌ها را ثبت می‌کند و **هیچ‌کس
import اش نمی‌کند**:

| ماژول | تسک وابسته | نتیجه |
|---|---|---|
| `backgroundAgentService.ts` + `backgroundAgentPanel.ts` + `agentManagerPart.ts` | **A1** | پنل و سرویس background agent هرگز بارگذاری نمی‌شوند |
| `composer/composerModule.ts` | **A6** | composer در زمان اجرا وجود ندارد |
| `executor/budgetTracker.ts` | **Q1** | جدول قیمت ۸-مدلی اصلاً اجرا نمی‌شود |
| `workflowAgentService.ts` | **M1** (صورت‌مسئله) | «Map در RAM» که M1 می‌خواهد رفع کند، کد مرده است |
| `modelManagement/*`، `powerMode.contribution.js` | — | مارکت‌پلیس مدل و powerMode هم مرده‌اند |

> **اصلاح مهم (بند ۸):** جدول بالا فقط برای ردیف‌هایی معتبر است که **تنها** از
> فایل contribution ثبت می‌شوند. import ترانزیتی جدا حساب می‌شود:
>
> ```bash
> grep -rn "workflowAgentService.js" src --include=*.ts | grep -v contrib/neuralInverse/
> # → src/vs/workbench/contrib/void/browser/toolsService.ts:34
> ```
>
> `toolsService.ts` (در contrib **ثبت‌شده‌ی** void) به‌صورت ایستا
> `IWorkflowAgentService` را import می‌کند، و آن هم `orchestrator/workflowOrchestrator`
> و `executor/agentExecutor` (و از آن طریق `budgetTracker`) را بالا می‌آورد. پس این
> سه **بارگذاری می‌شوند**. ردیف Q1 بالا از این بابت اصلاح شد.
>
> آنچه واقعاً مرده می‌ماند (صفر مسیر رسیدن، تأیید شد): `backgroundAgentService` +
> `backgroundAgentPanel` + `backgroundAgentCommands` + `agentManagerPart` (A1)،
> `composer/composerModule` (A6)، `agentStoreService`، سینگلتون‌های
> `modelManagement`، و `powerMode.contribution` — یعنی **ثبت** قابلیت‌های
> Power Mode (سرویس `powerBusService` خودش ترانزیتی بالا می‌آید).

علاوه بر این، **موتور context** هم زنده است؛ Void با `await import(...)` پویا
صدایش می‌زند (`toolsService.ts:297–313, 1149–1199`) — همان چیزی که ممیزی C1 دیده بود.

> ⚠️ این با Q10 فرق دارد: Checks/Enclave **عمداً** از `tsconfig` و workbench کنار
> گذاشته شده‌اند و مستند است؛ `neuralInverse` کامپایل می‌شود ولی **ثبت نمی‌شود** —
> که یعنی هیچ گیتی این را نمی‌گیرد. آیتم جدید برای Q8.

---

## ۳) جدول کامل ۵۰ تسک

ستون «حرفه‌ای‌تر در پروژه» = آیا نسخه‌ی بهتری از این تسک **همین الان در درخت کد**
هست (معمولاً از upstream 1.127) یا نه.

### ۳-۱) حافظه (M)

| تسک | مارکر سند | واقعیت کد | حرفه‌ای‌تر در پروژه | توصیه |
|---|---|---|---|---|
| **M1** ماندگاری گفتگو | 🔴 | thread های Void **از قبل** روی `THREAD_STORAGE_KEY` ذخیره می‌شوند (`chatThreadService.ts:761–775`) | ✅ **بله** — `common/model/chatSessionStore.ts` + `chatSessionOperationLog.ts` + `objectMutationLog.ts`: op-log افزایشی روی دیسک با append واقعی | **تسک را بازنویسی کن**: صورت‌مسئله (Map در RAM) به کد مرده اشاره دارد |
| **M2** بازیابی برداری | 🟡 | ⚠️ **اصلاح‌شده (بند ۸):** موتور کامل است (`agentMemoryService.ts`، سه مود `hybrid`/`lexical-promoted`/`lexical`) **ولی روی مسیر تزریق نیست**: `recallWithReasons` صفر caller خارجی دارد؛ مسیر تولیدی `getContextSummary(1500)` همگام و واژگانی را صدا می‌زند (`neuralInverseAgentService.ts:320`) | ❌ | 🟡 بماند — ادعای ✅ نادرست است؛ کارِ مانده «وصل‌کردن recall به تزریق» است نه فقط تست |
| **M3** ثبت خودکار + UI | 🔴 | تأیید شد: هیچ `autoCapture`/`consolidate` ای نیست | ⚠️ نیمه — `aiCustomization*` (ویرایشگر مدیریت instructions) الگوی UI را می‌دهد | باز |
| **M4** @Docs | 🔴 | تأیید شد: هیچ چیز | ❌ | باز |
| **M5** Context Ledger | 🟡 | زنده: `contextLedgerService`, `ledgerJournalCore`, `ledgerPolicy`, `ledgerBoundary`, `episodeSummarizer`, `workingBriefBuilder`, `ledgerRecallContrib` | ⚠️ upstream op-log هم‌پوشانی دارد ولی اپیزود/brief/recall ندارد — **مزیت ما** | ادامه؛ فقط live-patch + تست |
| **M6** سخت‌سازی Ledger | ✅ | تأیید شد | — | — |

### ۳-۲) Context (C) — بر پایه‌ی [ممیزی امروز](../02-context/audit-2026-09-08.md)

| تسک | مارکر سند | واقعیت کد | حرفه‌ای‌تر در پروژه | توصیه |
|---|---|---|---|---|
| **C1** سیم‌کشی موتور | 🟡 | شش ابزار `context_*` وصل | ❌ | `contextBudgets` + ماتریس مانده |
| **C2** نمایشگر مصرف | 🟡 بک‌اند | بک‌اند `IContextUsageReport` هست، UI صفر | ✅ **بله و کامل** — `browser/widgetHosts/viewPane/chatContextUsageWidget.ts` (حلقه‌ی درصدی) + `chatContextUsageDetails.ts`، وصل در `chatInputPart.ts:2869`، تست هم دارد | **کار UI را ننویس** — یا از همان استفاده کن یا ویجت را برای سایدبار وام بگیر |
| **C3** @-mentions | 🟡 | `@file`/`@folder` ارثی Void | ✅ **بله** — `browser/attachments/` (۱۰ فایل: `chatDynamicVariables`, `chatContextPickService`, `chatImplicitContext`, `chatScreenshotContext`, …) | دامنه را به «@symbol/@web برای سایدبار» کوچک کن یا کلاً به چت بومی مهاجرت کن |
| **C4** Pinned | 🟡 | `pinnedBlocks` در assembler | ⚠️ نیمه — `chatAttachmentModel` معادلِ pin دارد | کوچک‌شده |
| **C5** Repo map | 🔴 | تأیید شد: بدون امتیازدهی | ❌ | اولویت پایین (ابزار `context_*` جایگزینِ عملی) |
| **C6** auto-context | 🔴 | مسیر خودکار نیست | ⚠️ `chatImplicitContext.ts` معادل ضعیفش | معلق تا بعد از C2 |
| **C7** Compaction UX | 🟡 | `conversationCompactor.ts` هست، UX صفر | ⚠️ نیمه — `/compact` upstream فقط برای agentHost است (`chatActions.ts:1103–1119`)، ولی `tools/toolResultCompressor.ts` لایه‌ی مکانیکی را دارد | باز، ولی از دو قطعه‌ی بالا وام بگیر |

### ۳-۳) هم‌ترازی Agent (A)

| تسک | مارکر سند | واقعیت کد | حرفه‌ای‌تر در پروژه | توصیه |
|---|---|---|---|---|
| **A1** background agents | 🔴 | سرویس و پنل ما **بارگذاری نمی‌شوند** (بخش ۲) | ✅ **بله و خیلی بزرگ‌تر** — `browser/agentSessions/` (۱۹ فایل) + `agentSessions/agentHost/` (۱۷ فایل) + لایه‌ی کامل `vs/sessions/` (۲۳ contrib) + `contrib/remoteCodingAgents` | **تسک را عوض کن**: به‌جای ساختن، agent ما را به‌عنوان session provider ثبت کن. تأیید شد که هنوز نکرده‌ایم: `grep registerChatSessionItemProvider contrib/void` → صفر |
| **A2** native tool calling | 🔴 | Void هنوز XML-block دارد (`extractXMLToolsWrapper`) | ✅ **بله** — مسیر بومیِ tool-call در `voidModelProvider.ts:552–731` از قبل کار می‌کند (`toolCalling: true` در متادیتای مدل) | دامنه فقط «سایدبار Void» است، نه کل محصول |
| **A3** checkpoint فایل | 🔴 | ⚠️ **اصلاح‌شده (بند ۸):** علاوه بر `agentRollbackService.ts` (فقط `messageIndex`)، یک سرویس چک‌پوینت فایلیِ کامل در contrib **ثبت‌شده‌ی** firmware هست: `neuralInverseFirmware/browser/engine/projectConfig/checkpointService.ts` با `createCheckpoint`/`rewindTo`/`forkFrom`، `fileSnapshots` کامل، `.inverse/checkpoints/`، سقف ۵۰ و ابزار `fw_checkpoint_create` | ✅ **بله، دو تا** — یکی خودمان (بالا) و یکی upstream: `chatEditing/chatEditingCheckpointTimeline.ts` (+`Impl`) و `agentHostSnapshotController.ts` | **ننویس** — انتخاب کن کدام منبع حقیقت است و وصلش کن |
| **A4** مجوز یکپارچه | 🔴 | سه مدل پراکنده در Void | ✅ **بله** — `tools/languageModelToolsConfirmationService.ts`, `chatPermissionStorageKeys.ts`, `chatPermissionWarnings.ts`, `agentSessionApprovalModel.ts`, `agentHostPermissionUiContribution.ts`, `chatExternalPathConfirmation.ts`, `chatUrlFetchingConfirmation.ts` | **ننویس** — یکی کن روی همین |
| **A5** Plan mode | 🔴 | Void ندارد | ✅ **بله** — `builtinTools/reviewPlanTool.ts` + `browser/planReviewFeedback/` + `planAgentDefaultModel.ts` + `AgentSessionMode = 'interactive' \| 'plan' \| 'autopilot'` (`constants.ts:140`) | **ننویس** |
| **A6** composer | 🟡 | `neuralInverseSubAgentService` در Void زنده؛ composer در NI مرده | ✅ **بله** — `builtinTools/runSubagentTool.ts` | تسک را به «الگوی planner/worker روی runSubagent» تبدیل کن |

### ۳-۴) اکوسیستم (E)

| تسک | مارکر سند | واقعیت کد | حرفه‌ای‌تر در پروژه | توصیه |
|---|---|---|---|---|
| **E1** AGENTS.md/CLAUDE.md | 🔴 | Void فقط `.neuralinverserules` | ✅ **بله و کامل** — `promptSyntax/config/promptFileLocations.ts:52,57,77` (`AGENTS.md`, `CLAUDE.md`, `copilot-instructions.md`) + `computeAutomaticInstructions.ts` + `aiCustomizationManagementEditor` | **ننویس** — فقط `.neuralinverserules` را به‌عنوان منبع پنجم اضافه کن |
| **E2** Skills / Hooks | 🔴 | Void ندارد | ✅ **بله، هر دو** — skills: `promptFileLocations.ts:163–165` شامل `.claude/skills`، `.agents/skills`، `.github/skills` + ده skill آماده در `vs/sessions/skills/`؛ hooks: `promptSyntax/hookCompatibility.ts` و `hookClaudeCompat.ts` | **ننویس** — دامنه به «skill های اختصاصی خودمان» کوچک شود |
| **E3** CLI headless | 🔴 | تأیید شد: `cli/` همان CLI استاندارد tunnel/serve است؛ حالت `-p` ندارد | ❌ (فقط `copilotCliEventsUri.ts` که CLI **دیگران** را میزبانی می‌کند) | **واقعاً باز** |

### ۳-۵) کیفیت (Q)

| تسک | مارکر سند | واقعیت کد | حرفه‌ای‌تر در پروژه | توصیه |
|---|---|---|---|---|
| **Q1** هزینه/Usage | 🔴 | ⚠️ **اصلاح‌شده (بند ۸):** ادعای «هاردکد `$0.0000`» **باطل است**. `getSessionCost` (`chatThreadService.ts:580–604`) واقعی است: usage واقعی ledger + نسبت کالیبراسیون + قیمت از `getModelCapabilities`؛ آن `'$0.0000'` فقط گاردِ «مدلی انتخاب نشده» است. جدول ۸-مدلی `budgetTracker.ts` هم فقط برای مسیر workflow است | ⚠️ نیمه — `languageModelStats.ts` + `chatStreamStats.ts` شمارش دارند، جدول قیمت ندارند | باز، ولی کوچک‌تر: داشبورد + usage مسیر desktop + قیمت per-call |
| **Q2** بهداشت کدبیس | 🔴 | تأیید شد: ۷ فایل `.bak` زنده (`chatThreadService.ts.bak{,2,3}`، `powerModeTerminalHost.ts.bak{,2,3}`، `AgentNetworkViz.tsx.bak`) + contrib مرده‌ی بخش ۲ | ❌ | باز — دامنه بزرگ‌تر از تصور |
| **Q3** یکپارچه‌سازی استک‌ها | 🔴 | حالا **چهار** استک است نه سه: Void، NI (مرده)، upstream chat، و `vs/sessions` | ❌ | **اولویت را بالا ببر** — این سند خودش نیمی از فاز ۰ است |
| **Q4** یکپارچگی live-patch | ✅ | — | — | — |
| **Q5** هارنس verify | ✅ | — | — | — |
| **Q6** قطع stream | ✅ | `common/streamIntegrity.ts` زنده | — | — |
| **Q7** کمپین بیلد | ✅ | — | — | — |
| **Q8** رجیستر بدهی | 🟡 | زنده | — | دو آیتم جدید از این سند (بخش ۵) |
| **Q9** TLS | 🔴 | **تأیید شد، هنوز باز:** `[Environment]::GetEnvironmentVariable('NODE_TLS_REJECT_UNAUTHORIZED','User')` → `0`، و `NODE_EXTRA_CA_CERTS` خالی | ❌ | **P0 امنیتی — بالاترین اولویت واقعی این فهرست** |
| **Q10** contrib های نساخته | 🔴 | تأیید شد: `src/tsconfig.json` هر دو را exclude کرده + خطوط ۲۱–۲۲ workbench کامنت‌اند | ❌ | باز |
| **Q11** بدهی lint | 🔴 | فایل uncommitted در `git status` | ❌ | باز |

### ۳-۶) الگوهای freebuff (F)

| تسک | مارکر سند | واقعیت کد | حرفه‌ای‌تر در پروژه | توصیه |
|---|---|---|---|---|
| **F1** ابزار ویرایش قطعی | 🔴 | Void: `read_file`/`edit_file`/`rewrite_file` — بدون `str_replace` | ⚠️ نیمه — `builtinTools/editFileTool.ts` ابزار «code-block apply» است، نه primitive رشته‌ای | **واقعاً باز** و هنوز ارزشمند |
| **F2** compaction مکانیکی | 🔴 | ندارد | ⚠️ نیمه — `tools/toolResultCompressor.ts` دقیقاً لایه‌ی فشرده‌سازی خروجی ابزار است | دامنه کوچک‌تر شد |
| **F3** بازیابی stream | 🟡 | `streamIntegrity.ts` (بند الف/ب بسته با Q6) | ❌ | فقط بند ج (توکن‌شمار محلی + cache breakpoint) |
| **F4** knowledge/LESSONS | 🔴 | ندارد | ✅ **skills** کاملاً موجود (E2)؛ حلقه‌ی LESSONS نه | دامنه به LESSONS محدود شود |
| **F5** propose/steer/ask | 🔴 | `userInputRequestService.ts` در Void | ✅ **بله** — `askQuestionsTool.ts`, `reviewPlanTool.ts`, `manageTodoListTool.ts` + `chatTodoListService.ts` + ویجت `chatTodoListWidget.ts`, `taskCompleteTool.ts`, `confirmationTool.ts` | فقط best-of-N باز می‌ماند |
| **F6** ترمینال + XML | 🟡 | `commandSanitizer.ts`, `terminalCommandClassifier.ts`, `terminalToolService.ts` | ✅ برای بند الف — `tools/terminalToolIds.ts` + auto-approve بومی | بند ب (کانال XML) با A2 بی‌موضوع می‌شود |
| **F7** eval harness | 🔴 | ندارد | ❌ | باز |

### ۳-۷) موتور گراف ComfyUI (G)

| تسک | مارکر سند | واقعیت کد | توصیه |
|---|---|---|---|
| **G0–G9** | 🟡/🔴 | **تأیید شد: پوشه‌ی `workflow-engine/` وجود ندارد.** `find src -iname "*workflow-engine*"` → صفر. تنها چیز موجود، `workflowAgentService.ts` در contrib مرده است | کل دسته دست‌نخورده. با توجه به بخش ۲، حتی نقطه‌ی اتصالِ فرض‌شده (composer/executor) هم زنده نیست |

---

## ۴) جمع‌بندی عددی

| دسته | تعداد | ✅ بسته | 🟡 نیمه | 🔴 باز | **بی‌موضوع/بازتعریف چون upstream دارد** |
|---|---|---|---|---|---|
| M | ۶ | ۱ | ۳ | ۲ | ۱ (M1) |
| C | ۷ | ۰ | ۵ | ۲ | ۲ (C2، C3) |
| A | ۶ | ۰ | ۱ | ۵ | **۵ (A1، A2، A3، A4، A5)** + A6 بازتعریف |
| E | ۳ | ۰ | ۰ | ۳ | **۲ (E1، E2)** |
| Q | ۱۱ | ۴ | ۱ | ۶ | ۰ |
| F | ۷ | ۰ | ۳ | ۴ | ۲ (F5، F6-الف) |
| G | ۱۰ | ۰ | ۲ | ۸ | ۰ |
| **جمع** | **۵۰** | **۵** | **۱۵** | **۳۰** | **۱۳ کامل + ۵ نیمه** |

**ترجمه‌ی مدیریتی:** حدود **۲۶٪ از بک‌لاگ (۱۳ تسک) کار مرده است** — نه اینکه
انجام نشده، بلکه upstream نسخه‌ی بهتری دارد که همین الان در درخت است و agent
خودمان هم به آن وصل است. حدود ۱۰٪ دیگر باید دامنه‌شان کوچک شود.

---

## ۵) دو آیتم جدید برای رجیستر Q8

- **N5 — `contrib/neuralInverse` کامپایل می‌شود ولی ثبت نمی‌شود.**
  شدت 🔴. ۱۳۴ فایل که typecheck سبز می‌گیرند و هیچ‌وقت اجرا نمی‌شوند؛ A1/A6/Q1 روی
  آن‌ها برنامه‌ریزی شده‌اند. معیار پذیرش: یا `neuralInverse.contribution.js` به
  `workbench.common.main.ts` اضافه شود، یا مثل Q10 صریحاً exclude و مستند شود، و
  در هر دو حالت یک گیت در `tools/verify.mjs` که «contrib بدون importer» را می‌گیرد.

- **N6 — نقشه‌ی تسک‌ها از upstream عقب افتاده.**
  شدت 🟠. جدول Cursor-parity در README در برابر سایدبار Void نوشته شده، نه در برابر
  چت بومیِ ۱.۱۲۷ که agent ما در آن پیش‌فرض است. معیار پذیرش: ستون «معادل upstream»
  به جدول README اضافه شود و ۱۳ ردیفِ بخش ۴ علامت بخورند.

---

## ۶) توصیه‌ی ترتیب اجرا (بازنویسی «دسته‌ی ۱»)

1. **Q9** — تنها P0 امنیتیِ واقعاً باز، و کد نمی‌خواهد.
2. **N5** — تصمیم درباره‌ی contrib مرده. تا این بسته نشود، A1/A6/Q1 روی شن ساخته می‌شوند.
3. **A3 + A4 + A5 + E1 + E2 با وصل‌کردن، نه نوشتن** — پنج تسک با کسری از برآورد اولیه.
4. **C2** — یا ویجت بومی را در سایدبار وام بگیر یا سایدبار را کنار بگذار.
5. **Q3** فاز ۰ — با چهار استک، هر تصمیم دیگری بدون این سند سه‌بار پیاده می‌شود.

## ۸) داوری بین سه ممیزی مستقل (۲۰۲۶-۰۹-۰۸)

سه ممیزی جدا روی همین کامیت انجام شد (این سند + دو گزارش دیگرِ مالک). هرجا اختلاف
داشتند، ادعا مستقیماً با کد چک شد. نتیجه:

| موضوع | این سند | گزارش A | گزارش B | **داوری با کد** |
|---|---|---|---|---|
| **A3** چک‌پوینت فایلی خودمان | «فقط messageIndex» ❌ | «سرویس کامل در firmware» ✅ | «فقط rollback + upstream» ❌ | **A درست است.** `neuralInverseFirmware/.../checkpointService.ts` با `fileSnapshots`، `rewindTo`، `forkFrom`، `.inverse/checkpoints/`، سقف ۵۰، ابزار `fw_checkpoint_create` — و firmware در `workbench.common.main.ts:17` **ثبت شده** |
| **Q1** هاردکد `$0.0000` | «هاردکد زنده» ❌ | «هزینه واقعی است» ✅ | «هزینه واقعی است» ✅ | **A و B درست‌اند.** خط ۵۸۲ فقط گاردِ no-model است؛ `getSessionCost` واقعی است |
| **M2** آیا ✅ است؟ | 🟡 | «باید ✅ شود» ❌ | «به مسیر تزریق وصل نیست» ✅ | **B درست است.** `recallWithReasons` صفر caller؛ مسیر تولیدی `getContextSummary(1500)` است |
| **contrib مرده** | «کل contrib مرده» — بیش‌ازحد قطعی | «backgroundAgent مرده» ✅ | «نتیجه‌گیری کلی نکنید» ✅ | **B از نظر روشی درست است.** بند ۲ اصلاح شد: workflowAgentService/orchestrator/executor ترانزیتی زنده‌اند؛ backgroundAgent/composer/agentManager/powerMode.contribution مرده |
| **A5** plan mode | «upstream دارد» | «فلگ خوانده نمی‌شود — فیک است» | «مصرف‌کننده ندارد» | **A و B درست‌اند.** `getThreadPlanMode` فقط تعریف + پیاده‌سازی دارد، صفر caller |
| **A1** باگ ویندوز | ندیدم | «`/tmp/ni-bg-` هاردکد» ✅ | — | **A درست است** (`backgroundAgentService.ts:62`) — البته چون سرویس ثبت نشده، باگ نهفته است |
| **Q9** TLS | باز ✅ | باز ✅ | باز ✅ | **هر سه درست** — `User=0` تأیید شد |
| **Q2** فایل‌های `.bak` | ۷ ✅ | ۷ ✅ | + یک `.js` مرده ✅ | **هر سه درست.** `contrib/void/neuralInverse/browser/backgroundAgentService.js` (۲۴۵ بایت) هم هست |
| **G** موتور گراف | «هیچ‌چیز» | «هیچ‌چیز» | «composer پایه هست» ✅ | **B دقیق‌تر است:** `workflow-engine/` نیست، ولی composer/orchestrator/edgeValidator پایه‌ی قابل‌استفاده‌اند |

**دو چیزی که هیچ‌کدام از سه ممیزی نتوانستند تأیید کنند** (و نباید به‌عنوان انجام‌شده
ثبت شوند): ادعای ۱۰M توکن و p95 زیر ۱۵۰ms برای Ledger، و وضعیت PR ۱۳۹ — سرور
GitHub در این نشست authorize نشده است.

**نکته‌ی روشیِ قابل ثبت (تکمیل درس ممیزی C1):** «grep چیزی پیدا نکرد» شاهدِ نبودن
نیست — و «فایل contribution import نشده» هم شاهدِ مرده‌بودنِ کل پوشه نیست. برای
این کدبیس سه تله تکرار شد: نام‌های snake_case، وصل‌شدن در لایه‌ای غیر از انتظار،
و **import ترانزیتی از contrib دیگر**.

## ۹) اقدامات اعمال‌شده (۲۰۲۶-۰۹-۰۸، بعد از داوری)

**مارکرهای اصلاح‌شده:**

| تسک | از | به | دلیل |
|---|---|---|---|
| M1 | 🔴 (فایل) / 🟡 (README) | **🟡** | دریفت R1 بسته شد؛ ذخیره‌سازی حل شده، ادامه‌ی نشست نه |
| M2 | 🔴 شروع نشده | **🟡** | موتور hybrid کامل، ولی `recallWithReasons` صفر caller |
| A3 | 🔴 | **🟡** | دو پیاده‌سازی کامل داریم؛ برآورد M→S/M و دامنه شد «اتصال» |
| A5 | 🔴 P2 | **🔴 P1** | فلگ plan هرگز خوانده نمی‌شود — تله‌ی ایمنی، نه feature غایب |
| Q1 | 🔴 «هاردکد `$0.0000`» | **🟡** | صورت‌مسئله باطل بود؛ `getSessionCost` واقعی است |
| G6 | 🟡 | **🔴** | مارکر به صف background agent اشاره داشت، نه صف گراف |
| A1، A6 | 🔴 / 🟡 | بدون تغییر | مارکر درست بود، ولی صورت‌مسئله اصلاح شد (ثبت‌نشدن) |

**تسک‌های جدید:**

| تسک | اولویت | چرا اضافه شد |
|---|---|---|
| [A7](../03-agent-parity/07-native-chat-bridge.md) | **P0** | پل چت بومی در هیچ تسکی ثبت نبود؛ سخت‌سازی‌اش هفت تسک دیگر را از «ساختن» به «وصل‌کردن» تبدیل می‌کند |
| [Q12](12-desktop-usage-parity.md) | **P0** | `usage` روی مسیر desktop نمی‌رسد — ورودی Q1، M6 و C2 را خالی می‌کند |
| [Q13](13-contribution-registration-gate.md) | **P0** | کدی که کامپایل می‌شود و ثبت نمی‌شود؛ بلاک‌کننده‌ی A1/A6 + گیت خودکار |

**ساختاری:** قاعده‌ی قطعی وضعیت و «چهار شرط انجام‌شده» به README اضافه شد (بستن
N3)؛ جدول Cursor-parity با هشدار بازنگری و ردیف‌های اصلاح‌شده به‌روز شد؛ دسته‌ی ۰
(پایه‌ریزی) جایگزین صدر ترتیب اجرا شد؛ N11/N12/N13 به رجیستر Q8 اضافه و N3/N5/N7
خانه‌دار شدند.

**شمارش جدید:** `۵ ✅ / ۱۵ 🟡 / ۳۳ 🔴` روی ۵۳ فایل تسک (۵۰ + سه تسک جدید).

```bash
for f in $(find "تسک" -name "*.md" -not -name "README.md" -not -name "00-*" \
  -not -name "audit-*" -not -name "project-status*" -not -name "verify-handoff*" \
  -not -name "task-vs-code-audit*" -not -name "full-typecheck*" -not -name "editor-tools-audit*"); do \
  grep -m1 -o "وضعیت:\*\* *[^ |]*" "$f"; done | sort | uniq -c
```

## ۷) بازتولید

```bash
git rev-parse --short HEAD                      # ee636b38a52
grep -rn "neuralInverse\.contribution" src build out   # صفر در هر سه → بخش ۲
grep -n "registerAgentImplementation" src/vs/workbench/contrib/void/browser/voidModelProvider.ts
ls src/vs/workbench/contrib/chat/common/tools/builtinTools/
grep -n "AGENT_MD_FILENAME\|CLAUDE_MD_FILENAME\|claude/skills" \
  src/vs/workbench/contrib/chat/common/promptSyntax/config/promptFileLocations.ts
find src -iname "*workflow-engine*"              # صفر → دسته‌ی G
find src -name "*.bak*"                          # ۷ فایل → Q2
```

```bash
# بند ۸ — داوری بین سه ممیزی
grep -rn "workflowAgentService.js" src --include=*.ts | grep -v contrib/neuralInverse/
grep -rn "getThreadPlanMode" src --include=*.ts --include=*.tsx   # ۲ نتیجه، صفر caller → A5
grep -n "tmp/ni-bg" src/vs/workbench/contrib/neuralInverse/browser/backgroundAgentService.ts
grep -rn "recallWithReasons" src --include=*.ts | grep -v agentMemoryService.ts  # صفر → M2
grep -n "fw_checkpoint_create" src/vs/workbench/contrib/neuralInverseFirmware/browser/engine/agentTools/firmwareAgentToolService.ts
sed -n '580,584p' src/vs/workbench/contrib/void/browser/chatThreadService.ts     # گارد no-model → Q1
```

```powershell
[Environment]::GetEnvironmentVariable('NODE_TLS_REJECT_UNAUTHORIZED','User')   # 0 → Q9 باز
```

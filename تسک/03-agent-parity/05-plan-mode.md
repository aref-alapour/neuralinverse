# A5 — حالت Plan درجه‌یک (Plan Mode)

- **اولویت:** ~~P2~~ → **P1 (ایمنی)** | **برآورد:** M | **وضعیت:** 🟡 — **اولین قدم (گارد در مرز `callTool`) روی سورس انجام و commit شد (2026-09-08، ۸ تست standalone سبز)؛ پورت live-patch، تست owner و بقیه‌ی تسک باز** | **وابستگی:** A2
- **هم‌ارز در Cursor:** Toggle Plan — مدل اول برنامه می‌دهد، تو تأیید می‌کنی، بعد اجرا

> **اصلاح مارکر ۲۰۲۶-۰۹-۰۸ — این یک تلهٔ ایمنی است، نه فقط feature غایب.**
> ابزارهای `plan_mode_enter` / `plan_mode_exit` وجود دارند و فلگ per-thread را
> set می‌کنند، ولی `getThreadPlanMode` **صفر caller** دارد — فقط تعریف اینترفیس و
> پیاده‌سازی. یعنی کاربر «Plan mode» را روشن می‌کند، UI تأیید می‌گیرد، و **هیچ
> write ای بلاک نمی‌شود.**
>
> ```bash
> grep -rn "getThreadPlanMode" src --include=*.ts --include=*.tsx
> # فقط ۲ خط: toolsService.ts:174 (تعریف) و :203 (پیاده‌سازی) — هیچ مصرف‌کننده‌ای
> ```
>
> به همین دلیل اولویت از P2 به **P1** رفت: قابلیتی که ادعای مهار می‌کند و مهار
> نمی‌کند، از نبودنش بدتر است.
>
> **اولین قدم (S، همین حالا و مستقل از A2):** یا `getThreadPlanMode` را در مرز
> اجرای ابزار enforce کن، یا هر دو ابزار را حذف کن تا کسی به آن‌ها اتکا نکند.
> **قدم دوم:** `PlanAgentProvider` upstream (`extensions/copilot/src/extension/agents/vscode-node/planAgentProvider.ts`)
> و مود `'plan'` در `constants.ts:140` را مبنا بگیر — از صفر ننویس. توجه: پل
> `voidModelProvider` هم فهرست ابزار را کامل می‌دهد و محدودیت mode را اعمال
> نمی‌کند؛ آن بخش در [A7](07-native-chat-bridge.md) بسته می‌شود.

> ### ثبت پیشرفت 2026-09-08 — فقط «اولین قدم» انجام شد (طبق قاعده‌ی وضعیت: G1+G2 سبز و G3/G4 باز، پس 🟡)
>
> **مسیر (a) enforce انتخاب شد** — چون مرز واحد پیدا شد: هر دو مسیر مصرف‌کننده‌ی
> ابزارهای builtin از همان نقشه عبور می‌کنند — سایدبار چت (`chatThreadService.ts:1057`)
> و پل چت بومی (`voidModelProvider.ts:711`) هر دو `toolsService.callTool[toolName](...)`
> را صدا می‌زنند. تابع `withPlanModeGuard` در `toolsService.ts` کل نقشه‌ی callTool را
> می‌پیچد و در حالت plan هر ابزار نوشتن/اجرایی با پیام روشن برای مدل reject می‌شود
> (throw → هر دو caller آن را به نتیجه‌ی tool_error تبدیل می‌کنند). مسیر (b) حذف در
> محدوده‌ی مجاز این قدم غیرممکن بود: ابزارها/فلگ در `voidModelProvider.ts` (خطوط ۳۱۴-۳۴۲)،
> `toolsServiceTypes.ts`، `prompts.ts` و `neuralInverseAgentTypes.ts` هم ارجاع دارند.
>
> - **فقط یک فایل سورس تغییر کرد:** `src/vs/workbench/contrib/void/browser/toolsService.ts`
>   (گارد + سیم‌کشی؛ `voidModelProvider.ts` عمداً دست‌نخورده — مال A7).
> - **تست:** `src/vs/workbench/contrib/void/test/node/planModeGuard.test.ts` — ۸/۸ سبز
>   (اثبات می‌کند ابزار نوشتن در plan اجرا *نمی‌شود*، ابزار فقط‌خواندنی و `plan_mode_exit`
>   آزادند، و بعد از خروج از plan دوباره نوشتن برمی‌گردد). اجرا با همان مکانیک
>   `tools/run-tests-standalone.mjs` در temp (بدون کامپایل کامل)؛ typecheck با گزینه‌های
>   strict سورس روی هر دو فایل جدید سبز. بعد از آن به لیست `files` در
>   `tools/typecheck-slice.json` اضافه شد (تایپ‌چک اسلایس)؛ افزودن به لیست `tests`
>   (اجرای standalone) نیازمند stub های DOM در `run-tests-standalone.mjs` است — دست owner.
> - **ابزارهای بلاک‌شده (۱۸):** `write`, `edit`, `rewrite_file`, `edit_file`,
>   `multi_replace_file_content`, `create_file_or_folder`, `delete_file_or_folder`,
>   `generate_document`, `bash`, `run_command`, `run_background_command`,
>   `run_persistent_command`, `open_persistent_terminal`, `send_command_input`,
>   `kill_persistent_terminal`, `spawn_agent`, `query_ni_agent` — spawn/query هم بلاک شدند
>   چون agent های زیرمجموعه دسترسی write/edit/bash دارند و مهار را دور می‌زدند.
> - **پوشش ندارد (خارج از این قدم):** ترمینال Power Mode (اجراگر جدا در
>   `powerModeService.ts:405`؛ ابزارهای `enter/exit_plan_mode` آن فقط metadata برمی‌گردانند)،
>   ابزارهای MCP، و ابزارهای `internalToolService`.
> - **محدودیت شناخته‌شده:** `_currentThreadId` mutable است؛ اجرای هم‌زمان دو thread
>   می‌تواند فلگ را غلط بخواند (نقص ساختاری خودِ ابزارهای plan) — برای قدم دوم/A7.
> - **بدهی لینت فایل (موج ۱):** `toolsService.ts` هیچ هدر کپی‌رایت نداشت (اضافه شد) و
>   ~۶۰۸ مورد auto-fixable در commit جدا پرداخت شد؛ ~۳۱ مورد سخت (خانواده‌ی
>   `as any` روی dispatch ابزار — همان «گام سنگین» [Q11](../05-quality/11-lint-debt-core-chat-files.md))
>   می‌ماند. تا پرداخت نشود، هر commit این فایل `--no-verify` می‌خواهد. تست
>   `planModeGuard.test.ts` هم دو هشدار layering دارد (test/node → browser) —
>   الگوی رایج همه‌ی تست‌های موجود این پوشه (مثلاً chatThreadService.test.ts با ۳۰ هشدار).
> - **باقی‌مانده تا ✅:** افزودن تست به لیست `tests` ی standalone (نیازمند stub DOM؛
>   تایپ‌چکش از الان در slice هست)؛ پورت live-patch + تست owner روی نسخه‌ی نصبی؛ بعد قدم دوم (PlanAgentProvider upstream)،
>   toggle در UI، کارت برنامه و معیارهای پذیرش چهارگانه پایین همین فایل.

## هدف
Plan به‌عنوان یک حالت first-class: toggle در chat/agent → ابزارها فقط-خواندنی → مدل
برنامه‌ی گام‌به‌گام + فایل‌های درگیر تولید می‌کند → کاربر تأیید/ویرایش/رد می‌کند →
اجرا با همان برنامه به‌عنوان brief وظیفه.

## وضعیت فعلی در کد
- Power Mode ابزارهای `plan_mode_enter/exit` + `todo_write` دارد (`planModeTools.ts`) —
  ولی محصول‌سازی نشده
- NI autonomy service صراحتاً plan-approval ندارد («full autonomy, no plan-approval
  gate» — `neuralInverseAgentService.ts:187`)
- `agentTaskDecomposer.ts` تجزیه‌ی وظیفه با LLM دارد (پایه‌ی تولید برنامه)

## طرح پیاده‌سازی
1. toggle «Plan» کنار انتخاب حالت chat (`SidebarChat` حالت‌های ask/reason/copilot/agent)
2. در حالت plan: ScopedToolRegistry فقط ابزارهای خواندنی (read/search/gitStatus/…)؛
   ابزار نوشتن/ترمینال مسدود + پیام روشن به مدل
3. خروجی برنامه با قالب ساخت‌یافته: هدف / گام‌ها (فایل درگیر به ازای هر گام) /
   ریسک‌ها — رندر به‌صورت کارت قابل ویرایش (لیست checkbox)
4. کاربر: **Approve** (اجرا با برنامه به‌عنوان پیام اول + تزریق در system prompt) /
   **ویرایش گام‌ها** / **Reject** (بازگشت به گفتگو)
5. `requirePlanApproval` در `.neuralinverseagent` (پیش‌فرض false تا رفتار فعلی عوض نشود)؛
   اگر true، autonomy service قبل از اجرای ابزار نوشتن، حالت plan را طی کند
6. todo های اجرا (از `todo_write` موجود) در `AgentActivityBox` زنده آپدیت شوند

## معیارهای پذیرش
- [ ] در حالت plan هیچ ابزار نوشتن/اجرایی اجرا نمی‌شود (حتی اگر مدل اصرار کند)
- [ ] برنامه‌ی ساخت‌یافته قابل ویرایش قبل از تأیید است
- [ ] بعد از Approve، اجرا از همان برنامه شروع می‌شود و todo ها زنده پیش می‌روند
- [ ] با `requirePlanApproval: false` رفتار فعلی (خودمختار) دست‌نخورده است

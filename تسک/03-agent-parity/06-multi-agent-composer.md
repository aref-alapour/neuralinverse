# A6 — الگوی Planner/Worker (معادل Composer مولتی‌ایجنت Cursor)

- **اولویت:** P2 | **برآورد:** M/L | **وضعیت:** 🟡 اجزا موجود — ولی نیمی‌شان ثبت نشده‌اند | **وابستگی:** A1، A2، [Q13](../05-quality/13-contribution-registration-gate.md)

> **اصلاح صورت‌مسئله ۲۰۲۶-۰۹-۰۸ — «اجزا موجود» را تفکیک کن:**
>
> | جزء | مسیر | زنده؟ |
> |---|---|---|
> | `neuralInverseSubAgentService` (۹ نقش، سقف هم‌زمانی) | `contrib/void/browser/` | ✅ ثبت‌شده در `void.contribution.ts:87` |
> | `workflowOrchestrator` (DAG با `dependsOn`، Kahn، retry) | `contrib/neuralInverse/browser/orchestrator/` | ✅ ترانزیتی از `toolsService.ts:34` |
> | **`composer/composerModule`** (canvas، nodes، panels، serializer، history) | `contrib/neuralInverse/browser/composer/` | ❌ **مرده** — فقط از `neuralInverse.contribution.ts` که importer ندارد |
> | `runSubagentTool` upstream | `chat/common/tools/builtinTools/` | ✅ در استک بومی |
>
> پس ادعای «کامپوزر بصری از Composer خود Cursor جلوتر است» دربارهٔ کدی است که
> **در زمان اجرا بارگذاری نمی‌شود**. کیفیت کد بالاست؛ در دسترس کاربر نیست.
>
> ```bash
> grep -rn "composerModule" src --include=*.ts | grep -v contrib/neuralInverse/   # صفر
> ```
>
> **ترتیب درست:** اول Q13 (تصمیم ثبت)، بعد الگوی planner→worker→verifier روی
> `runSubagentTool` + orchestrator موجود. تا Q13 بسته نشود این تسک روی شن است.
- **هم‌ارز در Cursor:** Composer — یک planner کار را تجزیه می‌کند، worker ها موازی اجرا می‌کنند

## هدف
الگوی orchestrator روی زیرساخت موجود: نقش «planner» (تجزیه به زیرتسک‌های مستقل با
خروجی مشخص) + اجرای موازی زیرتسک‌ها با نقش‌های موجود (explorer/editor/tester/reviewer)
+ جمع‌بندی verifier. هدف: سرعت (موازی) و کیفیت (نقش مخصوص هر کار).

## وضعیت فعلی در کد
- `neuralInverseSubAgentService.ts` — صف + `MAX_CONCURRENT_SUB_AGENTS`، اجرای headless
  با `PowerModeService.runSubAgentLoop`، ۹ نقش با بسته‌ی ابزار per-role
- `AgentNetworkViz.tsx` — ویژوال شبکه‌ی agent **از قبل موجود است** (فقط باید تغذیه شود)
- `workflowOrchestrator` — DAG با concurrency level (اگر بخواهیم planner خروجی را به
  workflow تبدیل کند، موتور اجرا آماده است)
- ابزارهای `spawn_agent` / `get_agent_status` / `wait_for_agent` در Power Mode

## طرح پیاده‌سازی
1. **تعریف agent از نوع planner:** در `.inverse/agents/` (اسکیمای `IAgentDefinition`
   موجود) — system prompt خاص: «تسک را به زیرتسک‌های مستقل تجزیه کن؛ برای هر کدام
   نقش + ورودی + خروجی مورد انتظار تعیین کن؛ وابستگی‌ها را بگو» با خروجی JSON
   (schema validation با `outputValidator` موجود)
2. **موتور الگو:** سرویس `composerService`:
   - خروجی planner → ساخت workflow پویا (step ها = زیرتسک‌ها با dependsOn)
   - اجرا با `workflowOrchestrator` (موازی‌سازی و سطح‌بندی رایگان به دست می‌آید)
3. **UI:** در chat: دکمه «Composer» (یا حالت جدید) → نمایش گراف زیرتسک‌ها در
   `AgentNetworkViz` با وضعیت زنده (running/done/failed) + امکان cancel هر شاخه
4. **Verifier:** بعد از اتمام worker ها، نقش reviewer خروجی diff را ارزیابی می‌کند؛
   اگر reject → یک دور اصلاح (سقف ۲ دور)
5. بودجه‌ی مصرف: جمع بودجه‌ی run ها از `budgetTracker` — نمایش لحظه‌ای در UI

## معیارهای پذیرش
- [ ] یک تسک دو-بخشی (مثلاً «تست بنویس + داکیومنت به‌روز کن») دو worker موازی اجرا می‌شود
- [ ] گراف زنده در AgentNetworkViz وضعیت‌ها را نشان می‌دهد
- [ ] دور اصلاحِ verifier در صورت reject کار می‌کند (سقف ۲)
- [ ] مصرف توکن کل در UI دیده می‌شود و سقف دارد

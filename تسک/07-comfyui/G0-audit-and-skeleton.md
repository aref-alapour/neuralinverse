# G0 — ممیزی و اسکلت (Wave 0) — تصمیم extend-vs-replace

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** پیش‌نیاز همه‌ی Gها | **برآورد:** S (ممیزی انجام شد؛ فقط تصمیم‌ثبتی + اسکلت مانده) | **وضعیت:** 🟡 ممیزی ✔
- **منبع:** COMFYUI-HANDOFF §5 Wave 0 + ممیزی مستقل ما (سپتامبر ۲۰۲۶)

## نتیجه‌ی ممیزی (انجام‌شده — جزء تسک، `composer/` + `orchestrator` خوانده شد)

1. **`composer/model/composerModel.ts` (343 خط):** مدل صرفاً **بصری** است — nodes با
   position/size/selection/viewport، edges به‌صورت ۴تایی (sourceNodeId/PortId,
   targetNodeId/PortId). **هیچ semantics اجرایی ندارد**؛ dataType پورت‌ها فقط نمایشی
   است ('flow'|'text'|'json'|'any').
2. **`composer/nodes/nodeRegistry.ts` (304 خط):** ۶ نوع نود hard-code شده
   (trigger/agent/conditional/transform/output/group) با `configSchema` فرم‌محور
   (UI). **قرارداد نود تایپ‌شده نیست**: بدون input types واقعی، بدون execute، بدون
   RETURN_TYPES، بدون lazy/isChanged.
3. **`orchestrator/workflowOrchestrator.ts` (540 خط):** روی `IWorkflowDefinition`
   (مدل **steps**) کار می‌کند نه گراف canvas — سطح‌بندی Kahn برای همزمانی، هر step =
   یک agent run. یعنی canvas از طریق serializer به لیست step تبدیل می‌شود و بعد
   اجرا می‌شود. **موتور dataflow (لینک‌های تایپ‌شده، اجرای per-node، کش، lazy/async،
   اجرای مجدد جزئی) اصلاً وجود ندارد.**
4. نتیجه: ComfyUI engine لایه‌ی مفقوده است، نه رقیبِ چیزی که داریم.

## تصمیم پیشنهادی (ثبت کن و بعد از تأیید owner قطعی کن)

**Side-by-side + Adapter (نه replace فوری):**
- موتور پورت‌شده در ماژول جدید `browser/workflow-engine/` زندگی می‌کند (طبق پیشنهاد handoff)
- قرارداد نود جدید (`WorkflowNodeDef` از G4) با یک **adapter نود «Agent Step»** شروع
  می‌شود که همان `agentExecutor` فعلی را wrap می‌کند → همه‌ی agent های موجود بدون
  تغییر روی موتور جدید اجراپذیرند
- `workflowOrchestrator` فعلی دست‌نخورده می‌ماند (workflow های JSON step-based به کارشان
  ادامه می‌دهند)؛ canvas به‌تدریج per-node-kind روی موتور جدید می‌رود (G3 milestones)
- معیار مهاجرت نهایی: وقتی caching (G5) و partial re-execution دموی متقاعدکننده داد،
  serializer مسیر پیش‌فرض اجرا می‌شود

## کارهای باقی‌مانده‌ی این تسک
1. تأیید owner روی تصمیم بالا → ثبت در `workflow-engine/README.md` (design note)
2. ساخت اسکلت: `workflow-engine/{graph,validation,executionList,executor,nodeTypes,caching,queue,nodeInfo}.ts`
   (فایل‌های خالی با JSDoc منشأ پورت — هر کدام در موج خودش پر می‌شود)
3. ساخت `workflow-engine/PORTED-FROM.md` (جدول: module ← source path ← upstream commit `acb2a019`)
4. قبل از پورت هر ماژول: `git -C C:/Users/jobal/dev/comfyui log --oneline -5 -- <path>`
   (upstream روزانه جلو می‌رود)
5. **قاعده‌ی containment:** کل `workflow-engine/` مثل `تسک/` fork-only است — به‌دلیل
   منشأ GPL-3.0 هرگز وارد PR های upstream (Apache-2.0) نمی‌شود. در `AGENTS.local.md`
   ثبت شده.

## معیارهای پذیرش
- [ ] design note تصمیم extend-vs-replace در README ماژول ثبت شده
- [ ] اسکلت فایل‌ها + PORTED-FROM.md ساخته شده و کامپایل می‌شود
- [ ] قاعده‌ی fork-only در AGENTS.local.md هست

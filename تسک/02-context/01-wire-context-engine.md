# C1 — اتصال Context Engine به همه‌ی نقاط ورودی

- **اولویت:** P0 | **برآورد:** M (باقی‌مانده: S/M) | **وضعیت:** 🟡 ابزارها وصل‌اند، بودجه/ممیزی نه | **وابستگی:** —
- **هم‌ارز در Cursor:** موتور context واحدی که پشت همه‌ی قابلیت‌ها (Chat / Ctrl+K /
  Composer / Tab) یکسان کار می‌کند

## وضعیت راستی‌آزمایی‌شده (۲۰۲۶-۰۹-۰۷)

راستی‌آزمایی روی کد، نه روی سند. **مارکر قبلی 🔴 کهنه بود.**

**انجام‌شده — گام ۲ کامل است:**
- شش ابزار `context_*` (`search_symbols` / `related_files` / `file_context` /
  `import_graph` / `recent_edits` / `semantic_search`) داخل شیء `builtinTools`
  ثبت شده‌اند: `prompt/prompts.ts:580-626` (شیء از خط ۱۸۲ باز می‌شود و تا بعد از
  ۶۴۰ بسته نمی‌شود — پس هر شش تا عضو آن‌اند).
- `availableTools()` در `prompts.ts:678` آن‌ها را به چت می‌دهد: `agent`/`copilot`/
  `validate` کلِ `Object.keys(builtinTools)` را می‌گیرند، و `ask`/`reason`/`gather`
  هم همه‌ی ابزارهای **بدون نیاز به تأیید** را — و چون هیچ‌کدام از شش ابزار `context_*`
  در `approvalTypeOfBuiltinToolName` (`toolsServiceTypes.ts:21-38`، فقط edits/terminal)
  نیستند، **در همه‌ی حالت‌های چت جز `power`/`checks` در دسترس‌اند** — نه فقط executor.
- پیاده‌سازی‌شان در `void/browser/toolsService.ts:1146+` با import تنبل از
  `neuralInverse/browser/context/tools/`؛ نوع‌ها در `toolsServiceTypes.ts:80,143`
  و سطح تأیید در `neuralInverseAgentTypes.ts:56,204`.

> نکته‌ی مهم برای بازبین بعدی: `grep searchSymbols` در `contrib/void` **جواب اشتباه
> می‌دهد** — نام ابزارها snake_case است (`context_search_symbols`). همچنین ابزارها
> در `chatThreadService` وصل نمی‌شوند؛ مسیرشان `prompts.ts` + `toolsService.ts` است.

**باقی‌مانده:**
- [ ] `matrix.md` (ماتریس ممیزی) — وجود ندارد
- [ ] `contextBudgets` مرکزی — صفر hit در کل `src/`
- [ ] Ctrl+K با حالت `inline-edit` بسته‌بندی
- [ ] بسته‌ی context به‌ازای نقش در sub-agent ها

**دستور بازتولید:**
```bash
grep -n "^\tcontext_" src/vs/workbench/contrib/void/common/prompt/prompts.ts
grep -rn "contextBudgets" src/ | wc -l   # → 0
```

## هدف
Context Engine (که در `neuralInverse/browser/context/` یک موتور کامل است) به‌صورت
یکدست به **همه‌ی** نقاط ورودی وصل شود: sidebar chat، Ctrl+K، autocomplete،
workflow executor و sub-agent ها. الان بخش‌هایی از آن فقط به executor سرویس می‌دهد.

## وضعیت فعلی در کد
موتور موجود (همه در `src/vs/workbench/contrib/neuralInverse/browser/context/`):
- `packer/contextPacker.ts` — حالت‌های autocomplete / chat / inline-edit / agent با بودجه‌ی توکن
- `search/hybridSearchService.ts` + `bm25Index.ts` + `trigramIndex.ts` + `embeddingService.ts` + `persistentStore.ts`
- `index/workspaceSymbolIndex.ts`، `graph/dependencyGraph.ts`، `tracker/changeTracker.ts`،
  `relevance/relevanceScorer.ts`، `input/astContextService.ts`
- ابزارهای context (searchSymbols / getRelatedFiles / getFileContext / getImportGraph /
  getRecentEdits) — الان فقط در مسیر executor (`CONTEXT_TOOL_NAMES`) تزریق می‌شوند
- sidebar chat فقط از repo map ساده (`directoryStrService.ts`) و فایل‌های باز استفاده می‌کند

## طرح پیاده‌سازی
1. **ماتریس ممیزی:** جدول «نقطه‌ی ورودی × منبع context» بساز (چه چیزی الان تزریق می‌شود)؛
   به‌عنوان `تسک/02-context/matrix.md` نگه‌داری شود و در PR هم ضمیمه شود
2. chat mode های agent/copilot: تزریق ابزارهای context (searchSymbols و…) در کنار
   ابزارهای موجود — مسیر merge ابزار در `chatThreadService._runChatAgent` از قبل هست
3. Ctrl+K: استفاده از حالت `inline-edit` بسته‌بندی contextPacker (به‌جای فقط بافر اطراف cursor)
4. sub-agent ها (`neuralInverseSubAgentService`): هر role بسته‌ی context خودش بگیرد
   (explorer → search/getImportGraph؛ editor → فایل‌ها + diff areas)
5. تنظیم مرکزی «context budget» در settings: سهم هر منبع (repo map / history / memories /
   context pack) به‌ازای feature — یک `contextBudgets` config مشترک
6. شمارنده‌های ساده (event counter موجود): چند بار هر منبع به کار گرفته شد — برای اندازه‌گیری

## معیارهای پذیرش
- [ ] ماتریس ممیزی کامل است و در CI/PR ضمیمه می‌شود
- [ ] در sidebar chat (حالت agent) ابزار searchSymbols/getRelatedFiles قابل فراخوانی است
- [ ] Ctrl+K با context بسته‌بندی‌شده جواب بهتری می‌دهد (تست دستی روی ۳ سناریو)
- [ ] هیچ نقطه‌ی ورودی‌ای نیست که contextPacker را دور بزند

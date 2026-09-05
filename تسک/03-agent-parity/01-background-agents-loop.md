# A1 — وصل کردن حلقه‌ی LLM به Background Agents

- **اولویت:** P0 | **برآورد:** M | **وضعیت:** 🔴 (ماکارندی git آماده، مغز ندارد) | **وابستگی:** —
- **هم‌ارز در Cursor:** Background Agents — تسک را پس بده، برود روی worktree کار کند و PR بدهد

## هدف
مهم‌ترین feature خالی محصول. تمام چرخه‌ی git (worktree/branch/commit/PR، حداکثر ۳ تا
موازی + صف + cancel + diff نسبت به base + `gh pr create`) **از قبل کار می‌کند** — فقط
حلقه‌ی اجرای agent یک placeholder است. این تسک همان سیم‌کشی است.

## وضعیت فعلی در کد
- `src/vs/workbench/contrib/neuralInverse/browser/backgroundAgentService.ts`:
  - خط ~۲۲۲: `_runAgentLoop` → «Placeholder: The actual LLM agent loop will be wired here»
  - خط ~۱۷۱: «TODO: Wire WorkflowOrchestrator.run() here once tool CWD override is supported»
- UI آماده: `backgroundAgentPanel.ts` + `BackgroundAgentConsole.tsx`
- `workflowOrchestrator` + `agentExecutor` + `ToolRegistry.scope()` آماده‌اند ولی
  ابزارها CVD (پوشه‌ی workspace اصلی) را هدف می‌گیرند نه worktree

## طرح پیاده‌سازی
1. **Tool CWD override:** پارامتر `cwd` در زمینه‌ی اجرا (execution context) که
   `fsTools` / `terminalTools` / `gitTools` از آن بخوانند (پیش‌فرض: workspace root —
   بدون تغییر رفتار مسیرهای موجود)
2. **سیم‌کشی:** در `_runAgentLoop`:
   - ساخت ScopedToolRegistry با cwd = مسیر worktree
   - اجرای `agentExecutor` (یا orchestrator با یک step) با تعریف agent انتخابی
   - استریم خروجی به `BackgroundAgentConsole` (کانال موجود)
3. **دستور کار پیش‌فرض:** prompt کاربر + قانون‌های پروژه از داخل worktree (چون
   `.neuralinverserules` / AGENTS.md داخل worktree هست — هم‌راستا با E1)
4. **پایان کار:** خلاصه‌ی تغییرات (`git diff --stat`) + درخواست PR (از همان مسیر
   `gh` موجود) + اعلان (استفاده از `notify` موجود)
5. محدودیت‌ها: سقف iteration (مثلاً ۴۰)، timeout کلی (مثلاً ۳۰ دقیقه) — از
   `budgetTracker` موجود برای کنترل هزینه
6. live-patch port + تست owner

## معیارهای پذیرش
- [ ] تسک پس‌داده‌شده روی worktree جدا کار می‌کند؛ workspace اصلی دست‌نخورده می‌ماند
- [ ] پیشرفت به‌صورت زنده در BackgroundAgentConsole دیده می‌شود
- [ ] پایان کار: branch + commit + (در صورت فعال بودن) PR ساخته می‌شود
- [ ] دو background agent موازی روی دو worktree جدا بدون تداخل
- [ ] cancel واقعاً loop را می‌کشد و worktree را تمیز می‌کند

# E3 — اجرای Headless و CLI (برای CI و اتوماسیون)

- **اولویت:** P2 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** A1 (cwd override)
- **هم‌ارز در رقبا:** `claude -p` / `codex exec` — اجرای agent در pipeline بدون UI

## هدف
اجرای agent/workflow از خط فرمان: `neuralinverse agent run <agentId> --input "..."`
با خروجی NDJSON (رویدادهای progress) و exit code معنادار — برای CI، cron و اسکریپت.
این قابلیت برای بخش enterprise/firmware پروژه (که کار regulated می‌کند) حتی از
رقبا طبیعی‌تر است: pipeline های مهاجرت/کامپلاینس در CI اجرا شوند.

## وضعیت فعلی در کد
- سرویس‌ها در browser process زندگی می‌کنند (محدودیت معماری VS Code) — اجرای real
  headless نیاز به میزبان دارد
- `workflowAgentService.runAgent()` از داخل workbench قابل فراخوانی است
- زیرساخت electron-main برای IPC آماده است

## طرح پیاده‌سازی
1. **گام ۱ (ساده و کاربردی):** حالت «CLI bridge»: `neuralinverse --agent <id> --input "..."`
   → اجرای Electron با پنجره‌ی مخفی/کمینه + socket/named-pipe در electron-main که
   درخواست را به workflowAgentService می‌برد و NDJSON را به stdout تلمپ می‌کند
2. خروجی: هر رویداد یک خط JSON: `{type: "log"|"tool_call"|"tool_result"|"final"|"error", ...}`
   + کد خروج: 0 موفق / 1 خطای اجرا / 2 timeout / 3 budget
3. **گام ۲ (کامل):** استخراج executor به پکیج standalone (node) بدون Electron —
   وقتی A2 (native tool calling) انجام شد این خیلی واقعی‌تر می‌شود چون executor به
   UI وابسته نیست
4. احراز: از همان credentials/settings پروفایل (BYOLLM)؛ متغیر محیطی برای override
   provider (مثلاً مدل ارزان‌تر در CI)
5. نمونه‌ها: `docs/examples/ci-github-actions.yml` (run agent code-reviewer روی PR)

## معیارهای پذیرش
- [ ] اجرا از cmd بدون باز شدن پنجره؛ خروجی NDJSON قابل parse
- [ ] exit code درست در سه سناریو (موفق/خطا/timeout)
- [ ] abort با Ctrl+C تمیز است (پروسه و temporary ها پاک می‌شوند)
- [ ] مثال CI واقعاً روی یک PR اجرا شده

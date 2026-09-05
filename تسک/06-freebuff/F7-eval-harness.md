# F7 — بنچمارک و Eval برای agent خودمان (پورت BuffBench)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P2 | **برآورد:** M/L | **وضعیت:** 🔴 | **وابستگی:** F1 (ابزارها باید اول پایدار باشند)
- **منبع الگو:** freebuff `evals/buffbench/` (راستی‌آزمایی‌شده)

## چرا
الان هر تغییر در agent executor ما «به‌حس» تست می‌شود. یک harness کوچک یعنی:
هر تغییر آینده (F1 تا F6، A2، …) قابل رگرسیون-تست است و می‌توان عددی ادعا کرد
«agent ما بهتر شد». ضمناً runner های cross-agent freebuff یعنی می‌توانیم خودمان را
با Claude Code / Codex / opencode هم مقایسه کنیم.

## منبع
- `evals/buffbench/run-buffbench.ts` + `agent-runner.ts` — الگوی «بازسازی commit»:
  از commit واقعی ریپو، parent را checkout کن (`git show ${parentSha}:<path>` برای
  فایل‌های context — L116)، از agent بخواه همان تغییر را پیاده کند، با diff واقعی
  مقایسه کن؛ `finalCheckCommands` (تست/lint) بعد از پیاده‌سازی اجرا می‌شود (L130-135)
- `judge.ts` — پنل داور: `judge-gpt` + `judge-sonnet` فعال، امتیاز هر داور نگه داشته
  می‌شود + میانگین (dual-judge برای کاهش سوگیری یک مدل)
- `pick-commits.ts` — غربال commit های سخت (L60-110) تا dataset بی‌کيفیت نشود
- `runners/claude.ts`, `codex.ts`, `opencode.ts`, `codebuff.ts` — اجرای همان eval روی
  رقبا (مقایسه‌ی عددی!)
- `meta-analyzer.ts` + `lessons-extractor.ts` — تحلیل بین-dataset + استخراج درس‌ها
  (به F4-ب وصل می‌شود)

## طرح پیاده‌سازی
1. `tools/agent-evals/` (فقط local، fork-only — یا `evals/` اگر upstream بخواهد بعداً):
   - dataset: ۱۵-۳۰ commit از ریپوهای fixture کوچک (بجز این repo غول) — از
     غربال commit سخت شروع کن
   - runner: درایب `workflowAgentService.runAgent()` به‌صورت headless روی یک agent
     عمومی (implementation agent) با checkout تمیز در tmp
   - داوری: همان الگوی dual-judge با دو مدل از provider های متفاوت (BYOLLM!)
2. خروجی: جدول امتیاز per-task + diff نگه‌داری‌شده؛ رگرسیون = افت میانگین > آستانه
3. حلقه: درس‌های استخراج‌شده → `.inverse/lessons/` (F4-ب) → پرامپت‌های بهتر
4. runner های رقبا (اختیاری، برای مقایسه‌ی داخلی): همان eval روی `claude -p` و
   `codex exec` با CLI آنها (ابزارش را ما نداریم — اسکریپت ساده)

## معیارهای پذیرش
- [ ] یک eval end-to-end روی یک commit fixture اجرا و امتیاز می‌گیرد
- [ ] اجرای دوباره‌ی همان eval روی همان مدل → واریانس معقول (±۱۵٪)
- [ ] دو داور با مدل‌های متفاوت کار می‌کنند و امتیاز هر دو ذخیره می‌شود
- [ ] بعد از یک تغییر executor، قبل/بعد قابل مقایسه است (دستور ساده: `run + compare`)

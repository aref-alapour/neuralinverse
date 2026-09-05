# E2 — Skills و Hooks (اکوسیستم توسعه‌پذیری)

- **اولویت:** P2 | **برآورد:** L | **وضعیت:** 🔴 | **وابستگی:** A4 (رویداد مجوز)، E1
- **هم‌ارز در Cursor/Claude Code:** پوشه‌های skill پروژه + hook های lifecycle —
  اثبات‌شده توسط Claude Code؛ تعداد قابلیت‌ها را بدون تغییر core چند برابر می‌کند

## هدف
**Skills:** بسته‌های «دستورالعمل + اسکریپت» per-project که مدل به آن‌ها ارجاع می‌دهد
(`.inverse/skills/<name>/SKILL.md` + فایل‌های کمکی). **Hooks:** فرمان‌های shell که
روی رویدادهای lifecycle اجرا می‌شوند (`.inverse/hooks.json`).

## وضعیت فعلی در کد
- ۱۲ agent و ۶ workflow داخلی (`builtinLibrary.ts`) — ولی قالب «skill» سبک وجود ندارد
- trigger manager (file-save/schedule/commit/terminal) فقط workflow ها را شروع می‌کند
- هیچ رویداد pre/post-tool-call ای وجود ندارد (برای hooks لازم است)

## طرح پیاده‌سازی

### Skills
1. قالب: `.inverse/skills/<name>/SKILL.md` (frontmatter: `name`, `description`,
   `whenToUse`) + فایل‌های کمکی دلخواه (template ها، اسکریپت)
2. کشف: scan پوشه در باز شدن workspace؛ لیست skill ها به‌صورت فشرده (نام + توضیف +
   whenToUse) به system prompt اضافه می‌شود (~۵۰ توکن به ازای skill)
3. ابزار `use_skill(name)`: محتوای SKILL.md را به‌عنوان context برمی‌گرداند + مسیر
   فایل‌های کمکی — مدل آن‌وقت می‌داند چطور استفاده کند
4. UI: لیست skill ها در agentManagerPart + دکمه «New skill from chat» (از آخرین
   تبادل خوب یک skill بساز)

### Hooks
5. رویدادها: `session_start` / `session_end` / `pre_tool_call` / `post_tool_call` /
   `before_commit` — تعریف در `.inverse/hooks.json`:
   `[{ "event": "pre_tool_call", "tool": "runCommand", "command": "npm run lint", "blockOnFail": true }]`
6. اجرا از مسیر trusted (همان جایی که terminal tools اجرا می‌کنند)؛
   `pre_*` با `blockOnFail` می‌تواند اجرای ابزار را متوقف کند (لایه‌ی policy واقعی)
7. امنیت: hooks فقط از `.inverse/` خوانده می‌شوند (هم‌منطق `.neuralinverseagent`)؛
   در دیالوگ اولین بار تأیید گرفت

## معیارهای پذیرش
- [ ] یک skill «commit-convention» می‌سازیم؛ مدل در تسک commit از آن پیروی می‌کند
- [ ] hook `pre_tool_call` روی runCommand با lint ناموفق، اجرا را بلاک می‌کند
- [ ] لیست skills به system prompt کمتر از ۵۰ توکن به ازای skill اضافه می‌کند

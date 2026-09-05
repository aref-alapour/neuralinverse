# F4 — حافظه‌ی فایل‌محور: Knowledge Files + حلقه‌ی LESSONS.md + پوشه‌های skills

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P1 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** مکمل M1/M3 و E1/E2
- **منبع الگو:** freebuff — **بزرگ‌ترین چیزی که گزارش handoff از قلم انداخته بود** (توسط راستی‌آزمایی کشف شد)

## الف) Knowledge files — لایه‌ی حافظه‌ی قابل‌خواندن-توسط-انسان

**منبع:**
- `common/src/constants/knowledge.ts` — `isKnowledgeFile`: تشخیص `AGENTS.md`،
  `CLAUDE.md`، و `*.knowledge.md`
- `sdk/src/run-state.ts` — `selectKnowledgeFilePaths` (L755): اولویت per-directory:
  `AGENTS.md > CLAUDE.md > knowledge.md`؛ `selectHighestPriorityKnowledgeFile` (L47)؛
  fallback دایرکتوری home: `~/.knowledge.md` / `~/.AGENTS.md` / `~/.CLAUDE.md` (L687)
- `packages/agent-runtime/src/system-prompt/prompts.ts` — `knowledgeFilesPrompt` (L13-60):
  **انضباط نوشتن** — کِی به‌روزرسانی کند، چه چیزی بنویسد/ننویسد، قواعد اختصار،
  URL های scrap شده خودکار. این prompt، تفاوت بین «فایلی که مدل خرابش می‌کند» و
  «حافظه‌ی واقعی پروژه» است.

**ارزش برای ما:** حافظه‌ی ما (M2/M3) embedding-based و در storage داخلی است —
قوی ولی opaque. لایه‌ی knowledge file شفاف است: کاربر می‌خواند، git می‌کند، ادیت
می‌کند، بین تیم share می‌شود. **دو لایه مکمل:** knowledge file = قانون پایدار
پروژه؛ حافظه‌ی برداری = تجربه‌ی شخصی/رویدادی.

**پیاده‌سازی:**
1. تعریف ما: `.neuralinverserules` (موجود) + `AGENTS.md`/`CLAUDE.md` (تسک E1) +
   الگوی `*.knowledge.md` به‌عنوان لایه‌ی حافظه‌ی فایلی per-directory
2. ابزار `update_knowledge` برای agent: ویرایش knowledge file با همان انضباط
   prompt شده (پورت `knowledgeFilesPrompt` — به فارسی نیازی نیست، prompt انگلیسی)
3. در ماژول memory (M3): قبل از ثبت حافظه‌ی جدید، اگر محتوا «قانون پایدار» است →
   پیشنهاد نوشتن در knowledge file به‌جای storage داخلی (toast با انتخاب)

## ب) حلقه‌ی LESSONS.md — یادگیری از هر session

**منبع:** `agents/base2/base-deep.ts` فاز ۷ (L75, L211-247): بعد از هر session:
- نوشتن `LESSONS.md` در `<project>/.agents/sessions/<date>/` (چه شد، چه باید می‌شد)
- به‌روزرسانی فایل‌های skill مرتبط
- spawn یک `thinker-gpt` برای نقدِ خودِ lessons (کیفیت‌بخشی خودکار)
- در سمت eval ها: `evals/buffbench/lessons-extractor.ts` — استخراج
  `Lesson {whatWentWrong, whatShouldHaveBeenDone}` از eval های شکست‌خورده

**پیاده‌سازی:** در پایان هر run موفق/ناموفق workflow (قابل گذاشتن روی دکمه یا
اتوماتیک در حالت deep): تولید lesson یک‌خطی (رویکرد محلی، بدون LLM برای موارد
بدیهی مثل خطای ابزار؛ LLM فقط برای درس‌های واقعی) → ذخیره در
`.inverse/lessons/<date>.md` → تزریق N درس آخر در system prompt اجراهای بعدی
(بودجه ~۵۰۰ توکن). اتصال به F7: درس‌های eval هم همین‌جا بریزند.

## ج) پوشه‌های skills سازگار

**منبع:** `common/src/tools/params/tool/skill.ts` + `sdk/src/skills/load-skills.ts` +
گزینه‌های `skillsDir` / `skillsLoader` / `includeHomeSkills` — می‌خواند:
`~/.claude/skills` و `~/.agents/skills` (یعنی با اکوسیستم موجود Claude Code
سازگار است!) + skill های پروژه.

**پیاده‌سازی:** تسک E2 ما را با این تغییر کامل کن: علاوه بر `.inverse/skills/`،
پوشه‌های `~/.claude/skills` و `~/.agents/skills` هم اسکن شوند — کاربری که skill
برای Claude Code ساخته، بی‌دردست در NeuralInverse هم دارد. فرمت SKILL.md یکسان است.

## معیارهای پذیرش
- [ ] `src/foo.knowledge.md` در system prompt با اولویت درست تزریق می‌شود
- [ ] ابزار update_knowledge با انضباط (بدون طولانی‌شدن بی‌رویه) فایل را به‌روز می‌کند
- [ ] پایان run: فایل lesson ساخته می‌شود و در run بعدی N درس آخر در پرامپت است
- [ ] skill موجود در `~/.claude/skills` در لیست skill های ما دیده و اجرا می‌شود
- [ ] هیچ حافظه‌ی opaque ای برای چیزی که در knowledge file باید باشد ثبت نمی‌شود
      (مسیر پیشنهادی M3 کار می‌کند)

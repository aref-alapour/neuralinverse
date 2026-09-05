# الگوهای freebuff (Codebuff snapshot) — کاتالوگ راستی‌آزمایی‌شده

> منبع: `C:\Users\jobal\dev\freebuff` — snapshot عمومی Codebuff (بازبرند freebuff)،
> ~۳۴k خط TS، Bun monorepo. **لایسنس Apache-2.0.**
>
> ⚖️ **قانون clean-room (۲۰۲۶-۰۹-۰۵):** این کاتالوگ فقط برای **خواندن و ایده‌گیری**
> است. هیچ کدی از freebuff عیناً یا نزدیک‌به-عیناً کپی/تطبیق/پورت نمی‌شود — نه با
> attribution، نه با هدر. طرح و مکانیزم را یاد می‌گیریم و **از صفر با معماری TS
> خودمان** پیاده می‌کنیم تا نتیجه کاملاً متعلق به ما باشد و قابل PR عمومی به
> upstream. هیچ dependency از آن پروژه اضافه نمی‌شود.
>
> مرجع تحلیل: `FREEBUFF-HANDOFF.md` در ریشه + راستی‌آزمایی مستقل ما (سپتامبر ۲۰۲۶).
> همه‌ی مسیرها/خطوط/ثابت‌های ذکرشده در تسک‌های F1 تا F7 با کد واقعی چک شده‌اند —
> این ارجاع‌ها الان صرفاً «نقشه‌ی مطالعه» هستند، نه محل کپی.

## اصلاحات مهم نسبت به FREEBUFF-HANDOFF.md

1. **`process_type: 'BACKGROUND'` پیاده نشده** — در snapshot فعلی throw می‌کند
   (`sdk/src/tools/run-terminal-command.ts` L314-315). ترمینال background ما از
   منبع جلوتر است؛ فقط بخش‌های SYNC را پورت کنید.
2. **`WINDOWS.md` سند troubleshooting کاربر است**، نه فهرست scars مهندسی — جاهای
   باارزش در `docs/agents-and-tools.md` (فلسفه‌ی broker) و کامنت‌های کد
   (`nul`، POSIX mandate، کشف Git Bash) است. bunfs فقط برای binary های Bun مربوط است،
   نه VS Code.
3. compaction مکانیکی **placeholder برای ورودی‌های حذف‌شده ندارد** (drop بی‌صدا) و
   فقط **دو policy** تعریف شده (پیش‌فرض 60min/140k + DeepSeek Flash 15min/40k)، نه
   جدول per-model کامل.
4. «اعتبارسنجی اشتباه agent-با-tool» در واقع **auto-correction** است
   (`tryTransformAgentToolCall` — فراخوانی مدل به spawn تبدیل می‌شود، نه reject).
5. هشدار «toolRegistry.ts تغییرات uncommitted دارد» **منسوخ است** — الان working
   tree پاک است (فقط همین پوشه‌ها اضافه شده‌اند).
6. یادآوری برای تطبیق هدف: «target فاقد sub-agent» فقط درباره‌ی **موتور workflow**
   درست است؛ لایه‌ی Void سرویس sub-agent دارد (`neuralInverseSubAgentService`).

## چیزهای باارزش که handoff از قلم انداخته بود (کشف‌شده در راستی‌آزمایی)

- **سیستم knowledge-files** (AGENTS.md/CLAUDE.md/`*.knowledge.md` + fallback خانه +
  prompt انضباط نوشتن) → تسک **F4-الف**
- **حلقه‌ی LESSONS.md + استخراج درس از eval** → **F4-ب**
- **skills سازگار با `~/.claude/skills` و `~/.agents/skills`** → **F4-ج** (E2 را کامل می‌کند)
- **git commit guide جاسازی‌شده در description ابزار** (`buildGitCommitGuidePrompt`:
  تگ‌های `<commit_analysis>`، heredoc، toggle attribution، «هرگز push/interactive») +
  **repo-stats prompt** (آمار contributor ها، آگاهی از shallow-clone) → قابل ادغام در
  `voidSCMService` و `gitTools` — تسک ریز داخل F6-الف انجامش بیندازید
- **ابزار `apply_patch`** (پریمیتیو سوم ویرایش) → F1
- **`run_file_change_hooks`** — هوک per-filePattern (test/lint بعد از ویرایش) →
  هم‌راستا با E2 (hooks)؛ الگوی دقیقش را از منبع بردارید
- **کاتالوگ مدل با سقف قیمت/routing** (`freebuff-models.ts`، ۴۰۷۰ خط) و taxonomy
  خطاهای دوستانه → مرجع برای Q1 و بهبود پیام‌های خطا
- **گزینه‌ی `projectIndex`** در SDK — تزریق ایندکس ازپیش-محاسبه‌شده؛ دقیقاً همان
  چیزی که Context Engine ما به executor می‌دهد (C1) — الگو تأیید می‌کند مسیر درست است
- **@-mentions در ورودی** (`use-suggestion-engine.ts`) → هم‌راستا با C3
- ابزارهای نادیده‌گرفته‌شده: `think_deeply`, `read_docs`, `web_search` (Serper),
  `create_plan/add_subgoal/update_subgoal`, `set_messages`, `end_turn`

## جدول مپینگ: الگوی freebuff → تسک ما

| الگوی freebuff | تسک | اولویت | وضعیت |
|---|---|---|---|
| str_replace + تعمیر ورودی + apply_patch | **F1-الف** | P0 | 🔴 |
| خواندن پنجره‌ای + footer خودتوصیف | **F1-ب** | P0 | 🔴 |
| referencedBy (code-map) | **F1-ج** (+C5) | P0 | 🔴 |
| compaction مکانیکی + تریگر کش | **F2** (+C7) | P0 | 🔴 |
| بازیابی قطع stream + بهداشت پیام | **F3-الف/ب** | P0 | 🟡 بخشی |
| توکن‌شمار محلی + cache breakpoints | **F3-ج** (+Q1/C2) | P1 | 🔴 |
| knowledge files + انضباط نوشتن | **F4-الف** (+M1/M3/E1) | P1 | 🔴 |
| LESSONS.md + درس از eval | **F4-ب** | P1 | 🔴 |
| skills از `~/.claude/skills` | **F4-ج** (+E2) | P1 | 🔴 |
| propose/apply + فیلد instructions | **F5-الف** (+A4) | P1 | 🔴 |
| ask_user/suggest_followups/write_todos | **F5-د** (+A5) | P1 | 🔴 |
| steering mid-run | **F5-ج** | P1 | 🔴 |
| best-of-N (editor/thinker) | **F5-ب** (+A6) | P2 | 🔴 |
| قواعد ترمینال ویندوزی + clamp | **F6-الف** (+A4) | P1 | 🟡 بخشی |
| کانال XML-in-stream + اجرای سریالی | **F6-ب** (+A2) | P2 | 🔴 |
| RunState/checkpoint هوشمند (identity-gated snapshot، settle-then-save) | → **M1** را غنی‌تر می‌کند | P1 | — |
| buffbench + داور دوگانه + runner رقبا | **F7** | P2 | 🔴 |
| اسکیمای تعریف agent (inheritParentSystemPrompt، outputMode، spawnerPrompt) | → **A6** را غنی‌تر می‌کند | P2 | — |
| درس «base3 به‌جای base2» | → اصل معماری: loop ساده پیش‌فرض، sub-agent فقط opt-in «deep» | — | — |

## قانون Clean-room (جایگزین قانون Attribution قدیمی — الزام قانونی/اخلاقی)

هر کاری که از الگوهای freebuff الهام می‌گیرد:
1. **کد از صفر** با معماری، نام‌گذاری و سبک خودمان — هیچ کپی/تطبیقی، حتی با هدر
   attribution (این قانون از ۲۰۲۶-۰۹-۰۵ جایگزین روش «کپی + attribution» شد).
2. **هیچ dependency** از freebuff/Bun/AI-SDK — با layering ما هم نمی‌خواند.
3. ارجاع تحلیلی آزادانه مجاز است («الگوی مشابه X در Codebuff» در commit/PR)
   چون دیگر کدی جابه‌جا نمی‌شود؛ فقط پیاده‌سازی نباید ترجمه‌ی خط‌به‌خط باشد.

## توصیه‌ی ترتیب داخل این بخش

1. **F1** (ابزار ویرایش — بزرگ‌ترین گپ فنی ما) → 2. **F2** (مکانیکی، هم‌زمان با C7)
→ 3. **F3-الف/ب** (بهداشت — ارزان و بحرانی) → 4. **F4** (حافظه‌ی فایل‌محور، هم‌زمان
با دسته‌ی memory) → 5. **F5-ج/د** (steering و ask_user) → 6. بقیه طبق دسته‌بندی اصلی.

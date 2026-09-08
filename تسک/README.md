# تسک — نقشه‌ی رشد NeuralInverse تا سطح Cursor (و فراتر)

> این پوشه **fork-only** است و هرگز وارد PR های upstream نمی‌شود (هم‌ردیف `tools/`
> و `AGENTS.local.md`). هر تسک یک فایل مستقل با طرح پیاده‌سازی و معیار پذیرش است.
>
> قانون طلایی هر تسک (از `AGENTS.local.md`): پیاده‌سازی روی source → commit محلی →
> پورت به `tools/live-patch.py` → تست owner روی نسخه‌ی نصبی → **با اوکی owner،
> همان کار به‌صورت branch تمیز + issue/PR حرفه‌ای به upstream هم می‌رود.**

## ⚖️ قانون لایسنس / Clean-room (۲۰۲۶-۰۹-۰۵ — الزامی، همه‌ی تسک‌ها)

پروژه بین‌المللی می‌شود و با upstream همکاری عمومی داریم؛ پس برای **هر پروژه‌ی
لایسنس‌دارِ بیرونی** (freebuff/Codebuff — Apache-2.0؛ ComfyUI — GPL-3.0؛
**Cline — Apache-2.0**، کلون: `projects/ide-extensions/cline`، سند:
`CLINE-HANDOFF.md`؛ و هر منبع دیگر):

- **فقط می‌خوانیم:** کدشان را برای فهمیدن طراحی می‌خوانیم و **ایده** می‌گیریم.
- **هرگز عیناً کپی نمی‌کنیم:** نه کپی مستقیم، نه «پورت نزدیک‌به-عیناً»، نه هدر
  provenance، نه ترجمه‌ی مکانیکی خط‌به‌خط. خروجی باید کاملاً کدِ خودمان باشد —
  با معماری، نام‌گذاری و ساختار خودمان.
- **بدون dependency:** از آن پروژه‌ها هیچ وابستگی runtime اضافه نمی‌شود.
- نتیجه: هیچ آلودگی لایسنسی وارد upstream نمی‌شود و همه‌چیز قابل PR عمومی است.
- جاهایی که در فایل‌های F/G عبارت «پورت کن» آمده، از این پس یعنی:
  **«طرح را از منبع بفهم، native و از صفر با سبک خودمان پیاده کن».**

## مقیاس‌ها

- **اولویت:** P0 = فوری (هفته‌های آینده) / P1 = هسته‌ی بعدی / P2 = تمایز
- **برآورد:** S < نیم روز / M = ۱-۳ روز / L > یک هفته (شامل پورت live-patch)
- **وضعیت:** 🔴 شروع نشده / 🟡 در حال کار یا ناقص / ✅ انجام + تست‌شده

### تعریف قطعی وضعیت (قاعده‌ی الزامی — بستن R1/N3)

وضعیت **نظر نیست، تابع گیت‌های Definition of Done است**:

| نماد | تعریف |
|---|---|
| 🔴 | G1 (پیاده‌سازی روی سورس) شروع نشده یا ناقص است |
| 🟡 | G1+G2 سبز (کد نوشته و کامیت شده) ولی G3 (اجرای زنده) یا G4 (تست owner) باز است |
| ✅ | تا G4 سبز — owner روی نسخه‌ی قابل‌اجرا دیده و تأیید کرده |

**چهار شرط «انجام شده» (درس ممیزی ۲۰۲۶-۰۹-۰۸):** وجود فایل پیاده‌سازی به‌تنهایی
هیچ‌چیز را ثابت نمی‌کند. برای هر ادعا هر چهار مورد لازم است:
**فایل + ثبت (`registerSingleton`/contribution) + caller واقعی + سناریوی قابل‌مشاهده.**
سه ممیزی مستقل نشان دادند چک‌کردن فقط مورد اول، هم کد مرده را «آماده» گزارش
می‌کند و هم «grep پیدا نکرد» را به «وجود ندارد» ترجمه می‌کند.

## ⚠️ بازنگری بنیادی ۲۰۲۶-۰۹-۰۸ — این جدول در برابر سایدبار Void نوشته شده بود

جدول زیر فرض می‌کند سطح محصول ما **سایدبار Void** است. سه ممیزی مستقل نشان دادند
این فرض دیگر درست نیست:

1. **پایه‌ی ما VS Code ۱.۱۲۷ است** و استک چت بومی آن checkpoint فایلی، gauge مصرف
   context، plan، مجوز یکپارچه، AGENTS.md/CLAUDE.md، skills، hooks، sub-agent،
   todo و صف پیام را **از قبل و حرفه‌ای‌تر** دارد.
2. **`voidModelProvider.ts` مدل‌های BYOLLM ما را به‌عنوان agent پیش‌فرض همان چت
   بومی ثبت می‌کند** — پس آن قابلیت‌ها بالقوه با موتور خودمان کار می‌کنند، نه با
   Copilot. سخت‌سازی این پل شد [A7](03-agent-parity/07-native-chat-bridge.md).
3. برای بسیاری از ردیف‌های زیر، کار درست **«وصل‌کردن» است نه «ساختن»** — و برآوردها
   باید متناسب کوچک شوند.

**گزارش کامل با شواهد و داوری بین سه ممیزی:**
[ممیزی تسک‌ها در برابر کد](05-quality/task-vs-code-audit-2026-09-08.md)

## نقشه‌ی Cursor Parity — کجا ایستاده‌ایم

| قابلیت Cursor | وضعیت فعلی ما | تسک | اولویت |
|---|---|---|---|
| Memories (خودکار + معنایی) | ⚠️ حافظه‌ی واژگانی، ثبت فقط پایان task | [M2](01-memory/02-vector-retrieval.md) + [M3](01-memory/03-auto-capture-consolidation-ui.md) | P0→P1 |
| ادامه‌ی گفتگو / resume thread | ❌ حافظه در RAM می‌میرد | [M1](01-memory/01-conversation-persistence.md) | **P0** |
| @Docs (ایندکس مستندات) | ❌ | [M4](01-memory/04-docs-knowledge-base.md) | P2 |
| Context: نوار مصرف + شفافیت | 🟡 ویجت بومی از موج ۲ تغذیه می‌شود؛ gauge سایدبار موج ۳ ساخته شد (تست owner باز) | [C2](02-context/02-context-gauge-ui.md) | **P0** |
| @-mentions (@file/@symbol/@web) | ❌ (فقط stage انتخاب) | [C3](02-context/03-at-mentions.md) | P1 |
| فایل‌های Pinned + Notepads | ❌ | [C4](02-context/04-pinned-context.md) | P1 |
| درک Codebase (semantic retrieval) | ⚠️ موتور هست، نیمه‌وصل | [C1](02-context/01-wire-context-engine.md) + [C6](02-context/06-smart-auto-context.md) | P0→P1 |
| Repo map هوشمند | ⚠️ درخت ساده | [C5](02-context/05-repo-map-upgrade.md) | P1 |
| Compaction خودکار با UX | 🟡 موتور عالی، UX صفر | [C7](02-context/07-compaction-ux.md) | **P0** |
| گفتگوی بی‌پایان بدون فراموشی (تا ۱۰M+) | ❌ خلاصه بازنویسی می‌شود، بایگانی غیرقابل‌بازیابی | [M5](01-memory/05-context-ledger.md) | **P0** |
| Background Agents (تسک → PR) | 🔴 LLM وصل نیست **و سرویس ثبت نشده**؛ upstream پوسته‌ی کامل دارد | [A1](03-agent-parity/01-background-agents-loop.md) | **P0** |
| Checkpoints (restore فایل) | ⭐ **دو پیاده‌سازی کامل داریم** (firmware + upstream)، هیچ‌کدام وصل نیست | [A3](03-agent-parity/03-file-checkpoints.md) | P1 |
| سطح‌های auto-run / مجوز واحد | ⚠️ چهار مدل پراکنده؛ upstream مرجع آماده دارد | [A4](03-agent-parity/04-unified-permissions.md) | P1 |
| Plan mode | 🟡 **تله بسته شد (۰۹-۰۸):** گارد در مرز `callTool` نوشتن/اجرای ۱۸ ابزار را در plan رد می‌کند؛ پورت live-patch، تست owner و قدم‌های بعدی A5 باز | [A5](03-agent-parity/05-plan-mode.md) | **P1** |
| Composer (planner/worker) | ⚠️ sub-agent زنده، ولی ماژول composer ثبت نشده | [A6](03-agent-parity/06-multi-agent-composer.md) | P2 |
| Rules (استاندارد صنعت) | ⭐ upstream کامل دارد (AGENTS.md/CLAUDE.md)، ما وصل نیستیم | [E1](04-ecosystem/01-agents-md-compat.md) | **P0** |
| Skills / Hooks | ⭐ upstream هر دو را دارد (`.claude/skills` + hookCompatibility) | [E2](04-ecosystem/02-skills-and-hooks.md) | P2 |
| اجرای CLI/CI (مثل `claude -p`) | ❌ | [E3](04-ecosystem/03-cli-headless.md) | P2 |
| Usage / هزینه | 🟡 `usage` روی desktop می‌رسد (۰۹-۰۸: هر دو مسیر chat + تست پاریتی)؛ تست owner روی نسخه‌ی نصبی باز | [Q1](05-quality/01-cost-usage-tracking.md) + [Q12](05-quality/12-desktop-usage-parity.md) | **P0** |
| Tab (autocomplete) | ✅ داریم | — | — |
| Inline edit (Ctrl+K) | ✅ داریم | — | — |
| Apply / diff | ✅ Fast+Slow داریم | — | — |
| MCP | ✅ (desktop) | — | — |
| BYOLLM بدون lock-in | ✅ **برتر از Cursor** | — | — |

**مزیت‌هایی که Cursor ندارد و باید حفظ/تبلیغ شوند:** موتور workflow با composer بصری،
BYOLLM با ۲۲ provider + مدل‌های رایگان، ماژول‌های firmware و legacy migration، و
compaction ای که از نظر الگوریتم جلوتر است.

## ترتیب اجرای پیشنهادی

### دسته‌ی ۰ — پایه‌ریزی (بازنویسی‌شده ۲۰۲۶-۰۹-۰۸؛ جایگزین دسته‌ی ۱ قدیم)

> این پنج مورد قبل از هر feature جدید می‌آیند: دوتای اول کد نمی‌خواهند، و سه‌تای
> بعدی ورودیِ درست را برای بقیه‌ی بک‌لاگ فراهم می‌کنند.

1. **[Q9](05-quality/09-tls-verification-disabled.md)** — `NODE_TLS_REJECT_UNAUTHORIZED=0`
   هنوز روی سطح User ست است. تنها P0 امنیتیِ باز، و کد نمی‌خواهد.
2. **[Q13](05-quality/13-contribution-registration-gate.md)** — تصمیم درباره‌ی
   contrib ثبت‌نشده. تا این بسته نشود، برآورد A1 و A6 بی‌معنی است.
3. **[Q12](05-quality/12-desktop-usage-parity.md)** — `usage` روی desktop نمی‌رسد.
   پیش‌نیاز عددِ درست در Q1 و C2 و M6.
4. **[A7](03-agent-parity/07-native-chat-bridge.md)** — سخت‌سازی پل چت بومی.
   بزرگ‌ترین اهرم: A3/A4/A5/C2/C7/E1/E2 را از «ساختن» به «وصل‌کردن» تبدیل می‌کند.
5. **[A5](03-agent-parity/05-plan-mode.md) بند اول** — یا `getThreadPlanMode` را
   enforce کن یا ابزارهایش را حذف کن. الان ادعای مهار می‌کند و مهار نمی‌کند.

### دسته‌ی ۱ — برداشت سریع (بعد از دسته‌ی ۰؛ همه S یا S/M)
هدف: زودترین «حس Cursor» با کمترین ریسک. **بعد از A7 هر پنج مورد کوچک‌تر می‌شوند.**
1. **E1** سازگاری AGENTS.md/CLAUDE.md — upstream دارد؛ فقط اتصال
2. **C2** نمایشگر مصرف context — ویجت upstream هست؛ فقط تغذیه
3. **C7** UX دی compaction (`/compact` + کارت summary)
4. **Q1** هزینه‌ی واقعی + داشبورد Usage (بعد از Q12)
5. **Q2** بهداشت کدبیس — ✅ بخش حذف‌ها (۰۹-۰۸: ۷ فایل `.bak` حذف؛ «`.js` مرده» در واقع
   **شیمِ زنده‌ی** ۸ از ۹ باندل React بود و ماند)؛ پیشنهاد N5 منتظر تصمیم owner

### دسته‌ی ۲ — حافظه (قلب استراتژی؛ ادامه‌ی branch فعلی)
> **ستون فقرات این دسته [M5](01-memory/05-context-ledger.md) است.** M1 (ماندگاری) در فاز ۰/۵
> آن حل می‌شود و M2 (بازیابی) روی ایندکس فاز ۳ سوار می‌شود. M5 را قبل از M1/M2 شروع کن،
> وگرنه دو بار ذخیره‌سازی می‌نویسیم.
6. **M5** Context Ledger — بایگانی append-only + اپیزودهای تغییرناپذیر + brief + recall
7. **M2** بازیابی برداری حافظه‌ی پایدار (روی ایندکس مشترک M5-فاز۳؛ fallback واژگانی)
8. **M3** ثبت خودکار + تلفیق + UI مدیریت (تغذیه از `invariants`/`corrections` اپیزودها)

### دسته‌ی ۳ — اتکای agent
9. **A1** وصل کردن LLM به background agents (مهم‌ترین feature خالی)
10. **A2** native tool calling (auto: مدل قوی native، مدل ضعیف JSON-block)
11. **A4** مجوز یکپارچه + پیش‌نمایش
12. **A3** چک‌پوینت فایل + restore

### دسته‌ی ۴ — context عمیق
13. **C1** اتصال Context Engine به همه‌ی نقاط (+ ماتریس ممیزی)
14. **C6** انتخاب خودکار context (دکمه‌ی Codebase)
15. **C3** منشن‌ها → **C4** pinned/notepads → **C5** repo map هوشمند

### دسته‌ی ۵ — تمایز و اکوسیستم
16. **A5** plan mode → **A6** planner/worker → **E2** skills/hooks → **E3** CLI →
    **M4** docs indexing → **Q3** یکپارچه‌سازی سه stack (با توافق upstream)

### دسته‌ی ۶ — الگوهای freebuff (راستی‌آزمایی‌شده از Codebuff)
> کاتالوگ کامل + اصلاحات گزارش handoff: [`06-freebuff/README.md`](06-freebuff/README.md).
> **قانون clean-room اعمال شده:** تحلیل و مپینگ معتبرند؛ پیاده‌سازی فقط ایده‌محور
> و از صفر (بدون کپی کد — Apache-2.0).
> جای‌گذاری در دسته‌ها: F1 (ابزار ویرایش قطعی) کنار ابزارهای دسته‌ی ۳؛
> F2 (compaction مکانیکی) هم‌زمان با C7؛ F3-الف/ب (بهداشت پیام/بازیابی stream) قبل
> از هر کار طولانی روی executor؛ F4 (knowledge files + LESSONS + skills سازگار)
> هم‌زمان با دسته‌ی memory؛ F5-ج (steering) هر وقت؛ F6-الف (ترمینال) با A4؛
> F6-ب و F5-ب و F7 بعد از A1/A2.
17. **F1** ابزار ویرایش قطعی (str_replace + تعمیر ورودی + خواندن پنجره‌ای + referencedBy)
18. **F2** compaction مکانیکی با تریگر cache-aware (لایه‌ی زیر LLM-compactor موجود)
19. **F3** بازیابی قطع stream + بهداشت پیام + توکن‌شمار محلی + cache breakpoints
20. **F4** حافظه‌ی فایل‌محور: knowledge files + حلقه‌ی LESSONS + skills از `~/.claude/skills`
21. **F5** propose/apply + best-of-N + steering + ask_user/followups/todos
22. **F6** سخت‌سازی ترمینال (POSIX/nul/clamp) + کانال XML-in-stream
23. **F7** eval harness (پورت BuffBench با داور دوگانه و runner رقبا)

### دسته‌ی ۷ — موتور گراف ComfyUI (Track A: engine، Track B: embed)
> کاتالوگ + اصلاحات handoff + قواعد clean-room: [`07-comfyui/README.md`](07-comfyui/README.md).
> ممیزی Wave 0 انجام شده (پیشنهاد: side-by-side + adapter). با قانون clean-room،
> `workflow-engine/` **پیاده‌سازی کاملاً خودمان** خواهد بود — بدون کپی GPL، بدون
> محدودیت fork-only، و قابل PR به upstream.
24. **G0** تصمیم extend-vs-replace + اسکلت `workflow-engine/`
25. **G1** فرمت گراف + DynamicGraph (ephemeral با پیشوند deterministic)
26. **G2** موتور validation با NodeErrors ساخت‌یافته (تاکسونومی کامل ۱۴ رشته‌ای)
27. **G3** اجرای توپولوژیک + re-staging واحد (lazy/async/subgraph از یک مسیر)
28. **G4** قرارداد نود تایپ‌شده + adapter «Agent Step» روی agentExecutor فعلی
29. **G5** کش با signature اجدادی + اجرای مجدد جزئی (دموی اصلی — بیعت سرمایه‌ای این پورت)
30. **G6** صف/interrupt اتمیک + پروتکل رویداد کامل + progress
31. **G7** nodeInfo به‌عنوان منبع واحد schema پالت + combo های فایل‌سیستمی
32. **G8** اختیاری‌ها: jobs، history، node-replacement، نود API با قیمت زنده، بهداشت secret
33. **G9** (Track B، مستقل) اجرای خود ComfyUI به‌عنوان سرویس لوکال برای تولید تصویر

**قانون clean-room (جایگزین قوانین پورت قدیمی):** هیچ کدی از comfyui/freebuff یا
هر منبع لایسنس‌دار دیگری عیناً کپی نمی‌شود — فقط خواندن و ایده‌گیری؛ پیاده‌سازی
از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» بالای همین فایل). لاگ upstream
قبل از طراحی چک شود (`git -C C:/Users/jobal/dev/comfyui log --oneline -5 -- <path>`).

## وابستگی‌های کلیدی

- M2 → M3، M4 (زیرساخت برداری مشترک)
- C2 → C3، C4، C7 (breakdown جایی است که همه گزارش می‌دهند)
- A1 → E3 (cwd override پیش‌نیاز CLI است)
- A2 → A5، E3، F6-ب (پروتکل native پایه‌ی plan mode و standalone و کانال XML است)
- A4 → Q3 (مجوز مشترک پیش‌نیاز ادغام است)
- C1 → C5، C6، F1-ج (موتور وصل قبل از ارتقا)
- F1 → F7 (eval فقط بعد از ابزارهای ویرایش پایدار)
- F2 ↔ C7 (دولایه: مکانیکی همیشه + LLM شرطی)
- F4 ↔ M1/M3/E1/E2 (حافظه‌ی فایل‌محور مکمل حافظه‌ی برداری و rules)

## ثبت وضعیت

هر تسک در فایل خودش وضعیت دارد؛ بعد از تغییر، این جدول را هم به‌روز کن:

| تسک | وضعیت | شاخه (branch) | یادداشت |
|---|---|---|---|
| M5 | 🟡 | `feat/context-ledger` | فازهای ۰-۳ و ۵ روی سورس کامل + تست standalone؛ پورت live-patch و تست owner مانده (بند ۱۳ تسک) |
| M1 | 🟡 | درون M5 | journal = persistence؛ کلید conversationId در فاز ۵ بسته شد؛ تست owner مانده |
| M2 | 🟡 | درون `feat/context-ledger` | بازیابی hybrid + pin + سقف ۲۰۰۰ پیاده شد؛ تست owner مانده |
| M3 / M4 | 🔴 | — | روی زیرساخت M5 در session بعدی |
| **A7** | 🔴 | — | **جدید ۰۹-۰۸** — سخت‌سازی پل چت بومی؛ پرلوریج‌ترین تسک بک‌لاگ |
| **Q12** | 🟡 | `213acb1`, `a5ccefb` | usage روی desktop می‌رسد (هر دو مسیر chat + تست پاریتی در verify)؛ پورت live-patch + تست owner باز؛ ~۱۵ هشدار لینت سخت فایل باقی (Q11) |
| **Q13** | 🟡 | `3e16228` | گیت reachability در verify.mjs (با هوک hygiene سبز)؛ ۲۵۹ فایل، ۶ یتیم مستند، ۰ غیرمنتظره؛ تصمیم voiceEventStream با owner |
| **Q2** | 🟡 | `b43716a` | ۷ فایل `.bak` حذف + `*.bak*` ignore؛ شیم `backgroundAgentService.js` زنده درآمد و ماند؛ پیشنهاد N5 (گزینه A) منتظر تصمیم owner |
| A3 | 🟡 | `feat/context-ledger` | **موج ۳ (۰۹-۰۸):** منبع حقیقت = سرویس firmware (برای رندرر بازنویسی شد)، checkpoint در مرز واحد `toolsService` برای هر دو مسیر؛ `agentRollbackService` حذف شد؛ فرمان Restore؛ پورت live-patch و تست owner باز |
| A5 | 🟡 | `feffd9a`, `85335f0` | قدم اول بسته شد: enforce در مرز `callTool` (۱۸ ابزار نویسنده/اجرایی) + ۸ تست؛ پورت live-patch، تست owner و قدم‌های بعدی باز؛ ~۳۱ هشدار لینت سخت فایل باقی (Q11) |
| Q1 | 🟡 | — | **اصلاح ۰۹-۰۸** — از 🔴؛ ادعای هاردکد `$0.0000` باطل شد |
| G6 | 🔴 | — | **اصلاح ۰۹-۰۸** — از 🟡؛ مارکر به صف دیگری اشاره داشت |
| **M6** | ✅ | `235aef5`, `2c34e79` | سخت‌سازی Ledger بسته شد (فایل تسک ✅)؛ تست زنده‌ی Ledger همچنان مانده (S3 در وضعیت ۲۰۲۶-۰۹-۰۶) |
| **Q4** | ✅ | `8c6f1e8`, `875e01f`, `c6233c0` | یکپارچگی live-patch بسته شد؛ selftest هفت‌سناریویی + گیت parse اجباری سبز |
| **Q5** | ✅ | `8c6f1e8`, `cf6412b` | هارنس verify/typecheck-slice/run-tests سبز؛ پوشش محدود به slice (نک. V1/V2 در وضعیت ۲۰۲۶-۰۹-۰۶) |

> **وضعیت زنده (به‌روز ۲۰۲۶-۰۹-۰۶):** هشدار ممیزی ۰۹-۰۵ منسوخ شد — Q4 بسته
> شد و اکنون **۹۷ پچ + ۲ prepend** روی نصب اعمال و `--verify` سبز است
> (۹۹ OK)، ازجمله فوتر پیام و ابزارها. ماندنی‌ها: Ledger هنوز پورت زنده ندارد
> (S3)، پچ‌ها به نام‌های مینیفایِ همین بیلد وابسته‌اند و اولین آپدیت رسمی همه
> را MISSING می‌کند (S1/W4)، و هیچ بیلد کامل از سورس وجود ندارد — رجیستر
> کامل: [وضعیت پروژه ۲۰۲۶-۰۹-۰۶](05-quality/project-status-and-weaknesses-2026-09-06.md).

## Definition of Done (برای هر تسک)

1. پیاده‌سازی روی source (نه فقط live-patch) + استایل TS هم‌خوان فایل
2. commit محلی با پیام روشن (انگلیسی)
3. پورت به `tools/live-patch.py` + اجرای elevated + `--verify` سبز
4. restart توسط owner + تست روی نسخه‌ی نصبی (گیت شماره ۲)
5. فقط با تأیید صریح: PR به upstream (گیت شماره ۱) — بدون فایل‌های محلی

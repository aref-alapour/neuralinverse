# تسک — نقشه‌ی رشد NeuralInverse تا سطح Cursor (و فراتر)

> این پوشه **fork-only** است و هرگز وارد PR های upstream نمی‌شود (هم‌ردیف `tools/`
> و `AGENTS.local.md`). هر تسک یک فایل مستقل با طرح پیاده‌سازی و معیار پذیرش است.
>
> قانون طلایی هر تسک (از `AGENTS.local.md`): پیاده‌سازی روی source → commit محلی →
> پورت به `tools/live-patch.py` → تست owner روی نسخه‌ی نصبی → (اختیاری، فقط با
> تأیید صریح owner) PR به upstream.

## مقیاس‌ها

- **اولویت:** P0 = فوری (هفته‌های آینده) / P1 = هسته‌ی بعدی / P2 = تمایز
- **برآورد:** S < نیم روز / M = ۱-۳ روز / L > یک هفته (شامل پورت live-patch)
- **وضعیت:** 🔴 شروع نشده / 🟡 در حال کار یا ناقص / ✅ انجام + تست‌شده

## نقشه‌ی Cursor Parity — کجا ایستاده‌ایم

| قابلیت Cursor | وضعیت فعلی ما | تسک | اولویت |
|---|---|---|---|
| Memories (خودکار + معنایی) | ⚠️ حافظه‌ی واژگانی، ثبت فقط پایان task | [M2](01-memory/02-vector-retrieval.md) + [M3](01-memory/03-auto-capture-consolidation-ui.md) | P0→P1 |
| ادامه‌ی گفتگو / resume thread | ❌ حافظه در RAM می‌میرد | [M1](01-memory/01-conversation-persistence.md) | **P0** |
| @Docs (ایندکس مستندات) | ❌ | [M4](01-memory/04-docs-knowledge-base.md) | P2 |
| Context: نوار مصرف + شفافیت | ❌ (موتورش هست، UI ندارد) | [C2](02-context/02-context-gauge-ui.md) | **P0** |
| @-mentions (@file/@symbol/@web) | ❌ (فقط stage انتخاب) | [C3](02-context/03-at-mentions.md) | P1 |
| فایل‌های Pinned + Notepads | ❌ | [C4](02-context/04-pinned-context.md) | P1 |
| درک Codebase (semantic retrieval) | ⚠️ موتور هست، نیمه‌وصل | [C1](02-context/01-wire-context-engine.md) + [C6](02-context/06-smart-auto-context.md) | P0→P1 |
| Repo map هوشمند | ⚠️ درخت ساده | [C5](02-context/05-repo-map-upgrade.md) | P1 |
| Compaction خودکار با UX | 🟡 موتور عالی، UX صفر | [C7](02-context/07-compaction-ux.md) | **P0** |
| Background Agents (تسک → PR) | ⚠️ git آماده، **LLM وصل نیست** | [A1](03-agent-parity/01-background-agents-loop.md) | **P0** |
| Checkpoints (restore فایل) | ⚠️ فقط ایندکس پیام | [A3](03-agent-parity/03-file-checkpoints.md) | P1 |
| سطح‌های auto-run / مجوز واحد | ⚠️ سه مدل پراکنده؛ executor بدون تأیید | [A4](03-agent-parity/04-unified-permissions.md) | P1 |
| Plan mode | ❌ (فقط prompt-level) | [A5](03-agent-parity/05-plan-mode.md) | P2 |
| Composer (planner/worker) | ⚠️ اجزا موجود، الگو نیست | [A6](03-agent-parity/06-multi-agent-composer.md) | P2 |
| Rules (استاندارد صنعت) | ⚠️ فقط `.neuralinverserules` | [E1](04-ecosystem/01-agents-md-compat.md) | **P0** |
| Skills / Hooks | ❌ | [E2](04-ecosystem/02-skills-and-hooks.md) | P2 |
| اجرای CLI/CI (مثل `claude -p`) | ❌ | [E3](04-ecosystem/03-cli-headless.md) | P2 |
| Usage / هزینه | ❌ هاردکد `$0.0000` | [Q1](05-quality/01-cost-usage-tracking.md) | **P0** |
| Tab (autocomplete) | ✅ داریم | — | — |
| Inline edit (Ctrl+K) | ✅ داریم | — | — |
| Apply / diff | ✅ Fast+Slow داریم | — | — |
| MCP | ✅ (desktop) | — | — |
| BYOLLM بدون lock-in | ✅ **برتر از Cursor** | — | — |

**مزیت‌هایی که Cursor ندارد و باید حفظ/تبلیغ شوند:** موتور workflow با composer بصری،
BYOLLM با ۲۲ provider + مدل‌های رایگان، ماژول‌های firmware و legacy migration، و
compaction ای که از نظر الگوریتم جلوتر است.

## ترتیب اجرای پیشنهادی

### دسته‌ی ۱ — برداشت سریع (همین هفته؛ همه S یا S/M)
هدف: زودترین «حس Cursor» با کمترین ریسک.
1. **E1** سازگاری AGENTS.md/CLAUDE.md — برد onboarding
2. **C2** نمایشگر مصرف context
3. **C7** UX دی compaction (`/compact` + کارت summary)
4. **Q1** هزینه‌ی واقعی + داشبورد Usage
5. **Q2** بهداشت کدبیس + ابزار `live-patch --verify`

### دسته‌ی ۲ — حافظه (قلب استراتژی؛ ادامه‌ی branch فعلی)
6. **M1** ماندگاری گفتگوها (ادامه‌ی `feat/agent-conversation-memory`)
7. **M2** بازیابی برداری حافظه (با fallback واژگانی — سازگار BYOLLM)
8. **M3** ثبت خودکار + تلفیق + UI مدیریت

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

### دسته‌ی ۶ — پورت‌های freebuff (الگوهای راستی‌آزمایی‌شده از Codebuff)
> کاتالوگ کامل + اصلاحات گزارش handoff: [`06-freebuff/README.md`](06-freebuff/README.md).
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

**قانون پورت freebuff:** فقط کپی/تطبیق با attribution (هدر + `ThirdPartyNotices.txt`)،
هرگز dependency؛ منطق، نه import (Bun/Zod با layering ما نمی‌خواند). درس معماری:
loop ساده پیش‌فرض (base3)، sub-agent فقط opt-in.

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
| M1 | 🟡 | `feat/agent-conversation-memory` | ادامه‌ی کار جاری |
| بقیه | 🔴 | — | — |

## Definition of Done (برای هر تسک)

1. پیاده‌سازی روی source (نه فقط live-patch) + استایل TS هم‌خوان فایل
2. commit محلی با پیام روشن (انگلیسی)
3. پورت به `tools/live-patch.py` + اجرای elevated + `--verify` سبز
4. restart توسط owner + تست روی نسخه‌ی نصبی (گیت شماره ۲)
5. فقط با تأیید صریح: PR به upstream (گیت شماره ۱) — بدون فایل‌های محلی

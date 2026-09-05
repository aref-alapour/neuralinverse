# CLINE-HANDOFF — مرجع مطالعه‌ی Cline (ثبت ۲۰۲۶-۰۹-۰۵)

> **منبع:** https://github.com/cline/cline — کلون محلی:
> `projects\ide-extensions\cline` — commit مبنا: **`dac3b35b`** (2026-09-04).
> **لایسنس: Apache-2.0** (تأیید شد از `LICENSE`).
>
> ⚖️ **قانون clean-room (`AGENTS.local.md` gate 2) کاملاً اعمال می‌شود:** کد فقط
> خوانده می‌شود برای فهم طراحی؛ **هیچ کپی/ترجمه‌ای مجاز نیست** — پیاده‌سازی از
> صفر با معماری خودمان. Cline ریشه‌ی خانواده‌ی Roo-Code/Kilo-Code است؛ ۶۷k+ ستاره؛
> الان یک monorepo با اکستنشن VS Code + SDK مستقل + CLI است.
>
> ردیف کاتالوگ: `AI-LANDSCAPE-2026.md` §1 (ide-extensions) + §4 (shortlist).

## نقشه‌ی معماری (monorepo)

| مسیر | چیست |
|---|---|
| `apps/vscode/` | اکستنشن VS Code (هسته‌ی محصول) — `src/core/` + `webview-ui/` + `standalone/` |
| `sdk/` | SDK عمومی — `sdk/ARCHITECTURE.md` سند معماریش خوب است |
| `apps/cli/` | CLI (الگوی مرتبط با تسک E3 ما) |
| `evals/` | ارزیابی (مرتبط با F7) |
| `proto/` (در apps/vscode) | قرارداد host↔webview با protobuf — جایگزین جالب برای state passing ما |

## ماژول‌های `apps/vscode/src/core/` (نقشه‌ی مطالعه)

- **`task/`** — loop عامل: `task/` + `task/tools/` + `task/focus-chain/`
  (focus chain = نمایش زنده‌ی اهداف/پیشرفت → ایده برای A1/A6)
- **`controller/checkpoints/`** — `checkpointRestore.ts`،
  `checkpointViewLatestChanges.ts` → مستقیم مرتبط با تسک **A3** ما
  (چک‌پوینت فایل + restore؛ رویکردشان git-based snapshot است)
- **`controller/state/togglePlanActModeProto.ts`** + `core/prompts/` —
  **Plan/Act** دو-مود → تسک **A5** ما (plan mode واقعی، نه prompt-level)
- **`shared/AutoApprovalSettings.ts`** + `controller/state/` — مدل تنظیمات
  **auto-approval** تایپ‌شده و granular (per-action) → تسک **A4** ما
  (سطح‌های مجوز + پیش‌نمایش)
- **`context/context-tracking/FileContextTracker.ts`** + `core/context/` —
  ردگیری فایل‌های لمس‌شده/دیدیده‌شده → تسک‌های **C\*** ما
- **`core/mentions/`** — @-mention ها (فایل/مشکل/URL) → تسک **C3**
- **`core/hooks/`** — هوک‌های چرخه‌ی حیات → تسک **E2**
- **`core/controller/mcp/` + `core/integrations/`** — کلاینت MCP + marketplace
- **`skills-lock.json`** (در ریشه‌ی apps/vscode) — سیستم skills نسخه‌دار → **E2/F4-ج**
- **`core/storage/`, `core/ignore/`, `core/locks/`** — ماندگاری، gitignore-awareness، قفل همزمانی (locks → مرتبط با باگ هم‌زمانی M1 خودمان)

## نکته‌های اولیه‌ی ارزش‌سنجی (عمیق‌کاری بعداً در تسک‌ها)

1. **grpc/protobuf بین host و webview** (`proto/` + `grpc-handler.ts`): قرارداد
   تایپ‌شده‌ی دوطرفه — الگوی تمیزتری از پیام‌های ad-hoc ماست؛ برای بازطراحی لایه‌ی
   UI عامل‌ها (agentManagerPart) ارزش مطالعه دارد.
2. **checkpoints جدا از git کاربر**: snapshot های اختصاصی + UI «تغییرات اخیر» —
   برای A3 با شاخه‌بندی تمیزتر از raw-git است.
3. **AutoApprovalSettings granular**: هر ابزار یک سطح اجزا جدا — دقیقاً چیزی که
   A4 می‌خواهد؛ فقط طرح تنظیمات را ببین، پیاده‌سازی خودمان را بسازیم.
4. **Memory Bank** در این repo نیست (ویژه‌ی Roo-Code است) — اگر خواستیم آن را
   بررسی کنیم منبعش Roo است، نه Cline.
5. **worktree** در controller — مدیریت git-worktree برای تسک‌های موازی → مرتبط با A1.

## رأی نهایی ارزش‌پورتی (مطابق §4 رفرش AI-LANDSCAPE)

اولویت مطالعه برای ما: **A3 (checkpoints) > A4 (auto-approval) > A5 (plan/act) >
C3 (mentions) > E2 (hooks/skills)**. Cline موتور گراف/کش ندارد → با ComfyUI
تکمیل‌کننده است، نه هم‌پوشان.

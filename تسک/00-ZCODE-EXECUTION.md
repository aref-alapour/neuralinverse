# پرامپت کامل اجرای تسک‌ها برای zCode

> **این تنها فایلی است که باید به zCode بدهی.** خودکفاست: قواعد، تله‌های محیطی،
> ترتیب، و متن هر تسک. پایه: `7d7962f47f6`.
>
> نسخه‌های قبلی: [موج ۱ و ۲](00-PROMPTS-2026-09-08.md)، [موج ۳](00-PROMPTS-WAVE-3.md).
> این فایل جایگزین هر دو برای اجراهای بعدی است.

---

## بخش ۰ — پرامپت شروع (یک بار، اول هر session)

```text
سلام. روی پروژه‌ی NeuralInverse کار می‌کنی — fork کد VS Code 1.127 + Void.
workspace: C:/Users/jobal/dev/neuralinverse

قبل از هر کاری این چهار کار را بکن و گزارش بده:
1. `AGENTS.local.md` را کامل بخوان. همه‌ی دروازه‌هایش الزامی است — مخصوصاً:
   بدون تأیید صریح مالک هیچ push/issue/PR، و clean-room (کد هیچ پروژه‌ی
   لایسنس‌دار بیرونی عیناً کپی نمی‌شود).
2. `تسک/README.md` بخش «تعریف قطعی وضعیت» و «چهار شرط انجام‌شده» را بخوان.
3. `تسک/05-quality/task-vs-code-audit-2026-09-08.md` بند ۸ (داوری سه ممیزی) و
   بند ۲ (کدی که کامپایل می‌شود ولی ثبت نمی‌شود) را بخوان.
4. `git log --oneline -5` و `git status` بزن و بگو روی چه شاخه‌ای هستی.

── سه تله‌ی این کدبیس که وقتت را هدر می‌دهند ──

الف) «grep چیزی پیدا نکرد» شاهدِ نبودن نیست. سه بار در ممیزی‌ها اتفاق افتاد:
   نام‌های snake_case؛ وصل‌شدن در لایه‌ای غیر از جایی که انتظار می‌رود؛ و
   import ترانزیتی از contrib دیگر — از جمله از طریق باندل‌های .js که
   `grep --include=*.ts` نمی‌بیندشان. یک فایل که «مرده» اعلام شده بود در واقع
   شیمِ زنده‌ی ۸ باندل React بود و حذفش بیلد را می‌شکست.

ب) `npm run typecheck-client` که در CLAUDE.md آمده **در این فورک وجود ندارد**.
   دستور درست:
   NODE_OPTIONS="--max-old-space-size=8192" npx tsc -p src/tsconfig.json --noEmit
   با هیپ پیش‌فرض ۴GB به OOM می‌خورد (خروج ۱۳۴) و نتیجه‌ی گمراه‌کننده می‌دهد.

ج) `node build/eslint.ts <file>` آرگومان فایل را نادیده می‌گیرد و کل ریپو را
   lint می‌کند (>۱۰ دقیقه). برای یک فایل از `npx eslint <file>` استفاده کن.

── قواعد کد ──
تب (نه فاصله)؛ بدون `any`؛ import تکراری ممنوع (در همان خط موجود merge کن)؛
disposable ها بلافاصله بعد از ساخت register شوند؛ رشته‌های کاربر با
`nls.localize` خارجی‌سازی شوند؛ هدر کپی‌رایت Neural Inverse روی فایل جدید.

── قاعده‌ی کامیت (تصمیم مالک، ۲۰۲۶-۰۹-۰۸) ──
هوک hygiene هشدارهای eslint را هم fatal می‌شمارد. **`--no-verify` ممنوع است مگر
با تأیید صریح مالک.** اگر فایلی بدهی لینت تاریخی دارد:
  ۱. اول در یک کامیت جدای `chore(lint): …` بپردازش (بدون تغییر رفتاری)
  ۲. بعد کامیت feature ات را با هوک سبز بزن
این مسیر یک بار یک باگ واقعی پیدا کرد: قانون
`code-no-dangerous-type-assertions` پنهان کرده بود که یک descriptor سه فیلد
لازم ندارد. پس این سربار نیست.

حالا فقط گزارش بده و منتظر بمان. تسک‌ها را یکی‌یکی می‌دهم.
```

---

## بخش ۱ — چک‌لیست پایان هر تسک (به zCode بده)

```text
قبل از اینکه بگویی تمام شد:
1. NODE_OPTIONS="--max-old-space-size=8192" npx tsc -p src/tsconfig.json --noEmit
2. npx eslint <هر فایلی که عوض کردی>  → اگر هشدار داشت، طبق قاعده‌ی کامیت بپرداز
3. node tools/verify.mjs
4. چهار شرط «انجام شده» را صریح جواب بده:
   فایل ✔ / ثبت (registerSingleton یا contribution) ✔ / caller واقعی ✔ /
   سناریوی قابل‌مشاهده ✔
   — اگر یکی جواب ندارد، تسک 🟡 است نه ✅. دروغ نگو، بگو کدام باز است.
5. کامیت با پیام انگلیسی روشن. push نکن.
6. مارکر فایل تسک را طبق قاعده‌ی README به‌روز کن و بگو چه چیزی برای تست owner
   مانده.

و یک قاعده‌ی مهم: **هر تسک با یک دستور اثبات شروع می‌شود.** اگر تحلیل تسک با کد
نخواند، اول به من بگو — تحلیل‌ها روی کامیت‌های قبلی نوشته شده‌اند و ممکن است
کهنه باشند. سه بار تا حالا این اتفاق افتاده و هر بار تحلیل غلط بود، نه کد.
```

---

## بخش ۲ — موج ۳: چهار تسک موازی

> هیچ فایل مشترکی ندارند. هر چهار را می‌توانی هم‌زمان به چهار session بدهی.
> متن کامل هرکدام در [`00-PROMPTS-WAVE-3.md`](00-PROMPTS-WAVE-3.md) است.

| session | تسک | فایل اصلی | یک‌خطی |
|---|---|---|---|
| ۱ | **A3** | `agentRollbackService.ts` + firmware `checkpointService.ts` | سه پیاده‌سازی داریم؛ یکی را منبع حقیقت کن و در مرز ابزار پل ثبتش کن |
| ۲ | **C2** | `chatThreadService.ts` + react سایدبار | چت بومی تمام شد؛ فقط نمایشگر سایدبار مانده |
| ۳ | **E1** | `convertToLLMMessageService.ts` | هسته AGENTS.md/CLAUDE.md را دارد؛ یکی کن، `.neuralinverserules` را نگه دار |
| ۴ | **M2** | `agentMemoryService.ts` + `neuralInverseAgentService.ts` | موتور hybrid هست؛ فقط به مسیر تزریق وصلش کن |

**M1** (`workflowAgentService.ts`) هم موازی است ولی بزرگ‌تر — اگر ظرفیت پنجم داری بده.

---

## بخش ۳ — موج ۴: تسک‌های بازنویسی‌شده (بعد از موج ۳)

این چهار تسک امروز بازنویسی شدند چون فرضشان کهنه شده بود. **متن جدید را بخوان،
نه حافظه‌ات از قبل.**

### A4 — مجوز یکپارچه (`03-agent-parity/04-unified-permissions.md`)

```text
تسک: تسک/03-agent-parity/04-unified-permissions.md — کادر «بازنویسی دامنه» را
حتماً بخوان.

فرض قدیمی («سه مدل مجوز را یکی کن») باطل است. سایدبار و پل چت بومی از موج ۲
همان map و همان تنظیم autoApprove را می‌خوانند. دو مسیر عقب مانده‌اند:

1. Power Mode — askPermission جدا (powerModeProcessor.ts:58، caller در :366)
2. workflow executor — فقط blocklist رجکسی
   (neuralInverse/browser/tools/terminalTools.ts:68، BLOCKED_PATTERNS)

مورد ۲ ضعیف‌ترین حلقه‌ی امنیتی پروژه است: `run_command` هیچ تأییدی نمی‌گیرد و هر
دستوری که الگوی blocklist را نخورد بی‌پرسش اجرا می‌شود. blocklist سیاست نیست.

اول تصمیم مرجع را بنویس و تأیید بگیر (نقشه‌ی خودمان بماند یا سرویس هسته)، بعد
دو مسیر را به همان مرز بیاور. تست: یک دستور مخرب که در blocklist نیست باید در
هر چهار مسیر تأیید بخواهد.
```

### Q3 — یکپارچه‌سازی استک‌ها (`05-quality/03-unify-agent-stacks.md`)

```text
تسک: تسک/05-quality/03-unify-agent-stacks.md — کادر «اصلاح دامنه» را بخوان.

چهار حلقه‌ی اجرا داریم نه سه؛ حلقه‌ی چهارم VoidChatAgentImpl است. ولی بعد از A7
دیگر واگرا نیست. فاز ۰ این تسک فقط **سند معماری** است — کد ننویس.

جدول مسیرها را از A4 بردار، دوباره نساز. خروجی: یک سند که برای هر مسیر بگوید
executor، پروتکل ابزار، مدل مجوز، منبع context، و ledger اش چیست — و کدام‌ها
از قبل یکی شده‌اند.
```

### A2 — native tool calling (`03-agent-parity/02-native-tool-calling.md`)

```text
تسک: تسک/03-agent-parity/02-native-tool-calling.md — یادداشت بالای فایل را بخوان.

دامنه درست است (executor واقعاً JSON-block می‌خواند: agentExecutor.ts:522 با
chatMode: null و allowedToolNames: []). ولی **الگو را از صفر طراحی نکن** —
voidModelProvider.ts همین حالا حلقه‌ی tool-call بومی را با toolCalling: true
کار می‌کند و extractXMLToolsWrapper برای مدل‌های ضعیف fallback است.
کار: همان را به executor برسان.
```

### C7 — UX دی compaction (`02-context/07-compaction-ux.md`)

```text
تسک: تسک/02-context/07-compaction-ux.md — کادر «اصلاح دامنه» را بخوان.

حالا دو سطح را پوشش می‌دهد نه یکی: بعد از A7 بند ج، چت بومی هم در ledger
می‌نشیند. `/compact` و کارت summary باید هر دو را بگیرند.

دو قطعه‌ی آماده که نباید دوباره ساخته شوند:
- chat/common/tools/toolResultCompressor.ts (فشرده‌سازی خروجی ابزار)
- COMPACT_AGENT_HOST_CONVERSATION_ACTION_ID در chatContextUsageDetails.ts
  (الگوی اکشن /compact هسته)
```

---

## بخش ۴ — چیزهایی که zCode نباید دست بزند

| مورد | چرا |
|---|---|
| `product.json`، `voidAutoUpdaterService.ts`، `11-lint-debt-core-chat-files.md` | تغییرات کامیت‌نشده‌ی مالک، از قبل از این نشست‌ها |
| `.claude/` | untracked و ایگنور‌نشده — تصمیم مالک |
| **Q9** (TLS) | کار محیطیِ مالک، کد نمی‌خواهد |
| **A1**، **A6** | تا تصمیم [Q13](05-quality/13-contribution-registration-gate.md) اجرا نشود روی کد ثبت‌نشده کار می‌کنند |
| **G0–G9** | تصمیم محصولی مستقل؛ هنوز گرفته نشده |

---

## بخش ۵ — وضعیت زنده (تا `7d7962f47f6`)

**بسته‌شده در موج ۱ و ۲:** Q2 (بهداشت)، Q12 (usage روی desktop)، Q13 (گیت
ثبت contribution)، A5 قدم ۱ (گارد plan mode)، A7 بندهای الف/ب/ج/د (approval،
tool picker، ledger، gauge).

**گیت‌های سبز:** تایپ‌چک کامل `exit 0`؛ `verify.mjs` — ۱۰۰ تست، گیت contribution
۲۵۹ فایل / ۲۵۳ قابل‌رسیدن / ۶ یتیم مستند / صفر غیرمنتظره.

**باز و مال مالک:** Q9 (TLS)؛ تصمیم `voiceEventStream.contribution.ts`؛ تصمیم
N5 (باندل‌های React)؛ تأیید تغییر هدر `tools/**` در `eslint.config.js`؛ و
ratify یا reset چهار کامیت `--no-verify` موج ۱.

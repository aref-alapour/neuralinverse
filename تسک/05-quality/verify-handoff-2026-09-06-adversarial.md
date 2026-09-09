# Handoff for independent verification + بازبینی نقاط ضعف — بچ 2026-09-06 (فوتر چت + تحویل روی نصب + publish)

> **برای Claude Code:** این سند هم پروتکل راستی‌آزمایی مستقل است و هم درخواستِ
> صریحِ **بازبینی adversarial**. بخش ۲ را خودت اجرا کن و خروجی را با
> «انتظاری» مقایسه کن؛ بعد برو سراغ بخش ۵ — دوازده سوالی که باید با شواهد
> (نه حدس) جواب بدهی. هیچ دستوری در این سند **نمی‌نویسد** در Program Files یا
> فایل‌های کاربر؛ همه read-only هستند مگر موارد علامت‌خورده «ELEVATED» که
> فقط با تأیید صریح مالک اجرا شود. هیچ secret/کلیدی در این سند نیست و تو هم
> واردش نکن (فایل `~/.neural-inverse/mcp.json` مالک حاوی کلید است — فقط به
> اسمش ارجاع بده).

## ۰) زمینه در دو پاراگراف

مالک روی agent داخلی ادیتور NeuralInverse (فورک VS Code، نصب‌شده در
`C:\Program Files\NeuralInverse`، پایه 1.99.3) کار می‌کند و ادیتور باید
«دقیقاً مثل Cursor» کار کند. در ادامه‌ی موج رفع‌های دو روز قبل (issues
#140 و #139)، امروز سه کار انجام شد:

1. **قابلیت فوتر پیام agent** (مدت اجرای تسک + دکمه کپی کل متن همان پیام) که
   دیروز فقط در سورس پیاده شده بود، امروز با live-patch روی باندل
   **مینیفای‌شده‌ی** نصب مستقر شد — چون معلوم شد بیلد از سورس (sparse
   checkout با ۷٪ فایل روی دیسک) عملاً ممکن نیست و کپی‌های کامپایل‌شده‌ی
   AssistantMessageComponent داخل همان `workbench.desktop.main.js` هستند.
   ضمن مسیر، یک باگ سورس هم پیدا شد: ارجاع `_loopStartMs` خارج از scope در
   `abortRunning` که typecheck را می‌شکست.
2. همه‌ی کارها **گیت و publish شد**: ۴ commit روی `feat/context-ledger`،
   شاخه‌ی تمیز فقط-src روی `upstream/ledger-and-agent-fixes` (آپدیت PR #139)
   و issue جدید #141 روی ریپوی اصلی.
3. گیت‌های ولیدیشن قبل از publish سبز شدند (خروجی واقعی در بخش ۲).

نکته‌ی مهم برای داوری: بخشی از کار امروز **جراحی روی کد مینیفای‌شده** است.
سابقه‌ی خطرناک این مسیر: پچ `pe==="timeout"` که دو روز قبل با ghost-match
داخل `E?.type==="timeout"` رفت و ران‌تایم را شکست (فعلاً با REPAIR پچ
رفع شده؛ در SUPERSEDES ثبت است). پس هر جا از «آنکر یکتاست» نوشته‌ام، خودت
دوباره بشمار.

## ۱) اینورتوری دقیق (چه چیزی، کجا، با چه هشی)

### 1.1) commit های امروز روی `feat/context-ledger` (push شده روی origin)

```
e60945c1f5d  tools(live-patch): 97 patches — editor fixes + run_background_command + clipboard + chat footer
aca402aff6a  feat(chat): run duration + copy-whole-message footer on every agent reply
64ee3245b82  fix(tools): editor-agent tool reliability on Windows + long-task survival
4e40311e7e3  fix(stream): a cut stream must never look like a complete answer
```

(این چهار تا رویِ commit های دیروز — `2c34e798…` به قبل — سوارند. مالک
بعداً خود شاخه را روی origin هم push کرد.)

### 1.2) تغییرات سورسِ مرتبط با فوتر

| فایل | تغییر |
|---|---|
| `src/vs/workbench/contrib/void/common/chatThreadServiceTypes.ts` | فیلد اختیاری `durationMs?: number` روی واریانت assistant (خط ~79) |
| `src/vs/workbench/contrib/void/browser/chatThreadService.ts` | فیلد کلاس `_activeLoopStartMs` (~خط 201)؛ ست در شروع حلقه (~1157)، پاک‌سازی در هر دو خروج حلقه (Agent Loop Done / Aborted)؛ `durationMs` در هر سه سایت commit پیام assistant (~925, ~1376, ~1388) + لاگ `[AgentTool]` |
| `src/vs/workbench/contrib/void/browser/react/src/sidebar-tsx/SidebarChat.tsx` | فوتر JSX در `AssistantMessageComponent` (~1441-1460): شرط `isCommitted && durationMs>0`، فرمت `2.4s / 3m 42s / 1h 5m`، `CopyButton` با متن displayContent بدون تگ‌های `<system-reminder>` |
| `src/vs/workbench/contrib/void/browser/react/out/*` (۹ فایل) | بازکامپایل با scope-tailwind + tsup (ابزار پین‌شده در `tools/.verify/package.json`) |

نکته‌ی تایپ: `SidebarChat.tsx` تایپ `ChatMessage` را مستقیم از
`common/chatThreadServiceTypes.js` import می‌کند (خط 26) — هیچ کپیِ تایپ
محلی وجود ندارد. `CopyButton` (در `ApplyBlockHoverButtons.tsx` خط 73) از
`IClipboardService` استفاده می‌کند (خط 77-88)، نه `navigator.clipboard` —
یعنی مسیر تأییدشده‌ی کلیپ‌بورد پنجره‌ی اصلی.

### 1.3) پچ‌های جدید live-patch (۷ تا؛ مجموعاً 97 patch + 2 prepend)

نام‌های دقیق (همان رشته‌هایی که `--verify` چاپ می‌کند):

```
chat durationMs: stamp on error-path assistant commit
chat durationMs: stamp on success assistant commit
chat footer: run duration + copy message (MTs copy)
chat footer: run duration + copy message (V2s copy)
chat footer: run duration + copy message (kzs copy)
chat footer: run duration + copy message (Kjs copy)
chat footer: run duration + copy message (VJs copy)
```

ساختار کد در `tools/live-patch.py`: دو تاپل literal برای durationMs +
تابع سازنده‌ی `_footer_anchor/_footer_replacement` که با لیست
`[(next_def, jsx_runtime) × 5]` پچ‌های فوتر را می‌سازد. منطق فوترِ تزریق‌شده:
استایل inline (چون CSS اسکوپ‌شده‌ی tailwind بیلد نصب، کلاس‌های جدید را
نمی‌شناسد)، children داخل props (automatic JSX runtime)، دکمه‌ی کپی از
`globalThis.__niCopy` (prepend موجود) با fallback به `navigator.clipboard`
اگر prepend نبود.

### 1.4) publish روی گیت

| چی | کجا |
|---|---|
| PR #139 (آپدیت شد) | https://github.com/NeuralInverse/neuralinverse/pull/139 — head جدید: `17375b25213` روی `aref-alapour:upstream/ledger-and-agent-fixes` |
| کامنت توضیحی روی PR | https://github.com/NeuralInverse/neuralinverse/pull/139#issuecomment-5561603142 |
| Issue جدید #141 | https://github.com/NeuralInverse/neuralinverse/issues/141 |
| شاخه کامل (با tools و docs) | `origin/feat/context-ledger` (جدید روی fork) |

شاخه‌ی PR با `git checkout feat/context-ledger -- src` روی `fdae16d723`
ساخته شد (کل src جایگزین؛ **۷۴ فایل** — تصحیح ۲۰۲۶-۰۹-۰۶: عدد «۳۴» در نسخه‌ی
اول این سند غلط بود؛ `gh pr diff 139 --name-only | wc -l` → ۷۴، شامل ۹ آرتیفکت
`react/out` و ۹ فایل تست. هر ۷۴ فایل زیر `src/` هستند، پس نشتِ
tools/AGENTS.local.md/تسک رخ نداده — طبق قاعده‌ی carve در `AGENTS.local.md`
محلی که در main است).

## ۲) گیت‌های ولیدیشن — خودت اجرا کن (از ریشه‌ی `C:\Users\jobal\dev\neuralinverse`)

```bash
git log --oneline -4     # انتظار: e60945c1 → aca402af → 64ee3245 → 4e40311e
git status --porcelain   # انتظار: فقط ۳ فایل scratch تِرَک‌نشده:
                          #   tools/.verify/apply-admin.log , verify-admin.log , screenshot-small.jpg
```

```bash
node tools/run-tests-standalone.mjs 2>&1 | tail -1
# انتظار (خروجی واقعی امروز): tests      : 96 passed, 0 failed
```

```bash
node tools/typecheck-slice.mjs 2>&1 | tail -2
# انتظار (خروجی واقعی امروز):
#   type-check : 28 files, 10,589 lines — 0 error(s), 291 out-of-slice dependency diagnostics (sparse-checkout artifacts, ignored)
```

```bash
python tools/live-patch-selftest.py 2>&1 | tail -1
# انتظار: live-patch selftest: all scenarios passed
# (سناریو ۳ داخلش "99 OK, nothing missing/pending" چاپ می‌کند؛ اعداد از len(PATCHES) داینامیک می‌آیند)
```

آنکرهای ۷ پچ جدید باید در باندلِ نصب و `.orig` هرکدام **دقیقاً ۱ بار**
باشند (read-only؛ بدون elevation خواندنی است):

```bash
python - <<'EOF'
p = r"C:\Program Files\NeuralInverse\resources\app\out\vs\workbench\workbench.desktop.main.js"
cur = open(p, encoding='utf-8', errors='replace').read()
org = open(p + ".orig", encoding='utf-8', errors='replace').read()
A = {
 "A1": '{role:"assistant",displayContent:te,reasoning:ge,anthropicReasoning:null}),pe&&pe.name&&pe.name!=="tool_call"',
 "A2": '{role:"assistant",displayContent:ne.fullText,reasoning:ne.fullReasoning,anthropicReasoning:ne.anthropicReasoning})',
 "B1": 'isLinkDetectionEnabled:!0})})})]})}),MTs=iw.default.memo',
 "B2": 'isLinkDetectionEnabled:!0})})})]})}),V2s=ow.default.memo',
 "B3": 'isLinkDetectionEnabled:!0})})})]})}),kzs=Wu.default.memo',
 "B4": 'isLinkDetectionEnabled:!0})})})]})}),Kjs=rw.default.memo',
 "B5": 'isLinkDetectionEnabled:!0})})})]})}),VJs=aw.default.memo',
}
for k, a in A.items():
    print(k, "cur=", cur.count(a), "orig=", org.count(a))   # انتظار: همه 1 1
EOF
```

پارسِ باندلِ پچ‌شده (read-only):

```bash
node --check "/c/Program Files/NeuralInverse/resources/app/out/vs/workbench/workbench.desktop.main.js" && echo OK
# انتظار: OK   و grep -c durationMs روی همان فایل امروز 46 بود
```

لاگ renderer بعد از ری‌استارتِ پس از اعمال (پوشه‌ی جدید در زمان ری‌استارت،
امروز `20260906T224744`):

```bash
grep -iE "uncaught|TypeError|ReferenceError|SyntaxError|Minified React error" \
  "/c/Users/jobal/AppData/Roaming/NeuralInverse/logs/<newest>/window1/renderer.log"
# انتظار: خالی (امروز خالی بود)
```

**ELEVATED — فقط با تأیید مالک** (پیش‌نیازش بسته بودن NeuralInverse یا
قبول اینکه فقط verify است):

```bat
python tools/live-patch.py --verify
# انتظار (خروجی واقعی امروز): 99 OK, 0 PENDING, 0 MISSING  (exit 0)
```

وضعیت روی گیت‌هاب:

```bash
git ls-remote origin upstream/ledger-and-agent-fixes   # انتظار: 17375b25213...
gh pr view 139  --repo NeuralInverse/neuralinverse --json state,headRefOid
gh issue view 141 --repo NeuralInverse/neuralinverse --json state,title
```

## ۳) تصمیم‌های پرریسک + مستنداتشان

**D1 — فوتر با جراحی مینیفای‌شده، در ۵ کپی.** کامپوننت
`AssistantMessageComponent` پنج بار در باندل هست (به‌ازای هر entry point
باندل‌شده). هر پنج کپی destructuring یکسان دارند
(`chatMessage:i,isCheckpointGhost:e,isCommitted:t,messageIdx:n`) و فقط alias
runtime متفاوت است (`yt/wt/tt/St/Ct`) و نام کامپوننت بعدی
(`MTs=/V2s=/kzs=/Kjs=/VJs=`) که در آنکر آمده. نقطه‌ی درج: بعد از
بلاک displayContent و قبل از بستن آرایه‌ی children فرگمنت. children داخل
props چون automatic runtime است (`jsx(type, config)` — آرگومان سوم key است،
نه child).

**D2 — منبع زمان: متغیر `v`.** در بیلد نصب، `const v=Date.now(),y=50`
(آفست 11527900؛ متناظر `_loopStartMs`/`MAX_MESSAGES_SENT` سورس). همان `v`
در متریک‌های `"Agent Loop Done (Aborted)"` (آفست 11530922) و
`"Agent Loop Done"` (11536007) استفاده می‌شود. هر دو سایت commit (11532337
خطای non-retryable و 11532739 موفق) بین این‌ها هستند. بررسی shadow با
اسکن regex بین تعریف و سایت‌ها: صفر مورد. **آفست‌ها فقط برای همین بیلد
(1.99.3 امروز) معتبرند.**

**D3 — `__niCopy`.** پنجره‌ی اصلی `clipboard-sanitized-write` را deny
می‌کند؛ prepend موجود `globalThis.__niCopy` (execCommand + textarea) + ۷
سایت بازنویسی‌شده‌ی `navigator.clipboard.writeText`. دکمه‌ی فوترِ تزریق‌شده
`__niCopy` را صدا می‌زند و اگر نبود به `navigator.clipboard` برمی‌گردد.

**D4 — شاخه‌ی PR با path-checkout.** `git checkout -B pr/… fdae16d723` سپس
`git checkout feat/context-ledger -- src` — یعنی کل src با وضعیت نهایی
جایگزین شد، نه cherry-pick. نتیجه: هر چیزی که در working treeِ سورس بوده
(شامل کار دیروزِ هنوز push‌نشده به شاخه‌ی upstream مثل oss-tools/oss-agent)
هم وارد PR شده. **دامنه‌ی PR ۷۴ فایل است، ولی ریویوی دستی فقط روی زیرمجموعه‌ی
۳۴ فایلی انجام شد** — یعنی ~۴۰ فایل بدون بازبینی چشمی وارد PR شده‌اند؛
بازبینی مستقل در Q7 اجباری است.

**D5 — سایت abort عمداً live-patch نشد.** در HEAD، `abortRunning` هیچ
loop-start ای در scope ندارد؛ در نصب، پیام‌های abort شده فوتر زمان نمی‌گیرند
(فقط سورس، با `_activeLoopStartMs`، دارد). پذیرفته‌شده تا بیلد بعدی.

## ۴) نقاط ضعف شناخته‌شده — صادقانه (این‌ها را با شدت بررسی کن)

- **W1 (مهم‌ترین، سورس): رِیس `_activeLoopStartMs`.** فیلد تک‌مقداری روی
  سرویس است. اگر دو thread همزمان agent run کنند، دومی مقدار اولی را
  بازنویسی می‌کند و clear در پایانِ هر حلقه، مقدار دیگری را null می‌کند →
  duration غلط/صفر. پچ باندل (`v` لوکالِ هر فراخوانی) این مشکل را **ندارد**.
  جهت درست: کلید بر اساس threadId (مثلاً داخل streamState). آیا معماری
  فعلاً اجازه‌ی دو حلقه‌ی همزمان می‌دهد؟ (Q2)
- **W2: تأیید بصریِ فوتر توسط مالک هنوز انجام نشده.** ری‌استارت شد و لاگ
  renderer پاک است، اما هیچ پیام جدیدی بعد از ری‌استارت تست نشده که فوتر را
  دید. طبق live-test gate، تا مالک تست نکند کار «done» نیست.
- **W3: پیام‌های قدیمی فوتر ندارند** (durationMs موقع ساختشان ذخیره
  نشده) — طراحی است، نه باگ؛ ولی در تست مالک باید گفته شود.
- **W4: پچ‌های امروز به نام‌های مینیفای وابسته‌اند** (`te/ge/pe/ne/v/MTs/…`).
  اولین آپدیت رسمی برنامه همه را MISSING می‌کند (by design؛ `--status`
  می‌گوید) و استخراج دوباره لازم است — با درس ghost-match پچ `pe` (سابقه‌ی
  ثبت‌شده در SUPERSEDES).
- **W5: اثبات unshadow بودن `v` هیوریستیک بود** (regex روی متن مینیفای)، نه
  AST. `node --check` فقط syntax را تضمین می‌کند. اگر shadow واقعی وجود
  داشت، ReferenceError یا duration غلط در ران‌تایم می‌داد — لاگ امروز پاک
  است ولی فقط اجرای واقعی agent قاطع است (همان تست W2).
- **W6: قضاوت اینکه سایت `{role:"assistant",displayContent:E??"",…}),[E,k])`
  (آفست ~10740380) commit پیام thread نیست** (الگوی useMemo + jsx بعدش؛
  `_addMessageToThread` ندارد). نظر دوم بخواه (Q6).
- **W7: خودتس‌ت `-6`.** شمارش chained exceptions در
  `tools/live-patch-selftest.py` به‌صورت `N_PATCHES - 6` هاردکد تفریق
  می‌شود؛ افزودن پچ chained بعدی بدون آپدیت این عدد، تست را می‌شکند.
- **W8: `react/out/*` آرتیفکت کامپایل است** و commit شده؛ با toolchain پین‌شده‌ی
  `tools/.verify` کامپایل شده ولی deterministic بودن خروجی tsup بین ماشین‌ها
  اثبات نشده. ضمناً دایرکتوری `react/out` در `.gitignore` است ولی فایل‌هایش
  force-track شده‌اند — یعنی `git add react/out/` فایل‌های جدید را
  **بی‌صدا** نمی‌اندازد داخل؛ ریسک فراموشی در کامپایل‌های بعدی.
- **W9: react src هیچ type-check واقعی ندارد** (esbuild/tsup فقط transpile
  می‌کند و `typecheck-slice.json` هم مسیرهای react src را پوشش نمی‌دهد).
  فوتر از نظر تایپ فقط با «build موفق» بررسی شده. برای این تغییر خاص
  ایمن است (import تایپ از common) ولی به‌عنوان گپ سیستمیک بدان.
- **W10: سازگاری storage.** `durationMs` فیلد اختیاری‌ست؛ thread های قدیمی
  (بدون فیلد) باید بدون خطا deserialize شوند و بیلدهای قدیمی‌تر هم باید
  فیلد ناشناخته را تحمل کنند — رفتار deserializer را کسی تست نکرده (Q10).
- **W11: سه فایل scratch تِرَک‌نشده** (`apply-admin.log`, `verify-admin.log`,
  `screenshot-small.jpg`) در `tools/.verify` — احتمال commit تصادفی در
  آینده؛ بهتر است قاعده‌ی ignore اضافه شود.
- **W12: ادعاهای issue #141** (ازجمله «14 min → 23 s» و «464-occurrence
  scan completes end-to-end» و «96 tests») همه به شواهد همین تسک‌ها
  برمی‌گردند؛ صحت‌سنجی متن در برابر واقعیت در Q9.
- **W13: دسترسی elevated** برای همه‌ی گیت‌های Program Files لازم است — تو
  بدون مالک نمی‌توانی re-verify کنی؛ آن را به‌عنوان محدودیت روش بنویس، نه
  سبز تلقی کن.
- **W14 (کوچک): accessibility فوتر تزریق‌شده** فقط `title` دارد؛ aria-label
  ندارد؛ روی تمرکز کیبورد بسته به استایل پیش‌فرض `<button>` است.
- **W15: متن «Fixes delivered in #139» در issue #141** عمداً از کلیدواژه‌ی
  `Fixes #139` خودکار-بسته اجتناب کرد؛ با قرارداد ریپو چک کن که اشکال ندارد.

## ۵) چک‌لیست adversarial — با شواهد جواب بده

1. **Q1 — همه‌ی مسیرهای commit پیام assistant را از سورس بشمار**
   (`grep -n "role: 'assistant'" src/vs/workbench/contrib/void/browser/chatThreadService.ts`).
   آیا بعد از این تغییرات هیچ مسیری هست که پیام assistant را بدون
   `durationMs` commit کند (به‌جز مسیرهای عمداً مستثنا)؟
2. **Q2 — آیا دو agent loop می‌تواند همزمان اجرا شود؟** (streamState
   per-thread است؛ گارد سراسری هست یا نه؟) اگر بله، W1 باگ واقعی است —
   شدت و طرح رفع (per-thread) را بنویس.
3. **Q3 — آنکرهای ۷ پچ را خودت در باندلِ فعلی و `.orig` بشمار** (اسکریپت
   بخش ۲). آیا همه 1/1 هستند؟ هیچ آنکری هست که زیررشته‌ی دیگری را هم match کند؟
4. **Q4 — با پارسر واقعی (مثلاً TypeScript compiler API از
   `tools/.verify/node_modules/typescript`) بررسی کن `v` بین تعریفش و دو
   سایت commit redeclare نشده باشد.** (تأیید یا ردِ W5.)
5. **Q5 — کانتکست ±200 کاراکتری هر پنج سایت فوتر را dump کن** و تأیید کن
   درج، ساختار آرایه‌ی children فرگمنت را حفظ کرده و به `]})})` پایانی
   می‌رسد.
6. **Q6 — آیا سایت ~10740380 (`displayContent:E??"",…),[E,k])`) یک مسیر
   commit واقعی است که باید durationMs می‌گرفت؟** (رد یا تأیید W6.)
7. **Q7 — دیف `fdae16d7239..17375b25213` را فایل‌به‌فایل برو؛** آیا چیزی
   خارج از دامنه‌ی موردنظر (فایل بلااستفاده، تغییر ناخواسته) وارد PR شده؟
8. **Q8 — با toolchain پین‌شده دوباره `react/out` را کامپایل کن و diff بگیر؛**
   آیا خروجی commit شده بازتولید می‌شود؟ (W8.)
9. **Q9 — هر ادعای issue #141 و کامنت PR #139 را به شاهد نگاشت کن؛**
   ادعای بی‌شاهد پیدا می‌شود؟
10. **Q10 — مسیر persist/load پیام‌های thread را پیدا کن** (serialization در
    chatThreadService) و بگو آیا فیلد ناشناخته/اختیاری از هر دو جهت (بیلد
    قدیمی می‌خواند جدید، برعکس) بی‌خطر است. (W10.)
11. **Q11 — تابع `_satisfies_engines_1_91` در `tools/live-patch.py`** —
    جدول درستی (1.90.0→stamp, 1.91.0→نstamp, 1.99.3→نstamp, 2.0.0→نstamp,
    1.127.0→نstamp, 1.89.9→stamp) را با کد تطبیق بده.
12. **Q12 — سورسِ فوتر از `CopyButton`/`IClipboardService` استفاده می‌کند؛**
    شواهد موجود که IClipboardService در پنجره‌ی اصلی واقعاً کار می‌کند چیست؟
    (دکمه‌های کپی code-block در چت، هم‌اکنون در نصب، همین مسیر را دارند —
    از مالک بخواه یکی را تست کند یا در کد permission را ردیابی کن.)

## ۶) تست مالک (هنوز انجام نشده — الزامِ «done» بودن)

1. یک پیام هرچی به agent بده؛ پس از تمام شدن پاسخ، زیر پیام باید
   `Xm Ys` + دکمه `COPY` باشد؛ کلیک روی COPY متن کامل پیام را (بدون
   تگ‌های system-reminder) در کلیپ‌بورد می‌گذارد و ۱.۲ ثانیه «Copied!»
   می‌نویسد.
2. یک تسک چنددقیقه‌ای بده؛ مدت روی فوتر باید تقریباً برابر زمان واقعی
   باشد (دقت: زمانِ کل حلقه‌ی agent از شروع تا commit پیام).
3. پیام‌های قدیمی (قبل از امروز) فوتر **ندارند** — طبیعی است.
4. اگر وسط کار agent را استاپ کنی، پیام abort شده در **نصب فعلی** فوتر
   زمان ندارد (فقط از بیلد بعدی از سورس دارد) — طبیعی است (W3/D5).

## ۷) مسیرها و فکت‌های کلیدی

| چی | مقدار |
|---|---|
| ریپو / شاخه کاری | `C:\Users\jobal\dev\neuralinverse` / `feat/context-ledger` |
| remotes | origin=aref-alapour/neuralinverse ، upstream=NeuralInverse/neuralinverse (fetch-only) |
| باندل نصب | `C:\Program Files\NeuralInverse\resources\app\out\vs\workbench\workbench.desktop.main.js` (+ `.orig`) |
| مانیفست live-patch | `C:\Program Files\NeuralInverse\resources\app\.ni-livepatch.json` |
| نسخه‌ی پایه‌ی نصب | VS Code base 1.99.3 (آفست‌های بخش ۳ فقط برای همین بیلد) |
| لاگ‌های کاربر | `%APPDATA%\NeuralInverse\logs\<timestamp>\window1\renderer.log` |
| toolchain ریاکت | `tools/.verify/node_modules` (پین در `tools/.verify/package.json`) |
| تست/ولیدیشن | `tools/run-tests-standalone.mjs` ، `tools/typecheck-slice.mjs` ، `tools/live-patch-selftest.py` |
| وضعیت فعلی نصب | 97 patch + 2 prepend: apply و --verify سبز (99 OK)؛ ری‌استارت شده؛ renderer پاک |

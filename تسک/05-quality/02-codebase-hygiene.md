# Q2 — بهداشت کدبیس (Hygiene)

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🟡 (اجرای ۲۰۲۶-۰۹-۰۸ — بندهای ۱ و ۳ روی
  working tree انجام شد؛ چک‌لیست زیر) | **وابستگی:** —
- **هم‌ارز در Cursor:** هیچ — این تسک کیفیت داخلی است ولی برای «حرفه‌ای بودن» ضروری است

## هدف
پاک‌سازی چیزهایی که کدبیس را غیرحرفه‌ای نشان می‌دهند و ریسک می‌سازند.

## فهرست کارها
1. **فایل‌های `.bak` داخل repo** ✅ **حذف‌شده ۲۰۲۶-۰۹-۰۸** (rm ساده؛ stage/commit توسط
   orchestrator در موج ۱ انجام شد). هفت فایل، دقیقاً مطابق ممیزی:
   - `src/vs/workbench/contrib/void/browser/chatThreadService.ts.bak`/`.bak2`/`.bak3`
   - `src/vs/workbench/contrib/powerMode/browser/powerModeTerminalHost.ts.bak`/`.bak2`/`.bak3`
   - `src/vs/workbench/contrib/void/browser/react/src/sidebar-tsx/AgentNetworkViz.tsx.bak`
   - مدرک عدم ارجاع: grep سراسری ریپو (کل فایل‌ها به‌جز node_modules/.git/تسک/projects)
     برای نام کامل هر فایل → صفر نتیجه؛ کپی‌های هم‌نام در `out/` فقط local و
     untracked هستند (زیر `/out*/` ignore می‌شوند) و دست نخورده ماندند.
2. **فایل `void/neuralInverse/browser/backgroundAgentService.js`** ⛔️ **حذف نشد —
   مرده نیست، shim باربر است** (بررسی ۲۰۲۶-۰۹-۰۸):
   - **منشأ:** commit ‏`f4ceedc44d4` («feat: add background agents with shadow
     validation») به‌همراه خودِ سرویس واقعی
     (`contrib/neuralInverse/browser/backgroundAgentService.ts`، ۲۸۷ خط) و
     import اشتباه‌عمق در `react/src/util/services.tsx:60` اضافه شد.
   - **مکانیزم:** import از `react/src/util/` با ۴ سطح `../` به
     `void/neuralInverse/browser/backgroundAgentService.js` (خودِ shim) می‌رسد نه
     با ۵ سطح به `contrib/neuralInverse/...` (فایل واقعی). tsup طبق `external`
     regex در `react/tsup.config.js` هر import ‏`../../../*.js` را external نگه
     می‌دارد → ۸ باندل از ۹ باندل کامپایل‌شده‌ی `react/out/` (همه به‌جز `diff`)
     همین مسیر را literal دارند و در runtime/build از طریق shim به سرویس واقعی
     resolve می‌شوند. shim هم در `.eslint-allowed-javascript-files:182` عمداً
     allowlist شده است.
   - **حذفش = شکستن** sidebar/quick-edit/settings/onboarding/tooltip/editor-widgets/
     agent-manager/artifact باندل‌ها.
   - **رفع درست (برای بعد، خارج از این تسک):** اصلاح عمق import در
     `services.tsx:60-61` به ۵ سطح + rebuild هر ۹ باندل + حذف shim و خط ۱۸۲
     eslint-allowlist، به‌صورت یک تغییر اتمیک.
3. **جلوگیری از تکرار** ✅ `*.bak*` به `.gitignore:50` اضافه شد (با
   `git check-ignore --no-index` تأیید شد). pre-commit check جدا لازم نیست تا
   تعریف شود — الگوی ignore + این تسک کافی است؛ اگر owner خواست، در
   `AGENTS.local.md` خط اضافه شود.
4. **مرور TODO های بحرانی:** 🔴 باز — خارج از دامنه‌ی تأییدشده‌ی اجرای ۰۹-۰۸:
   - قیمت‌ها/پنجره‌های context با `TODO!!! double check` در `modelCapabilities.ts`
     (فهرست به Q1 وصل است)
   - `getSessionCost()` (با Q1 بسته می‌شود)
   - autocomplete context TODO در `chatThreadService.ts:551`
   - جمع‌بندی در `تسک/05-quality/tech-debt.md` هنوز ساخته نشده.
5. ~~**بررسی live-patch marker ها**~~ → منتقل شد و کامل اجرا شد در
   [Q4 — یکپارچگی live-patch](04-live-patch-integrity.md) (ابزار `--verify`
   + `--status` + `--rebaseline` + manifest + selftest sandbox؛ ۲۰۲۶-۰۹-۰۵
   سبز). اینجا فقط مرجع می‌ماند؛ هر کاری در آن تسک انجام می‌شود.

## N5 — باندل‌های React هم‌زمان tracked و ignore (تصمیم با owner؛ اقدامی نشد)

وضعیت تأیید ۲۰۲۶-۰۹-۰۸: هر ۹ فایل `react/out/*/index.js` ترَک هستند **و**
`react/.gitignore:1` (`out/`) — که بر الگوی ریشه `.gitignore:33` مقدم است —
مطابقت دارند (نکته: `git check-ignore` برای فایل tracked به‌طور پیش‌فرض
«not ignored» برمی‌گرداند؛ باید `--no-index` داد). وابستگی: ۱۳ فایل سورس
(`sidebarPane.ts`، `editCodeService.ts`، `neuralInverseAgentPane.ts`، …) مستقیم
`react/out/*/index.js` را import می‌کنند و gulpfile هیچ مرحله‌ی build واکنش
ندارد (`buildreact` فقط npm script دستی است) — یعنی clone تازه بدون این
باندل‌ها کامپایل نمی‌شود.

گزینه‌ها (توصیه: گزینه A):

- **A (توصیه — فعلاً):** استثنای صریح در root `.gitignore`
  (`!src/vs/workbench/contrib/void/browser/react/out/**` یا فقط `!.../out/*/index.js`)
  و اصلاح/حذف خط `out/` در `react/.gitignore`. باندل‌ها عمداً tracked بمانند تا
  clone تازه کامپایل شود و `git add .` باندل rebuild شده را دیگر بی‌صدا جا
  نگذارد. هزینه: ۹ آرتیفکت مینیفای‌شده در git می‌مانند (diff noise).
- **B (وضعیت پایانی درست — در دامنه‌ی [Q7](07-source-build-campaign.md)):**
  خارج‌کردن آرتیفکت‌ها از ریپو + سیم‌کشی `npm run buildreact` به‌عنوان pre-step
  بیلد/CI. تا وقتی بیلد کامل از سورس وجود ندارد، ریسک شکستن clone تازه را دارد.
- **C (وضعیت فعلی):** تناقض می‌ماند — هر باندل جدید/تغییرکرده بعد از کامپایل
  بعدی بی‌صدا از `git add` جا می‌ماند. قابل قبول نیست.

## معیارهای پذیرش
- [x] `git ls-files | grep -E '\.bak'` خالی است — با commit موج ۱ (2026-09-08) سبز شد
- [x] فایل js مرده: بررسی شد — **مرده نبود، shim باربر است؛ حذف نشد** (بند ۲)
- [x] الگوی `*.bak*` در `.gitignore` (بند ۳)؛ `python tools/live-patch.py --verify`
  مربوط به Q4 است و طبق وضعیت ۲۰۲۶-۰۹-۰۶ سبز (۹۹ OK)
- [ ] فهرست TODO های باز در یک فایل `تسک/05-quality/tech-debt.md` جمع شود — 🔴 باز

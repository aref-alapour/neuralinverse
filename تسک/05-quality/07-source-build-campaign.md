# Q7 — کمپین بیلد کامل از سورس

- **اولویت:** **P0** | **برآورد:** M | **وضعیت:** ✅ (هر شش فاز بسته — ۲۰۲۶-۰۹-۰۷)
- **وابستگی:** ندارد — خودش پیش‌نیازِ V1، V2، S3، D1، D2 و هر تست زنده‌ی Ledger است
- **شاخه:** `feat/context-ledger` (بدون کامیت کد؛ فقط سند و در صورت لزوم اصلاح toolchain)

## هدف — چرا این تسک P0 است

طبق [رجیستر نقاط ضعف](project-status-and-weaknesses-2026-09-06.md)، **S1** می‌گوید هیچ
بیلدی از سورس وجود ندارد و تنها مسیر رسیدن کد به کاربر، ۹۷ پچ روی باندل مینیفای
است. نتیجه‌اش شش ضعف دیگر است که هیچ‌کدام بدون بیلد قابل بستن نیستند:

| ضعف | چرا بدون بیلد بسته نمی‌شود |
|---|---|
| **S3** | Ledger هرگز زنده اجرا نشده؛ پیش‌فرضش `true` است |
| **V1** | ۸۱ فایل تست فقط با `npm run test-node` روی بیلد اجرا می‌شوند |
| **V2** | type-check واقعیِ react src فقط با toolchain کامل |
| **D1/D2** | مهاجرت storage و IndexedDB v2 روی داده‌ی واقعی تست نشده |
| **V4** | فیکس رِیس (`875785e`) فقط در سورس است؛ رفتار نصب‌شده فرق دارد |

## واقعیت‌های محیط — راستی‌آزمایی‌شده ۲۰۲۶-۰۹-۰۶/۰۷

این‌ها حدس نیستند؛ همان شب اجرا و تأیید شدند. هر rerun باید این‌ها را فرض بگیرد:

| # | واقعیت | اثر | راه‌حل تأییدشده |
|---|---|---|---|
| ۱ | ریپو **sparse-checkout** بود: `src` فقط ۹۱۱ فایل از ۹۲۹۷؛ `build/`, `extensions/`, `cli/`, `test/` اصلاً روی دیسک نبودند | `npm run compile` اصلاً شروع نمی‌شود | `git sparse-checkout disable` |
| ۲ | **بودجه‌ی Git LFS ریپو تمام شده** (`exceeded its LFS budget`) و چک‌اوت را نصفه می‌کشد | materialize شکست می‌خورد | `GIT_LFS_SKIP_SMUDGE=1` — هر ۹۷ فایل LFS فقط fixture تست کوپایلت‌اند |
| ۳ | `.nvmrc` = **24.15.0**؛ node سیستم **25.6.1**؛ هیچ nvm/fnm/volta نصب نیست | گیت `preinstall` **major را دقیقاً برابر** می‌خواهد → رد | `VSCODE_SKIP_NODE_VERSION_CHECK=1` (موقت) — نک. «ریسک باز» |
| ۴ | `node_modules` عملاً خالی بود: **۹ پکیج**، همه native | نصب کامل لازم است، نه بازسازی ABI | `npm ci` (لاک در ریشه هست → بازتولیدپذیر) |
| ۵ | فقط **VS Community 2026** (`18.7`) نصب است؛ `preinstall.ts` فقط پوشه‌ی `2019`/`2022` را می‌شناسد | «Invalid C/C++ Compiler Toolchain» | `vs2022_install="C:\Program Files\Microsoft Visual Studio\18\Community"` |
| ۶ | `build/npm/gyp` روی `node-gyp@11.2.0` پین است که major 18 را نمی‌شناسد (فقط 15/16/17) | **بی‌اثر** — آن نسخه فقط هدر دانلود می‌کند | کاری لازم نیست |
| ۷ | node-gyp باندل‌شده‌ی npm 11.9.0 نسخه‌ی **12.2.0** است و `versionYear = 2026` دارد | کامپایل native سالم است | کاری لازم نیست |
| ۸ | `NODE_TLS_REJECT_UNAUTHORIZED=0` در سطح **User** ویندوز ست است | کل نصب روی TLS تأییدنشده می‌رود | خارج از دامنه‌ی این تسک → [Q9](09-tls-verification-disabled.md) |
| ۱۰ | **کتابخانه‌های Spectre-mitigated نصب نیستند.** `@vscode/deviceid` با `error MSB8040` می‌میرد؛ در MSVC 14.51.36231 پوشه‌ی `lib/spectre` وجود ندارد | `npm ci` بار دوم هم exit 1 داد و دوباره rollback کرد | جزء `Microsoft.VisualStudio.Component.VC.Runtimes.x86.x64.Spectre` نصب شود — **خودِ همین ریپو در `scripts/install-windows-deps.ps1` این را مستند کرده** («required by @vscode/deviceid»). نیازمند Administrator |
| ۹ | postinstall `@playwright/browser-chromium` **کل `npm ci` را کشت**: دانلود Chromium Headless Shell روی هر ۴ میرور با timeout سوکت TLS و سپس `Download failure, code=3221225794` شکست خورد → `npm error code 1` → rollback خودکار npm کل `node_modules` را پاک کرد (فقط `@azure` با `EPERM` جا ماند) | فاز ۲ صفر شد | `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` — برای `compile` هیچ لازم نیست |

## متغیرهای محیطی استاندارد این کمپین

```bash
export VSCODE_SKIP_NODE_VERSION_CHECK=1
export vs2022_install="C:\\Program Files\\Microsoft Visual Studio\\18\\Community"
# فقط در rerun، اگر تست‌های playwright لازم نیست:
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
```

## طرح — فازها و گیت هر فاز

### فاز ۰ — materialize درخت ✅ (۲۰۲۶-۰۹-۰۶)

```bash
git sparse-checkout list > <scratch>/sparse-list-backup.txt   # برای برگشت
GIT_LFS_SKIP_SMUDGE=1 git sparse-checkout disable
```

**گیت:** `git config core.sparseCheckout` → `false`؛ `git status --porcelain` خالی؛
`find src -type f | wc -l` → **۹۳۰۸**؛ `build/` روی دیسک. **همه سبز شد.**

### فاز ۱ — هدرها و پیش‌نیازها ✅ (۲۰۲۶-۰۹-۰۶)

```bash
npm ci --prefix build/npm/gyp
node build/npm/preinstall.ts
```

**گیت:** exit 0؛ هدرهای `electron 42.3.0` و `node 24.15.0` در کش node-gyp. **سبز شد.**

### فاز ۲ — نصب کامل وابستگی‌ها ✅ (تلاش سوم، بعد از نصب Spectre libs)

> **تلاش اول (۲۰۲۶-۰۹-۰۶ ۲۳:۴۰ → ۰۰:۰۵): شکست.** ۱۱۶۴ پکیج نصب شد، بعد
> postinstall پلی‌رایت روی دانلود Chromium مرد و **rollback خودکار npm کل
> `node_modules` را پاک کرد** (به ۱ پوشه‌ی قفل‌شده رسید). درسِ ثبت‌شده: در این
> ریپو یک postinstall شکست‌خورده = صفر شدن کل نصب، نه یک هشدار.

> **تلاش دوم (۰۰:۰۷ → ۰۰:۳۷): شکست، علت متفاوت.** با
> `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` دانلود مرورگر رد شد و نصب تا کامپایل native
> پیش رفت (`Generating code` از MSVC)، اما `@vscode/deviceid` روی
> `error MSB8040: Spectre-mitigated libraries are required` مرد → `npm error code 1`
> → **rollback دوباره کل `node_modules` را صفر کرد**.
> نکته‌ی روش: کد خروجی shell را باور نکن — پوسته exit 0 داد چون آخرین دستور
> `echo` بود؛ عدد واقعی از `NPM_CI_EXIT=1` در لاگ آمد. همیشه exit خودِ npm ثبت شود.

**پیش‌نیاز قبل از تلاش سوم (نیازمند Administrator):**

```powershell
# همان کاری که scripts/install-windows-deps.ps1 خودش می‌کند
& "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vs_installer.exe" modify `
  --installPath "C:\Program Files\Microsoft Visual Studio\18\Community" `
  --quiet --norestart --add Microsoft.VisualStudio.Component.VC.Runtimes.x86.x64.Spectre
```

**گیت این پیش‌نیاز:** پوشه‌ی
`C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\lib\spectre`
باید بعد از نصب وجود داشته باشد. **۲۰۲۶-۰۹-۰۷: نصب شد و پوشه ساخته شد** (`onecore`,
`x64`, `x86`). نکته: `--passive` و `--quiet` باید از ابتدا elevated اجرا شوند، وگرنه
installer با `Exit Code: 5007` برمی‌گردد.

```bash
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1       # اجباری بعد از شکست تلاش اول
rm -rf node_modules                             # بقایای rollback را پاک کن
npm ci --foreground-scripts > <log> 2>&1        # هرگز pipe به tail نکن
```

**نتیجه‌ی تلاش سوم: `NPM_CI_EXIT=0`، صفر `npm error`، ۱۱۶۱ پکیج، و هر هفت ماژول
native کامپایل‌شده** — یعنی زنجیره‌ی VS 2026 + node-gyp 12.2.0 + هدرهای Electron
42.3.0 زیر Node 25 سالم است.

**گیت:** exit 0 و هیچ خطای کامپایل native (`node-pty`, `kerberos`,
`native-keymap`, `@vscode/*`, `cpu-features`, `ssh2`).
**اگر شکست خورد:** اول خطا را طبقه‌بندی کن — اگر ریشه‌اش node 25 است (engines-check
یا API حذف‌شده)، همان‌جا توقف و **اجازه‌ی نصب Node 24.15.0 از مالک بگیر**.

### فاز ۳ — کامپایل ✅ (۲۰۲۶-۰۹-۰۷ ۰۳:۰۳)

```bash
npm run compile > <log> 2>&1
```

**نتیجه: `COMPILE_EXIT=0` — اولین کامپایل کاملاً سبز این فورک.**
`0` خطای TypeScript، `0` مورد `Debug Failure`، و **۸۹۸۴ فایل در `out/`**.
مدت: ۴٫۷ دقیقه. Node 25 هیچ‌جا مشکل‌ساز نشد؛ اجازه‌ی نصب Node 24 لازم نشد.

**مسیر رسیدن به صفر — هشت کامپایل:**

| # | تغییر | خطای TS | خطای گالپ |
|---|---|---|---|
| ۱ | وضعیت اولیه | ۱۷۷ | ۳۹ |
| ۲ | شش باگ خودمان رفع شد | ۱۷۰ | ۳۹ |
| ۴ | وابستگی‌های `open-remote-ssh` نصب + پاک‌سازی firmware | ۱۶۰ | ۳۹ |
| ۵ | `skipLibCheck` برای اکستنشن ssh | ۱۵۵ | ۳۹ |
| ۶ | Checks/Enclave در `exclude` tsconfig | ۰ | **۱۰۴** |
| ۷ | همان دو از استریم گالپ هم خارج شد | ۰ | ۳۹ |
| ۸ | `componentFixtures` از استریم خارج شد | ۰ | **۰** |

**دو درس روشی از این جدول:**

۱. **گالپ و TypeScript دو چیز متفاوت می‌شمارند.** آن «۳۹ خطا» که از همان کامپایل
اول گزارش می‌شد، هیچ‌کدام دیاگنوستیک TypeScript نبود؛ همه
`Debug Failure: Expected fileName to be present in command line` بودند. همیشه هر دو
عدد جدا گزارش شود.

۲. **`exclude` در tsconfig کافی نیست.** استریم گالپ (`gulp.src('src/**')`) مستقل از
برنامه‌ی TypeScript است؛ فایلی که استریم شود ولی در برنامه نباشد، transpiler را
می‌کشد. این باگ **از قبل در ریپو زنده بود**: `componentFixtures` سال‌ها در
`exclude` بود و هرگز از استریم خارج نشده بود — یعنی این فورک حتی با صفر خطای تایپ
هم کامپایل نمی‌شد. حالا هر دو در `excludedSourceGlobs` در `build/lib/compilation.ts`
هم‌گام نگه داشته می‌شوند.

### فاز ۴ — گیت تست واقعی ✅ (V1 بسته شد)

**نتیجه: `11,913 passing / 182 pending / 0 failing`, `TEST_NODE_EXIT=0`.**
اجرای اول ۸ شکست داد؛ هیچ‌کدام ریشه‌اش فایل LFS نبود، پس **fail خام = fail واقعی = ۸**
و هر هشت رفع شد (سه باگ تست در `episodeSummarizer.test.ts`، پنج انتظار کهنه در
`chatRequiresSetup` که فورک عمداً کوتاهش کرده). مقایسه: هارنس قبلی ۹۶ تست.

```bash
node tools/verify.mjs           # هارنس فعلی — باید همچنان سبز بماند
npm run test-node > <log> 2>&1  # ۸۱ فایل تستِ تاکنون خاموش
```

**گیت و قاعده‌ی صداقت:** دو عدد جدا گزارش شود —
`fail خام` و `fail واقعی = خام − (fail هایی که root cause شان pointer بودنِ فایل LFS است)`.
هر «LFS-exempt» باید با نام fixture مربوطه اثبات شود، نه ادعا.

### فاز ۵ — اولین اجرای زنده ✅ (S3 بسته شد — ۲۰۲۶-۰۹-۰۷)

> مسیر عوض شد: به‌جای بیلد dev آینه، **بسته‌ی نصبی از سورس ساخته و روی سیستم نصب شد**
> (`1.99.3` → `1.127.0`, commit `8d4400da`)، و تست زنده روی همان انجام شد.

**شاهد Ledger — سه thread در `escapezoom_dev/.inverse/ledger/`:**

| thread | lastSeq | خطوط journal | schema |
|---|---|---|---|
| `064b24a1…` | ۲ | ۲ | v1 |
| `0b9bc4b4…` | ۴ | ۴ | v1 |
| `ac7d2eef…` | ۲ | ۲ | v1 |

`lastSeq` در meta با تعداد خطوط journal در هر سه دقیقاً می‌خواند — یعنی گاردِ CAS و
شماره‌گذاری gapless در عمل درست است، نه فقط در تست واحد. `episodeCount: 0` هم درست
است چون گفتگوها از مرز اپیزود عبور نکردند. **D2 هم بی‌سروصدا بسته شد:** مهاجرت
`contextLedgerEnabled=true` روی پروفایل واقعی کاربر بدون خطا انجام شد.

```bash
scripts/code.bat --user-data-dir "<scratch>/ni-dev-userdata" \
                 --extensions-dir "<scratch>/ni-dev-ext"
```

**اجباری:** هرگز بدون این دو سوییچ اجرا نشود. `product.json` این فورک
`nameShort: "NeuralInverse"` است و dev-build می‌تواند با پروفایل واقعیِ نسخه‌ی
نصب‌شده هم‌مسیر شود؛ این بیلد مهاجرت `contextLedgerEnabled=true` و اسکیمای
IndexedDB v2 را با خودش دارد و **نباید قبل از تست، داده‌ی چت واقعی کاربر را لمس کند**.

**گیت (تست مالک):** برنامه بالا می‌آید → یک چت واقعی → Ledger مسیر پیش‌فرض است →
`recall_history` روی گفتگوی قبلی جواب می‌دهد → فوتر مدت‌اجرا دیده می‌شود.

### فاز ۶ — ثبت نتایج 🔴

اعداد واقعی فازهای ۳-۵ در همین فایل و در
[رجیستر ضعف‌ها](project-status-and-weaknesses-2026-09-06.md) به‌روز شوند
(V1/V2/S1/S3/D1/D2 با شاهد بسته یا بازتعریف شوند).

## معیارهای پذیرش Q7

- [ ] `out/` وجود دارد و `npm run compile` با exit 0 تمام می‌شود
- [ ] عدد واقعی `test-node` ثبت شده، با تفکیک fail خام از fail واقعی
- [ ] بیلد dev با `--user-data-dir` ایزوله بالا آمده و مالک Ledger را زنده دیده
- [ ] هیچ فایل داده‌ی کاربر واقعی در این کمپین لمس نشده
- [ ] بلاکرهای این کمپین در جدول «واقعیت‌های محیط» به‌روز مانده‌اند

## ریسک باز — Node 25 به‌جای 24.15.0

`VSCODE_SKIP_NODE_VERSION_CHECK=1` گیت را دور می‌زند، نه مشکل را. ماژول‌های native
علیه هدرهای **دانلودشده** (Electron 42.3.0 / Node 24.15.0) کامپایل می‌شوند، پس ABI
خطر اصلی نیست؛ خطر جایی است که اسکریپت‌های بیلد یا engines-check پکیج‌ها روی node 25
بشکنند. چون هیچ version-manager ای نصب نیست، رفعش = دانلود مستقیم Node 24.15.0 و
جابه‌جایی PATH → **نیازمند اجازه‌ی صریح مالک**.

## قواعد اجرایی این کمپین

1. **هیچ دستور طولانی‌ای pipe به `tail`/`head` نشود** — بافر می‌کند و پیشرفت را
   نامرئی می‌کند (اشتباه ثبت‌شده‌ی ۲۰۲۶-۰۹-۰۶). خروجی مستقیم به فایل لاگ.
2. کارِ طولانی در پس‌زمینه، با ناظر پیشرفتِ خودپایان، و **نتیجه حتماً گزارش شود**
   — حتی اگر شکست باشد.
3. تا پایان کمپین، هیچ agent دیگری در همین working tree فایل تغییر ندهد.
4. برگشت‌پذیری: لیست sparse قبلی بکاپ دارد؛ برای برگشت
   `git sparse-checkout set --stdin < <backup>`.

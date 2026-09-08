# Q14 — بسته‌بندی ویندوز می‌شکند: SDK کوپایلت در خروجی نیست

- **اولویت:** **P0 برای انتشار** | **برآورد:** M | **وضعیت:** 🟡 بسته‌بندی و installer سبز شدند (`93189d61e72`)؛ نصب و تست owner باز
- **کشف:** ۲۰۲۶-۰۹-۰۸، حین اجرای «بیلد و نصب از HEAD»
- **مهم:** این نقص **از قبل وجود داشته** و ربطی به موج‌های ۱–۳ ندارد

## علائم

```bash
export VSCODE_SKIP_NODE_VERSION_CHECK=1 PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
npm run gulp vscode-win32-x64
# → 'vscode-win32-x64' errored after 46 min
# → Error: [prepareBuiltInCopilotRipgrepShim] Copilot SDK directory not found at
#   C:\Users\jobal\dev\VSCode-win32-x64\resources\app\extensions\copilot\node_modules\@github\copilot\sdk
```

کامپایل قبلش کاملاً سبز است (`npm run compile` → exit 0، صفر خطای TS، ۹۰۲۶ فایل).
شکست فقط در مرحله‌ی بسته‌بندی است.

## آنچه تا اینجا ثابت شده

**۱. `sdk/` در سورس هست و ۳۳ فایل دارد:**

```bash
find extensions/copilot/node_modules/@github/copilot/sdk -type f | wc -l   # ۳۳
```

**۲. در خروجی بسته‌بندی کلاً نیست.** مقایسه‌ی دو طرف نشان می‌دهد این‌ها حذف شده‌اند:
`sdk`، `ripgrep`، `prebuilds`، `clipboard`، `foundry-local-sdk`، `pvrecorder`، `README.md`.

```bash
ls extensions/copilot/node_modules/@github/copilot/          # سورس
ls ../VSCode-win32-x64/resources/app/extensions/copilot/node_modules/@github/copilot/
```

**۳. `.moduleignore` قطعاً علت نیست — تجربی رد شد.** قوانین روی ۳۳ فایل واقعی
`sdk/` اجرا شد: **۳۱ تا می‌مانند**، فقط `index.js` (قانون ۲۱۸) و `index.d.ts`
(قانون عمومی `**/*.ts`) حذف می‌شوند.

```bash
node -e "
const fs=require('fs'),path=require('path');
const mmMod=require('minimatch'); const mm=typeof mmMod==='function'?mmMod:(mmMod.minimatch||mmMod.default);
const rules=fs.readFileSync('build/.moduleignore','utf8').split(/\r?\n/g).map(l=>l.trim()).filter(l=>l&&!/^#/.test(l));
const excludes=rules.filter(l=>!/^!/.test(l)).map(l=>'**/node_modules/'+l);
const base='extensions/copilot/node_modules/@github/copilot/sdk';
const walk=d=>fs.readdirSync(d,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(d,e.name)):[path.join(d,e.name)]);
const files=walk(base).map(f=>f.split(path.sep).join('/'));
let kept=0,dropped=0; for(const f of files){ excludes.find(e=>mm(f,e)) ? dropped++ : kept++; }
console.log('total',files.length,'kept',kept,'dropped',dropped);"
# → total 33 kept 31 dropped 2
```

**۴. مسیر جمع‌آوری وابستگی درست کار می‌کند.** ابتدا به اشتباه فکر کردم
`getProductionDependencies('extensions/')` مقصر است (فقط ۱ وابستگی برمی‌گرداند —
`typescript`)، ولی این طراحی است: آن فایل فقط وابستگی‌های **مشترک** را دارد.
کوپایلت مسیر اختصاصی خودش را دارد (`packageCopilotExtensionStream`،
`extensions.ts:464`) و آن درست است:

```bash
node --experimental-strip-types -e "
import('./build/lib/dependencies.ts').then(m=>{
  const d=m.getProductionDependencies('extensions/copilot');
  console.log('total:', d.length);
  d.filter(x=>x.includes('@github')).forEach(x=>console.log(' ', x));});"
# → total: 323، شامل @github/copilot
```

**۵. 🎯 نقطه‌ی افت دقیقاً مشخص شد: `sdk/` در `.build` هست و در اپ نهایی نیست.**

```bash
ls -d .build/extensions/copilot/node_modules/@github/copilot/sdk        # هست
ls -d ../VSCode-win32-x64/resources/app/extensions/copilot/node_modules/@github/copilot/sdk   # نیست
```

یعنی `packageCopilotExtensionStream` وظیفه‌اش را درست انجام داده و افت **در
مونتاژ نهایی** (`packageTask` در `gulpfile.vscode.ts`) رخ می‌دهد — همان‌جا که
خط ۲۷۱ `.build/extensions/**` را کپی می‌کند.

**۶. ترتیب taskها درست است** (`gulpfile.vscode.ts:643-647`): ابتدا `rimraf`، بعد
`packageTask`، بعد `prepareCopilotRipgrepShimTask`. پس فرضیه‌ی «shim زودتر از کپی
اجرا می‌شود» رد شد.

**قدم بعدی برای هرکس این را برمی‌دارد:** تنها شکاف باقی‌مانده داخل `packageTask`
است — بین `gulp.src(['.build/extensions/**'], { base: '.build', dot: true })` در
خط ۲۷۱ و آنچه واقعاً روی دیسک می‌نشیند. کاندیداها: فیلتری در ادامه‌ی همان
pipeline، یا `createAsar`، یا محدودیت طول مسیر ویندوز روی مسیرهای عمیق
(`sdk/tgrep/bin/...` نسبتاً عمیق است و ویندوز سقف ۲۶۰ کاراکتری دارد — این را
راستی‌آزمایی نکردم و کاندیدای جدی است).

**۴. تناقض قرارداد:** `.moduleignore` عمداً `sdk/index.js`، `ripgrep/**` و
`prebuilds/**` را حذف می‌کند، ولی `prepareBuiltInCopilotRipgrepShim`
(`build/lib/copilot.ts:290`) وجود `sdk/` را الزامی می‌داند و می‌خواهد shim را در
`sdk/ripgrep/bin/<platformArch>` بگذارد. این دو با هم سازگار نیستند.

**۵. کار ما نیست:** هر دو فایل درگیر آخرین بار در `2d68ded2f2b` عوض شده‌اند —
کامیتی **قبل از** بیلد نصب‌شده‌ی فعلی.

```bash
git log --oneline 8d4400dad69..HEAD -- build/.moduleignore build/lib/copilot.ts build/gulpfile.vscode.ts
# → خالی
```

## سؤال باز — بیلد نصب‌شده‌ی فعلی چطور ساخته شد؟

[Q7](07-source-build-campaign.md) فاز ۵ می‌گوید بسته‌ی نصبی از سورس ساخته و نصب شد
(`1.127.0`, commit `8d4400da`). ولی همان مسیر امروز می‌شکند. سه احتمال، و پاسخ
تعیین می‌کند اصلاً چه چیزی باید رفع شود:

1. آن بیلد از مسیر دیگری ساخته شد (نه `vscode-win32-x64`)
2. آن موقع هم شکست و به‌صورت دستی دور زده شد
3. `extensions/copilot/node_modules` بین آن زمان و حالا دوباره نصب شده و محتوایش
   فرق کرده

**اولین قدم این تسک، جواب‌دادن به همین سؤال است** — نه دست‌زدن به pipeline.

## دامنه‌ی پیشنهادی

سؤال محصولی مقدم: **آیا اصلاً به افزونه‌ی کوپایلت در بسته نیاز داریم؟** agent این
فورک `voidModelProvider` است، نه کوپایلت. اگر پاسخ منفی است، ساده‌ترین رفع، خارج
کردن این افزونه از بسته‌بندی است — که هم این شکست را حذف می‌کند، هم اندازه‌ی بسته
را کم می‌کند، هم مسئله‌ی مارکت‌پلیس (زیر) را کوچک‌تر می‌کند.

## مسئله‌ی جانبیِ کشف‌شده در همین اجرا

`product.json` قابل کامیت نیست چون گیت hygiene وجود `extensionsGallery` را رد
می‌کند — و آن گیت **درست عمل می‌کند**:

```bash
node -e "console.log(require('./product.json').extensionsGallery.serviceUrl)"
# → https://marketplace.visualstudio.com/_apis/public/gallery
```

فورک به مارکت‌پلیس خود مایکروسافت وصل است، که شرایط استفاده‌اش را برای محصولات
غیر-VS Code نقض می‌کند. برای پروژه‌ای که قرار است عمومی شود این ریسک واقعی است.
**تصمیم مالک:** مهاجرت به Open VSX، یا پذیرش آگاهانه. تا آن زمان `product.json`
فقط با bypass قابل کامیت است و در درخت کاری می‌ماند.

## ✅ رفع (۲۰۲۶-۰۹-۰۸، کامیت `93189d61e72`)

چهار پیش‌نیاز CI پشت سر هم مانع بودند. هر چهار حالا **شرطی** اند، نه فرض‌شده:

| # | مانع | رفع |
|---|---|---|
| ۱ | SDK کوپایلت پیدا نمی‌شد | فلگ `includeBuiltInCopilotExtension = false` (تصمیم محصولی مالک) — سه نقطه‌ی اتصال گارد شد |
| ۲ | `signtool.exe ENOENT` | `ENOENT` → «امضا ندارد، strip لازم نیست» + هشدار یک‌باره؛ هر خطای spawn دیگر همچنان fatal |
| ۳ | `tools\*` غایب | `vscode-win32-x64-inno-updater` باید **قبل از** setup اجرا شود (در series آن نیست) |
| ۴ | `appx/code_x64.appx` غایب | بلوک appx فقط وقتی artifact روی دیسک باشد تعریف می‌شود + هشدار |

**نتیجه:**

```bash
npm run gulp vscode-win32-x64                # exit 0، ۲۰ دقیقه
npm run gulp vscode-win32-x64-inno-updater   # exit 0
npm run gulp vscode-win32-x64-system-setup   # exit 0
# → .build/win32-x64/system-setup/VSCodeSetup.exe  (۲۲۱ MB)
#   nameLong=NeuralInverse، version=1.127.0، commit=e6fc416a2b7
```

**جواب سؤال باز بخش قبل:** بیلد نصب‌شده‌ی قبلی (`8d4400da`) احتمالاً هرگز از این
مسیر ساخته نشده — هر چهار مانع، پیش‌نیاز CI اند و روی هیچ ماشین توسعه‌ای وجود
ندارند. یعنی Q7 فاز ۵ به installer نرسیده بود.

**دو چیزی که این بسته ندارد** (و در مسیر انتشار باید برگردند):
- امضای Authenticode روی باینری‌های native — نیازمند Windows SDK
- یکپارچگی منوی راست‌کلیک ویندوز (`.appx`) — نیازمند MSIX tooling.
  توجه: CLSID هایی که مالک به `product.json` اضافه کرد ورودی همین قابلیت‌اند.
- الگوی مشابه signtool در `build/gulpfile.reh.ts:537` دست‌نخورده ماند؛ بیلد
  سرور remote به همان مانع خواهد خورد.

## معیار پذیرش

1. جواب سؤال «بیلد فعلی چطور ساخته شد» ثبت شود.
2. تصمیم درباره‌ی حضور افزونه‌ی کوپایلت در بسته گرفته و ثبت شود.
3. `npm run gulp vscode-win32-x64` با exit 0 تمام شود.
4. `vscode-win32-x64-system-setup` یک `.exe` تولید کند.
5. نصب روی ماشین و بالاآمدن برنامه با نسخه‌ی درست.

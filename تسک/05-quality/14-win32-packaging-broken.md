# Q14 — بسته‌بندی ویندوز می‌شکند: SDK کوپایلت در خروجی نیست

- **اولویت:** **P0 برای انتشار** (کامپایل و اجرای dev سالم‌اند) | **برآورد:** M | **وضعیت:** 🔴
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

**۳. `.moduleignore` توضیح‌دهنده نیست.** `build/.moduleignore:218` فقط
`@github/copilot/sdk/index.js` را می‌گیرد، نه کل `sdk/**`. پس ۳۲ فایل دیگر باید
می‌ماندند. یعنی حذف از جای دیگری است — کاندیداها: `getCopilotExcludeFilter`،
مرحله‌ی کپی `node_modules` در `gulpfile.vscode.ts`، یا رفتار `.moduleignore` روی
دایرکتوری‌هایی که فایل اصلی‌شان strip شده.

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

## معیار پذیرش

1. جواب سؤال «بیلد فعلی چطور ساخته شد» ثبت شود.
2. تصمیم درباره‌ی حضور افزونه‌ی کوپایلت در بسته گرفته و ثبت شود.
3. `npm run gulp vscode-win32-x64` با exit 0 تمام شود.
4. `vscode-win32-x64-system-setup` یک `.exe` تولید کند.
5. نصب روی ماشین و بالاآمدن برنامه با نسخه‌ی درست.

# مسیر پوشش کامل type-check (task Q5 §د)

این سند «چطور وقتی واقعاً ۱۰۰٪ لازم است» را مستند می‌کند — نه اتوماسیون، چون
هزینه‌اش صدها مگابایت دانلود روی کلون partial است.

## حالت سبک (پیش‌فرض — همان که `node tools/verify.mjs` اجرا می‌کند)

```
type-check : 23 files, 10,070 lines — 0 errors
tests      : 79 passed, 0 failed
```

پوشش با stub های محلی `tools/.verify/ensure-platform-stubs.mjs` به‌دست آمده؛
stub ها فقط برای ماژول‌های vs/platform ای ساخته می‌شوند که در sparse-checkout
روی دیسک نیستند و با ظاهر شدن فایل واقعی `.ts` بی‌اثر می‌شوند (tsc همیشه
`.ts` را به `.d.ts` ترجیح می‌دهد).

**تنها استثنای باقی‌مانده:** `sendLLMMessage.impl.ts` — فایل `@ts-nocheck` است
(پرچم خود repo برای نسخه‌ی وب)؛ افزودنش به برش پوشش را «فیک» بالا می‌برد چون
tsc اصلاً داخلش را چک نمی‌کند. تا وقتی پرچم برداشته نشده، صادقانه در فهرست
NOT CHECKED می‌ماند.

## مسیر کامل (وقتی ۱۰۰٪ لازم شد)

```bash
# ۱) کل sparse-checkout را گسترش بده (چند صد MB دانلود؛ کلون partial است)
git sparse-checkout set --cone build src resources tools "تسک"

# ۲) نصب بدون اجرای postinstall و بدون باینری الکترون
ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm install --ignore-scripts

# ۳) type-check کامل با tsconfig خود repo
npx tsc -p src/tsconfig.json --noEmit

# ۴) برگشت به حالت سبک
git sparse-checkout set --stdin < tools/sparse-light.txt
# (فایل tools/sparse-light.txt لیست اصلی را نگه می‌دارد)
```

### نتیجه‌ی اجرای ۲۰۲۶-۰۹-۰۵ روی این ماشین

گام ۱ و ۲ روی این کلون **اجرا نشد** — شبکه‌ی npm پشت proxy بسته است
(`npm install` با `network In most cases you are behind a proxy` شکست خورد؛
حتی `--prefer-offline` به دلیل گره‌های native به node-gyp رسید که همان‌جا
مرد). TypeScript 5.9.3 برای هارنس از کش محلی npm استخراج شد
(`tools/.verify/bootstrap.mjs` همین کار را بازتولید می‌کند). بنابراین عدد
پوشش «کامل» روی این ماشین قابل اندازه‌گیری نبود و مسیر بالا فقط مستند شده
است، نه اجراشده. هارنس سبز است و می‌گوید چه چیزی را ندیده — که همان
قرارداد این تسک است.

## عوارض جانبی شناخته‌شده

- stub های `.d.ts` در `.git/info/exclude` هستند (لوکال، هرگز کامیت نمی‌شوند)
  و در فول‌چک‌اوت واقعی بی‌اثرند.
- `npm install` کامل ممکن است گره‌های native بخواهد (node-gyp)؛ روی ویندوز
  بدون ابزار build ویژوال استودیو همان‌جا می‌شکند — پیش‌نیازش را جدا کن.

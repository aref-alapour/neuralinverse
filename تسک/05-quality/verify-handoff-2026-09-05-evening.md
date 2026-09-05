# Handoff for independent verification — editor-agent fixes, evening of 2026-09-05

> **برای Claude Code:** این سند پروتکل راستی‌آزمایی مستقل است. همه‌ی دستورها را
> خودت اجرا کن و خروجی را با «انتظاری» زیر هر کدام مقایسه کن — خواندنِ گزارش
> جای اجرا را نمی‌گیرد (درس ثبت‌شده‌ی همین روز: ✅ قبل از گیت سبز).
> هیچ دستوری در این سند **نمی‌نویسد** در Program Files یا فایل‌های کاربر؛
> همه read-only هستند مگر اینکه صریحاً «elevated»标注 شده باشد (و آن‌ها را
> فقط با تأیید مالک اجرا کن).

## ۰) زمینه در یک پاراگراف

مالک روی agent داخلی ادیتور NeuralInverse (مدل OSS از طریق omni.local) کار
می‌کرد. سه موج مشکل در یک روز ریشه‌یابی و رفع شد: (۱) ابزارهای MCP (clude
`list_memories` با 404 بک‌اند، playwright با resolve بی‌پایان `@latest`)، (۲)
خطاهای ابزار که به‌شکل `{}` نمایش داده می‌شدند، (۳) لایه‌ی OSS-enhancement که
فایل‌ها را در ۳۰۰۰ کاراکتر می‌برید، خواندن worktree را ناممکن می‌کرد و با
تزریق «ادامه بده» جوابِ سؤال کاربر را به ازسرگیری تسک تبدیل می‌کرد. در نصب
کردن این رفع‌ها، دو پچ خودشان باگ سینتکس داشتند و صفحه‌ی سیاه دادند؛ هر دو
اصلاح و یک گیت parse به selftest اضافه شد. مالک تأیید کرد برنامه الان بالا
می‌آید («خب این درست شد»).

## ۱) گیت‌های repo — از ریشه‌ی `C:\Users\jobal\dev\neuralinverse`

```bash
git log --oneline -9          # انتظار: c6233c06 → e333d7b6 → b7ee1612 → 4364a3dc
                              # → 95b073fa → bf3e21ed → 8c6f1e80 → 235aef5d → 875e01f1
git status --porcelain        # انتظار: خالی (clean)

node tools/verify.mjs ; echo "exit=$?"
```

انتظار `verify.mjs` (خروجی واقعی امروز، 2026-09-05 ~22:00):

```
PASS     type-check
  type-check : 26 files, 10,382 lines — 0 error(s), 260 out-of-slice … (ignored)
  self-test  : OK (deliberate error was caught)
PASS     tests
  tests      : 87 passed, 0 failed
PASS     live-patch
  live-patch selftest: all scenarios passed
coverage   : 90% of the ledger feature files type-checked (10,382 of 11,586 lines)
NOT CHECKED (1 files, 1,204 lines):
  - …/llmMessage/sendLLMMessage.impl.ts   ← @ts-nocheck؛ چک‌کردنش پوشش فیک است
exit=0
```

نکته‌ها:
- بدون هیچ نصب/`npm install` اجرا می‌شود؛ TypeScript خصوصی در
  `tools/.verify/node_modules` (bootstrap از کش npm وقتی شبکه بسته است).
- selftest مربوط به live-patch از commit `c6233c06` به بعد **دو گیت parse اجباری**
  دارد (`node --check` روی هر دو bundle سندباکس بعد از apply). اگر خواستی
  مرور کنی: `tools/live-patch-selftest.py`، سناریوی ۲.
- تست‌های ۸۰→۸۷ با `ossRetryGuard.test.ts` (گارد سؤال) اضافه شد.

## ۲) گیت‌های نصب (read-only، بدون elevation)

```bash
python tools/live-patch.py --verify ; echo "exit=$?"
# انتظار: "39 OK, 0 PENDING, 0 MISSING" و exit=0   (38 پچ + 1 prepend)

python tools/live-patch.py --status
# انتظار (خروجی واقعی الان):
#   app version  : 1.1.3 (product.json)
#   last apply   : 2026-09-05T21:54:04  repo e333d7b6  app v1.1.3
#   files        : هر ۴ فایل "matches last apply"
```

**نکته‌ی ظریف ۱ — manifest:** `repoCommit=e333d7b6` است چون applyِ نهایی قبل
از commit آخر (`c6233c06`) اجرا شد؛ اما payload هایی که اعمال شد از
working-tree ای بودند که همان اصلاحات `c6233c06` را داشت. ناسازگاریِ ظاهری
است، نه محتوایی. (اعمال مجدد idempotent همه‌چیز را «already» می‌گوید — ولی
elevation می‌خواهد؛ لازم نیست.)

**نکته‌ی ظریف ۲ — گیت سینتکس درجا:**

```bash
node --check "C:\Program Files\NeuralInverse\resources\app\out\vs\workbench\workbench.desktop.main.js"
node --check "C:\Program Files\NeuralInverse\resources\app\out\main.js"
# انتظار: هر دو بی‌خروجی (pass) — همین الان تست شده، هر دو PARSES.
```

`package.json` برنامه `"type": "module"` دارد، پس این چکِ درجا فایل را با
goal ای غیر از Electron (classic script) می‌خواند — به همین دلیل چک را در
«هر دو goal» انجام بده اگر شک داشتی (کپی به temp بدون package.json = Script
goal). این تمایز خودش بخشی از forensic امشب بود: یک خطای سینتکس واقعی
(`const st` دوبل) در هر دو goal می‌مرد؛ یک خطای ظاهری فقط در یکی.

## ۳) لنگرهای forensic صفحه‌ی سیاه (روی bundle نصب‌شده، read-only)

```python
python - <<'EOF'
d = open(r'C:/Program Files/NeuralInverse/resources/app/out/vs/workbench/workbench.desktop.main.js', encoding='utf-8').read()
print('single st declaration (fixed):', d.count('const st=jZ*(De-1),'))   # انتظار: 1  (قبلاً 2 بود → SyntaxError)
print('ternary restored:', d.count('>1)?`${me.uri.fsPath}'))              # انتظار: 1  (? جاافتاده بود)
print('empty-page message present:', '(no more content — page' in d)      # انتظار: True
print('24k preview present:', 'showing first 24,000 of' in d)             # انتظار: True
print('question guard present:', 'toolsExecutedThisRun' in d)             # انتظار: True
EOF
```

خروجی واقعی الان: `1 / 1 / True / True / True`.

## ۴) رفع‌های محلی خارج از repo (با بکاپ)

```bash
# الف) پچ @clude/sdk (روت 404 بک‌اند → فال‌بک /recent):
grep -c "NI_LOCAL_PATCH_2026_09_05" \
  "C:/Users/jobal/.clude/sdk-host/node_modules/@clude/sdk/dist/cli/index.js" \
  "C:/Users/jobal/.clude/sdk-host/node_modules/@clude/sdk/dist/mcp/server.js"
# انتظار: هر دو = 1
ls …/dist/cli/index.js.ni-patch.orig …/dist/mcp/server.js.ni-patch.orig   # هر دو موجود

# ب) پین playwright در تنظیمات MCP ادیتور:
grep '"@playwright/mcp@' "C:/Users/jobal/.neural-inverse/mcp.json"
# انتظار: "@playwright/mcp@0.0.80"  (+ بکاپ: mcp.json.ni-backup)
```

برای اثبات عملکردیِ پچ SDK (سرور تازه spawn می‌شود، نه پروسه‌ی قدیمی):
handshake استاندارد stdio-MCP روی `node …/dist/cli/index.js mcp-serve` با env
از `C:/Users/jobal/.zcode/cli/config.json` (`.mcp.servers.clude-memory.env`)
و `tools/call list_memories {page:2,page_size:3}` — انتظار: `isError:false`
و یک `note` مبنی بر محدودیت ۱۰۰ آیتم. (روش همین امروز اجرا و سبز شده.)
⚠️ این پچ داخل node_modules است و با آپدیت پکیج پاک می‌شود؛ متن issue
بالادستی در `تسک/05-quality/editor-tools-audit-2026-09-05.md` منتظر OK مالک است.

## ۵) رفتارهایی که فقط مالک می‌تواند زنده ببیند (خارج از توان CLI)

1. برنامه بالا می‌آید (تأییدشده توسط مالک، پس از رفع صفحه‌ی سیاه).
2. **آزمون اصلی:** تسک تمام شود → «چقدر زمان برد این تسک اجرا بشه؟» → فقط
   جواب، بدون ادامه. (تست‌های واحد معادل: `ossRetryGuard.test.ts`.)
3. وسط‌کار: «چقدر مونده؟» → جواب + ادامه (عمداً حفظ شده).
4. «تسک رو ادامه بده» → ادامه (دستور است، سؤال نیست).
5. خواندن فایل بزرگ در گفتگوی agent (برش ۲۴k با راهنمای grep) و مسیر مطلق
   worktree (`C:/Users/jobal/docker/escapezoom_dev-EZ-0102`) بدون ENOENT.
6. خطاهای MCP با پیام واقعی (نه `{}`) — فقط اگر ابزاری واقعاً خطا بدهد.

## ۶) موارد بازِ شناخته‌شده (که باگ نیستند)

- Ledger خودش روی live-patch پورت **نشده** (تصمیم dev-build vs پورت، باز).
- `sendLLMMessage.impl.ts` در NOT CHECKED مانده (`@ts-nocheck`).
- گارد سؤال، الگویی است: جمله‌ی دستوریِ مبتنی بر «چند…» ممکن است سؤال پنداشته
  شود؛ بدترین عارضه = نبودِ auto-retry (نه ازسرگیری ناخواسته).
- `usage` واقعی provider هنوز با مدل واقعی تست نشده (مسیر کد کامل است).

## ۷) تله‌هایی که امروز گرفتیم (برای راستی‌آزماییِ خودت)

| تله | نشانی | درس |
|---|---|---|
| «الگو حاضر است» ≠ «JS معتبر است» | selftest قدیمی روی پچِ سینتکس‌خراب سبز شد | از `c6233c06`، parse-gate اجباری است |
| goal های parse متفاوت | `node --check` درجا = ESM (package.json type:module)، Electron = Script | هر دو را چک کن |
| کرش انکودینگ cp1252 | `UnicodeEncodeError … \u2192` در کنسول برخی shell ها | هر دو اسکریپت UTF-8 را force می‌کنند (`4364a3dc`)؛ اگر کنسول خاصی still خراب بود، `PYTHONIOENCODING=utf-8` فقط برای مقایسه |
| پروسه‌ی MCP قدیمی | سرور clude-memoryِ spawn‌شده قبل از پچ، کد قدیمی را اجرا می‌کند | تست عملکردی فقط با spawn تازه |

## ۸) خلاصه‌ی commit ها (chrono)

| کامیت | چه چیز |
|---|---|
| `235aef5d` | M6: مرز اپیزود مشترک/رشدی، `<ledger_notice>`، usage واقعی، پاک‌سازی migration |
| `8c6f1e80` | Q4 یکپارچگی live-patch (verify/status/rebaseline/manifest/selftest) + Q5 هارنس verify |
| `bf3e21ed` | پیام خطای واقعی MCP به‌جای `{}` + پورت live-patch |
| `95b073fa` | سند ممیزی ابزارها + پیش‌نویس issue بالادستی |
| `4364a3dc` | UTF-8 stdout برای اسکریپت‌ها (کنسول cp1252) — کامیت خودِ Claude قبلی |
| `b7ee1612` | خوانایی فایل برای agent های OSS (۲۴k/صفحه‌ی خالی/خواندن worktree) |
| `e333d7b6` | گارد سؤال: جواب به سؤال، تسک را ازسر نمی‌گیرد |
| `c6233c06` | اصلاح دو payload خراب + گیت parse اجباری در selftest |

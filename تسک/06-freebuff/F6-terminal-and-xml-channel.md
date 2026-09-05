# F6 — سخت‌سازی ترمینال + کانال ابزار XML داخل stream

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P1 (الف) / P2 (ب) | **برآورد:** M | **وضعیت:** 🟡 بخشی هست | **وابستگی:** A4 (الف)، A2 (ب)

## الف) قواعد ترمینال hard-won ویندوزی

**منبع (راستی‌آزمایی‌شده):**
- `common/src/tools/params/tool/run-terminal-command.ts` — description ابزار شامل:
  **الزام POSIX روی همه‌ی OS ها** (Git Bash در ویندوز)، هشدار واقعی «`> nul` در
  Git Bash فایلی به‌نام `nul` می‌سازد که قابل حذف نیست» (L174)
- `sdk/src/tools/run-terminal-command.ts` — حتی یک **بازنویسی خودکار** `nul → /dev/null`
  در خروجی مدل (L232-235)؛ `MAX_TERMINAL_TIMEOUT_SECONDS=600` + `clampTerminalTimeoutSeconds`
  (L23-28): timeout را **مدل انتخاب می‌کند** ولی به ۶۰۰s clamp می‌شود؛
  `stdoutOmittedForLength: true` وقتی خروجی بزرگ است (به‌جای cut بی‌اطلاع)
- `cli/src/utils/terminal-command-broker.ts` — الگوی broker: پروسه‌ی helper بدون
  کنسول مالک spawn است؛ درخواست/پاسخ روی فایل‌های یک‌بارمصرف با سقف (4MB/64KB)؛
  خود-تخریب با poll کردن parent PID (L172-184)؛ tree-kill ویندوزی `taskkill /t /f` (L310)

**اصلاح نسبت به handoff:** `process_type: 'BACKGROUND'` در این snapshot **پیاده
نشده** (throw می‌کند: sdk L314-315) — انتظارش را به پورت نبرید؛ نسخه‌ی ما از قبل
terminal های background دارد (بهتر از منبع!).

**پیاده‌سازی:** ادغام در `terminalTools.ts` + `terminalCommandClassifier` ما:
1. بازنویسی `nul→/dev/null` + قاعده‌ی POSIX در description ابزار (ما ویندوز-first هستیم!)
2. timeout مدل-انتخاب‌گر با clamp (ترکیب با دسته‌بندی فعلی ما: پیش‌فرضِ دسته،
   override مدل تا سقف ۶۰۰s)
3. `stdoutOmittedForLength` در خروجی ابزار (جایگزین cut خاموش)
4. الگوی parent-PID self-reap برای هر پروسه‌ی helper آینده (مثلاً A1، E3)
5. کشف Git Bash دقیق (منطق WINDOWS.md: scoop/choco/غیر-C:) اگر مسیر اجرای مدل bash است

## ب) کانال دوم ابزار: XML داخل متن stream با اجرای mid-stream

**منبع:** `packages/agent-runtime/src/tool-stream-parser.ts` (بافر تگ ناقص بین chunk ها،
L54-115) + `tools/stream-parser.ts`:
- مدل می‌تواند `<codebuff_tool_call>{json}</codebuff_tool_call>` داخل متن بفرستد؛
  پارسر stateful تگ‌های نیمه را بین chunk ها بافر می‌کند و ابزار را **همان لحظه،
  با مکث stream** اجرا می‌کند (`executeXmlToolCall` L416، `await toolPromise` L366-369)
- ترتیب اجرا با promise-chaining ساده: `previousToolCallFinished` (L221, L300-306) —
  کشف‌شده در stream ولی اجرا اکیداً سریالی؛ اولین call با promise از قبل resolved
  (بدون بن‌بست انتظار برای پایان stream)
- `common/src/util/partial-json-delta.ts` — parse تدریجیِ JSON نیمه‌stream شده برای
  UI زنده (پیش‌نمایش آرگومان‌ها موقع تایپ مدل!)

**ارزش برای ما:** این جایگزین/تکامل پروتکل JSON-block فعلی ما (`toolCallParser.ts`)
است: برای مدل‌های ضعیف/OSS بدون native tool calling، این کانال درست‌تر از markdown
block هاست چون mid-stream اجرا می‌شود (لاتنسی کمتر) و با streaming ما سازگار است.
با A2 سه‌لایه می‌شود: native (مدل قوی) → XML-in-stream (مدل متوسط) → JSON-block
(legacy). اجرای سریالی با promise-chaining مستقیماً در `agentExecutor` قابل پیاده‌سازی است.

## معیارهای پذیرش
- [ ] فرمان مدل با `> nul` به `/dev/null` بازنویسی/هشدار می‌شود
- [ ] مدل timeout=10000s فرستاد → به 600s clamp شد
- [ ] خروجی ۱MB → خروجی ابزار نشانگر omission دارد نه cut
- [ ] (ب) با مدل بدون native tools: تگ XML وسط stream پارس و همان لحظه اجرا می‌شود؛
      تگ نصف‌شده بین دو chunk بافر و ادامه پیدا می‌کند
- [ ] (ب) دو ابزار ویرایش در یک پاسخ، به ترتیب ظهور اجرا می‌شوند (سریالی)

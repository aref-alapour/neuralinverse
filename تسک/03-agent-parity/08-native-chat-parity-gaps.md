# A8 — چت بومی از دو قابلیتِ سایدبار جا مانده

- **اولویت:** P1 | **برآورد:** S | **وضعیت:** ✅ تست owner سبز (۰۹-۰۹) — `recall_history` نتیجه‌ی امتیازدار برگرداند
- **کشف:** ۲۰۲۶-۰۹-۰۹، حین ریشه‌یابی تست زنده‌ی owner
- **مرتبط:** ادامه‌ی [A7](07-native-chat-bridge.md) — همان الگو، دو نقطه‌ی جامانده

## ریشه‌یابی دقیق‌تر (بعد از کدخوانی، ۰۹-۰۹)

- شکاف ۲ عمیق‌تر از «ثبت نمی‌شود» بود: ابزارهای recall در
  `IVoidInternalToolService` ثبت می‌شوند و اسکیمای XMLشان از طریق
  `generateSystemMessage('agent',…)` به پیام سیستمی پل می‌رسید — ولی
  (الف) `extractXMLToolsWrapper` فقط XML ابزارهایی را استخراج می‌کند که در
  فهرست `mcpTools` خودش باشند و پل فقط `copilotMcpTools` می‌داد، و (ب) در
  حلقه‌ی اجرا شاخه‌ای برای internal tools نبود و به else «Tool ... is not
  available» می‌افتاد (voidModelProvider — دقیقاً همان پیامی که owner دید).
- شکاف ۱ هم لایه‌ی سومی داشت: کوئری recall در `getContextSummaryAsync` از
  working memory مربوط به workflow agent می‌آمد که در چت معمولی (حتی سایدبار)
  خالی است → `''` زودهنگال. پس صرفاً async کردن، تست ۲ را سبز نمی‌کرد؛
  کوئری باید از پیام خود کاربر بگذرد.

## الگوی تکرارشونده

[A7](07-native-chat-bridge.md) نشان داد پل چت بومی مسیر ساخت پیام سیستمی و
فهرست ابزار **جدای خودش** را دارد. هر قابلیتی که فقط در مسیر سایدبار وصل شود،
در چت بومی غایب می‌ماند — و چون هر دو «کار می‌کنند»، کسی متوجه نمی‌شود.

این یک بار در موج ۳ دیده و رفع شد (E1: قواعد به پل نمی‌رسید). دو مورد دیگر
باقی مانده که در تست زنده لو رفتند.

## شکاف ۱ — حافظه‌ی M2 به چت بومی نمی‌رسد

| مسیر | تابع | چه چیزی صدا می‌زند |
|---|---|---|
| سایدبار | `prepareLLMChatMessages` (`convertToLLMMessageService.ts:1015`) | `_getCombinedAIInstructionsForChat` → **`getContextSummaryAsync()`** ← hybrid M2 |
| **چت بومی** | `generateSystemMessage` (`:899`) | `getContextSummary()` ← **همگام و واژگانی** |

یعنی حتی وقتی [M7](../01-memory/07-memory-systems-split.md) بسته شود و حافظه
واقعاً پر باشد، چت بومی همچنان نسخه‌ی واژگانی می‌گیرد نه بازیابی معنایی.

**رفع:** `generateSystemMessage` را async-aware کن و همان
`_getCombinedAIInstructionsForChat` را صدا بزن. تابع از قبل `async` است، پس
تغییر کوچک است.

## شکاف ۲ — ابزارهای recall لجر در چت بومی نیستند

در تست زنده مدل سه بار تلاش کرد و هر بار گفت **«ابزار `recall_history` در
دسترس نیست»** و آخرش: «`recall_history` در سیستم وجود ندارد.»

`ledgerRecallContrib.ts` این ابزارها را ثبت می‌کند (`recall_history`،
`expand_episode`) ولی به فهرستی که پل به مدل می‌دهد نمی‌رسند.

**اثر:** نیمه‌ی بازیابیِ [M5](../01-memory/05-context-ledger.md) از سطح اصلی
محصول در دسترس نیست. ژورنال پر می‌شود ولی هیچ‌کس نمی‌تواند از آن بخواند —
که کل نکته‌ی «گفتگوی بی‌پایان بدون فراموشی» را از بین می‌برد.

```bash
grep -n "recall_history" src/vs/workbench/contrib/void/browser/ledgerRecallContrib.ts
grep -n "getTools\|copilotMcpTools" src/vs/workbench/contrib/void/browser/voidModelProvider.ts
```

## معیار پذیرش

1. در چت بومی، `recall_history` در فهرست ابزارها باشد و روی گفتگوی قبلی نتیجه
   بدهد — نه «در دسترس نیست».
2. بلوک `Agent Memory` با پسوند `(matched: vector:…)` در چت بومی هم بیاید
   (بعد از بسته‌شدن [M7](../01-memory/07-memory-systems-split.md)).
3. **یک تست که هر دو مسیر را با هم بسنجد** — الگوی تست پاریتی
   [Q12](../05-quality/12-desktop-usage-parity.md) اینجا هم جواب می‌دهد: هر
   قابلیتی که سایدبار دارد و پل ندارد باید سوئیت را قرمز کند. بدون این گیت،
   شکاف سوم و چهارم هم به همین شکل کشف خواهند شد — یکی‌یکی و با تست دستی.

## رفع ثبت‌شده (۰۹-۰۹)

1. **حافظه:** `getAIInstructionsForChat(querySeed?)` عمومی شد روی
   `IConvertToLLMMessageService`؛ پل آن را با پیام کاربر صدا می‌زند و به
   system message می‌چسباند (الگوی workspace_rules از E1). در مسیر سایدبار،
   `prepareLLMChatMessages` آخرین پیام کاربر را به‌عنوان querySeed می‌دهد و
   متد جدید `getChatMemoryContext(query)` روی سرویس agent (کلید = پیام کاربر،
   نه working memory) وقتی agent context خالی است جانشین می‌شود — یعنی چت
   تازه هم recall معنایی می‌گیرد، سایدبار و پل هر دو.
2. **ابزارهای recall:** پل `internalToolService.getToolInfos()` را مثل
   chatThreadService با copilotMcpTools ادغام می‌کند (internal اول، dedup،
   سقف ۱۲۸) و همان فهرست به `_callLLM` → extractor/sendLLMMessage می‌رسد؛
   شاخه‌ی اجرای internal tools قبل از fallback «not available» اضافه شد و به
   `internalToolService.execute` می‌رود.
3. **تست پاریتی:** `test/node/nativeChatParity.test.ts` (الگوی Q12، پارس
   سورس هر دو مسیر) با ۵ لنگر: رساندن حافظه به پل، seed شدن کوئری از پیام
   کاربر، پیشنهاد internal tools توسط پل، اجرایشان، و ماندن 'agent' در شرط
   internal tools سازنده‌ی پیام سیستمی. ثبت در typecheck-slice.json؛
   verify.mjs = ۱۵۱ تست سبز.

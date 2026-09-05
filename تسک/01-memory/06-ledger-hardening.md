# M6 — سخت‌سازی Context Ledger (شکاف‌های پیداشده در ممیزی)

- **اولویت:** P0 — قبل از هر تست زنده‌ی Ledger | **برآورد:** M | **وضعیت:** ✅ کد کامل (2026-09-05؛ تست زنده و پورت live-patch طبق همین سند، بعد از Q4 باقی می‌ماند)
- **شاخه:** ادامه‌ی `feat/context-ledger`
- **وابستگی:** [M5](05-context-ledger.md) (پیاده‌سازی پایه) | **مرتبط:** [Q5](../05-quality/05-verification-harness.md)، [C2](../02-context/02-context-gauge-ui.md)، [C7](../02-context/07-compaction-ux.md)

## زمینه

ممیزی ۲۰۲۶-۰۹-۰۵ روی شاخه‌ی `feat/context-ledger`: ۶۷ تست اجرا و سبز، ۳۱۶ سمبل
import شده معتبر، ۳۷٪ کد type-clean. سه باگ پیدا و **رفع شد** (کامیت `955b621d`):

| رفع‌شده | چه بود |
|---|---|
| migration فلگ | `voidSettingsService` تنظیمات را با defaults ادغام نمی‌کند و برای هر کلید یک خط migration دستی دارد؛ `contextLedgerEnabled` آن خط را نداشت ⇒ روی **هر نصب موجود** مقدار `undefined` خوانده می‌شد و کل Ledger بی‌صدا خاموش می‌ماند |
| ناپایداری round-trip | `mergeEpisodeBodies` کلید `alternatives: undefined` می‌ساخت که `JSON.stringify` دورش می‌اندازد ⇒ `brief.json` بعد از reload با نسخه‌ی حافظه فرق می‌کرد |
| import شکسته | `ledgerRecall.test.ts` یک سطح اشتباه import می‌کرد ⇒ آن فایل هرگز کامپایل نشده بود |

این تسک، شکاف‌های **باقی‌مانده** است. اینها را در فایل M5 نمی‌نویسیم تا آن سند
معماری بماند و این سند بدهی.

---

## ۱. مرز اپیزود در turn های ابزارمحور بسته نمی‌شود ⚠️ مهم‌ترین

**کد فعلی** (هم در `chatThreadService._closeEpisodeIfNeeded` و هم در
`agentExecutor._compactHistoryViaLedger`):

```ts
const tail = await readTail(threadId, policy.tailMinMessages + 4);   // ۱۲ ورودی آخر
const boundaryIdx = tail.findIndex(e => e.role === 'user' && e.seq > fromSeq);
if (boundaryIdx < 0 || boundaryIdx > 4) return;                      // ← اینجا
```

پنجره فقط ۱۲ ورودی آخر است و مرز باید در **۵ اسلات اول** آن باشد. در یک turn با
تعداد زیاد فراخوان ابزار (۲۰+ ورودی) هیچ پیام `user` ای در آن پنجره نیست، یا هست
ولی جلوتر از اسلات ۴ — پس اپیزود بسته نمی‌شود و `return` بی‌صدا اتفاق می‌افتد.

**شاهد:** در جلسه‌ی پیاده‌سازی، سناریوی تست با نقش‌های واقعی (user/assistant/tool)
دو بستن متوالی را رد کرد؛ برای سبز شدن، سناریو به «همه‌ی ورودی‌ها user» تغییر داده
شد. یعنی تست به کد تطبیق داده شد، نه برعکس.

**رفع:**
- به‌جای پنجره‌ی ثابت، جست‌وجوی مرز با **پنجره‌ی بزرگ‌شونده**: از `tailMinMessages`
  شروع کن و تا سقفی (مثلاً ۲۰۰ ورودی) عقب برو تا اولین `user` با
  `seq > fromSeq` پیدا شود که بعد از آن حداقل `tailMinMessages` ورودی باقی بماند.
- اگر تا سقف هیچ مرز امنی نبود، یک شمارنده‌ی `ledger.boundaryMissed` بالا برود و
  `console.warn` با دلیل چاپ شود — نه `return` خاموش.
- هر دو نقطه (chat و executor) از **یک تابع مشترک** استفاده کنند؛ الان منطق دوبار
  نوشته شده و همین باعث شد باگ arity و باگ مرز در هر دو تکرار شوند.
- تست با ترکیب واقعی نقش‌ها: `user, assistant, tool×6, assistant, user, …` و یک
  turn با ۲۵ ورودی ابزار.

## ۲. پیشوند بدون brief بی‌صدا حذف می‌شود ⚠️

در `contextAssembler.assemble`، وقتی `brief === null` (هنوز هیچ اپیزودی بسته نشده)
ولی `keepFromIdx > 0` (چون tail از بودجه بیشتر است)، پیام‌های قدیمی‌تر از payload
حذف می‌شوند **بدون هیچ نشانه‌ای**. `BRIEF_TAIL_NOTE` — که تنها جایی است که به مدل
می‌گوید «بقیه در ledger هست، از `recall_history` استفاده کن» — فقط وقتی brief وجود
دارد اضافه می‌شود.

نتیجه: در پنجره‌ی بین «گفتگو طولانی شد» و «اولین اپیزود بسته شد»، مدل یک گفتگو
می‌بیند که از وسط شروع شده و نمی‌داند چیزی قبلش بوده. این با شکاف ۱ ترکیب می‌شود و
بدترش می‌کند.

**رفع:** وقتی `keepFromIdx > 0` و brief نداریم، یک بلوک کوتاه تزریق شود:

```
<ledger_notice covers_seq="1-842">
Older messages are preserved in the ledger but are not summarized yet.
Use recall_history to retrieve any of them.
</ledger_notice>
```

با تست: `brief=null` + tail سرریز ⇒ حتماً یک head message با این نشانه تولید شود.

## ۳. عدد مصرف context قابل مشاهده نیست

`IContextUsageReport` ساخته و در `_ledgerUsageReports` نگه داشته می‌شود، ولی هیچ
مصرف‌کننده‌ای ندارد: نه UI (کار [C2](../02-context/02-context-gauge-ui.md)) و نه لاگ.
یعنی ادعای اصلی این معماری — «payload ثابت و مستقل از طول گفتگو» — در تست زنده
**قابل اندازه‌گیری نیست**.

**رفع (کوچک، قبل از C2):** یک `console.log` تک‌خطی از گزارش در مسیر assemble، پشت
همان فلگ:

```
[ChatThread] ledger assembled: brief 3.1k + pinned 0 + recalled 0 + tail 38.2k = 41.3k / 120k (rev 12, journal 1.84M)
```

`journal` باید مجموع توکن‌های ژورنال باشد تا نسبت «کل بایگانی به payload» در یک نگاه
دیده شود. همین یک خط، پروتکل تست زنده را از حدس به اندازه‌گیری تبدیل می‌کند.

## ۴. `usage` واقعی provider هنوز نیست

`OnFinalMessage` هیچ فیلد usage ندارد و لایه‌ی provider در electron-main هم آن را
برنمی‌گرداند. الان هزینه از تخمین `chars/4` × قیمت مدل حساب می‌شود و
`ILedgerEntry.meta.usage` عملاً همیشه خالی است.

**رفع:** تکمیل فاز ۴ M5 — عبور دادن `usage` از هر شش provider تا `OnFinalMessage`،
ثبت روی ورودی ژورنال، و ضریب کالیبراسیون per-model از نسبت تخمین/واقعی. این تسک با
[Q1](../05-quality/01-cost-usage-tracking.md) مشترک است؛ هر کدام اول رسید، دیگری
فقط مصرف‌کننده می‌شود.

## ۵. موارد کوچک

- `_journaledThisSession` (Map از threadId به Set از ChatMessage) هیچ‌وقت پاک نمی‌شود
  و تا پایان session به همه‌ی پیام‌ها ارجاع نگه می‌دارد. بعد از مهاجرت موفق یک
  thread، Set اش باید حذف شود.
- منطق `readRange`/مرز در دو فایل تکرار شده (بند ۱ آن را یکی می‌کند) — همان تکرار
  باعث شد یک باگ arity در هر دو جا بیفتد.
- `ledgerRecallService` وزن cosine را رزرو کرده ولی embedding را وصل نکرده
  (`RECALL_WEIGHTS_NO_EMBEDDINGS` همیشه فعال است). این عمدی و مستند است، ولی باید
  در [M2](02-vector-retrieval.md) بسته شود نه اینجا — فقط اینجا ثبت می‌شود تا فراموش نشود.

---

## معیارهای پذیرش

- [x] اپیزود در یک thread با turn های ابزارمحور بسته می‌شود؛ تست با ترکیب واقعی نقش‌ها
  سبز است (`ledgerBoundary.test.ts`: سناریوی ۲۵ ورودی ابزار در انتهای ژورنال —
  دقیقاً شکلی که پنجره‌ی ثابت ۱۲تایی را می‌شکند — + ترکیب ممیزی
  user/assistant/tool×6/assistant/user؛ `sizes` اثبات می‌کند پنجره ۱۲→۲۴→۴۸ رشد کرده)
- [x] هیچ مسیر `return` خاموشی در بستن اپیزود نمانده — همه یا لاگ دارند یا شمارنده
  (`noteBoundaryMissed`: شمارنده per-thread + `console.warn` یک‌بار به‌ازای هر دلیل؛
  executor علاوه بر آن `ctx.log` می‌زند؛ بستن موفق، warned-state را ریست می‌کند)
- [x] منطق مرز در chat و executor یک تابع مشترک است:
  `void/common/ledgerBoundary.ts → resolveCloseBoundary` (هر دو نقطه فقط
  decideBoundary را gate می‌کنند و بعد همان تابع را صدا می‌زنند)
- [x] با `brief=null` و tail سرریز، `<ledger_notice>` تزریق می‌شود (سه تست در
  `contextAssembler.test.ts`: تزریق با covers_messages درست / عدم تزریق وقتی
  چیزی fold نمی‌شود / عدم تزریق وقتی brief هست؛ توکن‌های notice از بودجه‌ی tail
  رزرو می‌شود تا جمع بخش‌ها دقیقاً با total برابر بماند)
- [x] خط `ledger assembled:` در کنسول با اعداد درست ظاهر می‌شود و جمع بخش‌ها با
  total برابر است (ساختار گزارش: بخش‌ها از `report.sections` چاپ می‌شوند که
  by-construction با `totalTokens` جمع می‌شوند؛ شامل بخش `notice` و
  `journal <کل توکن‌های ژورنال>`)
- [x] `usage` واقعی برای anthropic + openai-compatible ثبت می‌شود: `OnFinalMessage`
  فیلد `usage` گرفت؛ anthropic از `response.usage`، openai-compat با
  `stream_options.include_usage` از چانک آخر؛ در `chatThreadService` روی
  `meta.usage` ورودی ژورنال + جمع session + کالیبراسیون per-model
  (نسبت تخمین/واقعی؛ `getSessionCost` اول واقعی، بعد کالیبره‌شده) —
  **تست زنده‌ی provider هنوز نه** (پورت Ledger ممنوع تا بعد از این تسک؛
  هماهنگ با قاعده‌ی همین سند)
- [x] `_journaledThisSession` بعد از مهاجرت پاک می‌شود (و دیگر ساخته نمی‌شود —
  فقط در بازه‌ی migration زنده است)
- [x] `node tools/verify.mjs` سبز (type-check ۲۳ فایل/۱۰٬۰۷۰ خط صفر خطا + ۷۹ تست)
- [ ] پورت live-patch Ledger — عمداً باز: طبق خود تسک فقط بعد از Q4 سبز و با
  تصمیم صریح (پیشنهاد ممیزی: اول dev-build)

### باگ‌های latent اضافی که هارنس Q5 در همان گذر پیدا کرد

- `contextLedgerService`: توکن DI فقط value بود؛ استفاده‌ی type در
  `@IContextLedgerService x: IContextLedgerService` نمی‌گذاشت — type-alias هم‌نام اضافه شد.
- `chatThreadService`: `_getAgentService` مقدار `undefined` را برمی‌گرداند برخلاف
  امضای `| null`؛ و `getSessionCost` به `content` روی union نقش‌ها می‌زد.
- `ledgerRecallContrib`: `ledgerOn` مرده بود و هدر می‌گفت ابزارها فقط با فلگ ثبت
  می‌شوند — ثبت حالا واقعاً به فلگ گره خورد.

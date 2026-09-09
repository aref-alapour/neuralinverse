# M5 — Context Ledger (حافظه‌ی دفترکل: بایگانی ابدی + خلاصه‌ی تغییرناپذیر + بازیابی)

- **اولویت:** P0 — ستون فقرات دسته‌ی حافظه؛ M1/M2 زیرمجموعه‌ی آن می‌شوند
- **برآورد:** L (۵ فاز، هر فاز مستقلاً قابل تست و live-patch)
- **وضعیت:** ✅ تست owner سبز (۰۹-۰۹) — ژورنال gapless و با محتوای واقعی ابزار؛
  **باقی‌مانده:** تست مقیاس ۱۰M (ادعای p95 هنوز اثبات نشده)
  | **شاخه:** `feat/context-ledger` (از `feat/agent-conversation-memory`)
- **وابستگی:** — (زیرساخت‌های لازم همه از قبل در کد هستند)
- **هم‌ارز در بازار:** Cursor Memories + Claude Code compaction + session resume — و یک قدم جلوتر:
  در هیچ‌کدام از آنها «مسیرهای رد شده» به‌صورت ساخت‌یافته و مصون از فراموشی نگه‌داری نمی‌شود.

> ⚖️ **clean-room:** این تسک صددرصد پیاده‌سازی خودمان است. هیچ کدی از Cursor/Claude Code/
> freebuff/Cline کپی یا ترجمه نمی‌شود. طرح زیر از تحلیل مسئله‌ی خودمان درآمده و
> قابل PR به upstream است.

---

## ۱. هدف در یک جمله

به‌جای اینکه هر نوبت کل تاریخچه برای مدل فرستاده شود، یک **خلاصه‌ی مهندسی‌شده‌ی پایدار**
(شامل تصمیم‌ها، **مسیرهای رفته‌شده و دلایل رد شدنشان**، شکست‌ها، و قواعد کاربر) فرستاده
شود؛ در عین حال **هیچ بایتی از تاریخچه حذف نشود** و مدل بتواند هر لحظه با یک ابزار،
هر تکه از گذشته را عیناً برگرداند. نتیجه: گفتگو می‌تواند تا ۱۰M توکن و فراتر رشد کند،
در حالی که payload هر درخواست زیر ~۶۰k توکن **ثابت** می‌ماند.

---

## ۲. تصمیم‌های معماری (قطعی‌شده — اگر عوض شد، اول اینجا عوض شود)

| # | تصمیم | دلیل |
|---|---|---|
| D1 | **خلاصه‌ها تغییرناپذیرند (immutable).** اپیزودی که بسته شد، خلاصه‌اش دیگر هرگز به LLM داده نمی‌شود. | جلوگیری از drift ناشی از بازنویسی زنجیره‌ای (بند ۳-الف) |
| D2 | **بایگانی روی دیسک، ایندکس در IndexedDB.** journal در `.inverse/ledger/`، ایندکس جست‌وجو در `persistentStore`. | دیسک: قابل بازرسی/بکاپ/دیباگ و مستقل از storage. IndexedDB: جست‌وجوی سریع بدون خواندن ۴۰MB |
| D3 | **ادغام brief قطعی (deterministic) است، نه LLM.** فقط بدنه‌ی اپیزود با LLM ساخته می‌شود. | قواعد و بن‌بست‌ها هرگز نباید «تفسیر مجدد» شوند |
| D4 | **یک Ledger مشترک برای هر سه مسیر** (chat / executor / workflow agent)، ولی مرحله‌ای: چت اول، دو مسیر دیگر در فاز ۵. | دو مسیر دیگر امروز واقعاً داده حذف می‌کنند؛ ولی همه را با هم عوض کردن ریسک بالا دارد |
| D5 | **brief فقط روی مرز اپیزود عوض می‌شود.** بین دو اپیزود، prefix درخواست بایت‌به‌بایت ثابت است. | پایداری prompt-cache provider — بند ۶-۵ |
| D6 | **degrade تدریجی، هرگز خطا.** بدون LLM → بدنه‌ی قطعی؛ بدون embedding → BM25؛ بدون دسترسی دیسک → in-memory با هشدار. | سازگاری BYOLLM |

---

## ۳. چرا معماری فعلی به هدف نمی‌رسد (ممیزی کد — تأییدشده)

### الف) خلاصه بازنویسی می‌شود ⇒ drift تجمعی
`_summarize` خلاصه‌ی جدید را به‌صورت `LLM(priorSummary + پیام‌های تازه)` می‌سازد
(`conversationCompactor.ts` — بخش «Summarization LLM call»). یعنی متن خلاصه در هر
compaction **از نو نوشته می‌شود**. در یک گفتگوی ۱۰M توکنی این ۵۰ تا ۲۰۰ بار تکرار
می‌شود — فتوکپیِ فتوکپی. تصمیم نوبت اول تا نوبت پنجاهم به یک جمله‌ی مبهم تقلیل و بعد
ناپدید می‌شود. **این ریشه‌ای‌ترین ایراد است.**

### ب) طرح خلاصه، چیزی که می‌خواهیم را ندارد
سرفصل‌های فعلی: Objective / Requirements / Key Decisions / Files / Tool Activity /
Current State / Next Steps.
**غایب:** مسیرهای رد شده + دلیل رد، تلاش‌های شکست‌خورده + پیام خطا، اصلاحات کاربر
(«نه، اینجوری نه»)، قواعد تغییرناپذیر. بدون اینها مدل همان بن‌بست را دوباره می‌رود —
گران‌ترین نوع اتلاف توکن.

### ج) بایگانی هست، راه برگشت نیست
پیام‌های تاشده در storage می‌مانند (`_maybeCompactThreadForSend` فقط request را فشرده
می‌کند و thread ذخیره‌شده دست‌نخورده می‌ماند — `chatThreadService.ts:364`) ولی
**مدل هیچ ابزاری برای دسترسی به آنها ندارد**. عملاً برای مدل حذف شده‌اند.

### د) لایه‌ی ذخیره‌سازی به ۱۰M نمی‌رسد
`chatThreadService.ts:471` (`_storeAllThreads`): **کل** threadها در یک کلید JSON سریالایز
و **در هر پیام** کامل بازنویسی می‌شوند. ۱۰M توکن ≈ ۴۰MB متن ⇒ هر پیام یک
`JSON.stringify` روی ۴۰MB + یک write کامل. رفتار O(n²). IDE خیلی قبل از ۵۰۰k توکن قفل می‌شود.

### ه) موارد فرعی ولی جدی
1. **حذف واقعی داده در دو مسیر:** `agentExecutor.ts:478` (`history.length = 0`) و
   `workflowAgentService.ts:454` (`conv.splice`) — در تضاد مستقیم با «هیچ‌چیز حذف نمی‌شود».
2. **کش خلاصه فقط in-memory** است ⇒ بعد از هر restart همه‌ی خلاصه‌ها دوباره با LLM ساخته
   می‌شوند: هزینه + نتیجه‌ی متفاوت. ضمناً `agentExecutor` اصلاً `cacheKey` پاس نمی‌دهد ⇒ هر بار از صفر.
3. **توکن‌شمار `chars/4`** و `getSessionCost` هاردکد `$0.0000` — بودجه‌بندی روی حدس بنا شده؛
   برای فارسی و کد خطای ۳۰-۵۰٪.
4. `compactThread()` (حالت دستی، `chatThreadService.ts:319`) **هیچ caller ندارد** — کد مرده.
5. هیچ تستی برای compactor وجود ندارد.

---

## ۴. معماری هدف — پنج لایه

```
L0  Journal        append-only، روی دیسک، هرگز پاک/بازنویسی نمی‌شود
L1  Episodes       هر ~۶۰k توکن یک اپیزود بسته و یک‌بار خلاصه می‌شود → قفل (immutable)
L2  Working Brief  ادغام قطعیِ اپیزودها → ۲-۴k توکن، پایدار بین مرزهای اپیزود
L3  Recall         ابزار جست‌وجو/بازگشایی روی L0+L1 (BM25 + trigram + embedding موجود)
L4  Assembler      بودجه‌بندی نقش‌محور + تضمین پایداری prompt-cache
```

**جریان یک درخواست:**

```
system prompt  +  <working_memory>(L2)  +  [pinned]  +  [recalled blocks](L3، فقط اگر مدل خواست)
               +  tail پیام‌های اخیر عیناً  →  provider
```

### چیدمان روی دیسک

```
.inverse/ledger/<threadId>/
  meta.json                 # {threadId, title, createdAt, lastSeq, episodeCount, briefRevision, schemaVersion}
  journal/000001.jsonl      # یک ILedgerEntry در هر خط؛ چرخش در ۸MB
  journal/000002.jsonl
  blobs/<entryId>.txt       # بدنه‌ی کامل خروجی‌های غول‌پیکر (> ۶۴k کاراکتر)
  episodes/ep-0001.json     # IEpisodeSummary — فقط یک بار نوشته می‌شود
  brief.json                # آخرین IWorkingBrief (تاریخچه در brief-history.jsonl)
```

نوشتن با `withInverseWriteAccess` از
`neuralInverseFirmware/browser/engine/utils/inverseFs.js` — همان الگویی که
`agentStoreService.ts:214` استفاده می‌کند.

### ایندکس در IndexedDB
`context/search/persistentStore.ts` → `DB_VERSION: 1 → 2`، دو store جدید:

- `ledger-entries`: `{ id, threadId, seq, role, name, ts, tokens, terms[], snippet }` با ایندکس روی `threadId` و `terms`
- `ledger-episodes`: `{ id, threadId, ordinal, fromSeq, toSeq, terms[], body }`
- بردارها در store موجود `embeddings` با پیشوند namespace `ledger:` (بدون تغییر schema)
- `onupgradeneeded` باید ایمن باشد: نبود store قدیمی خطا ندهد، ایندکس فایل‌های موجود دست‌نخورده بماند

---

## ۵. قراردادهای داده

فایل جدید: `src/vs/workbench/contrib/void/common/ledgerTypes.ts`

```ts
export const LEDGER_SCHEMA_VERSION = 1;

export type LedgerRole = 'user' | 'assistant' | 'tool' | 'system' | 'note';

/** یک رکورد تغییرناپذیر در journal. seq بدون شکاف و صعودی است. */
export interface ILedgerEntry {
	id: string;          // le_<threadId>_<seq>
	seq: number;
	threadId: string;
	role: LedgerRole;
	name?: string;       // نام ابزار برای role='tool'
	content: string;     // اگر > INLINE_MAX_CHARS: سر و ته + اشاره به blobRef
	blobRef?: string;
	ts: number;
	tokens: number;      // اندازه‌گیری‌شده در لحظه‌ی نوشتن
	meta?: {
		toolCallId?: string;
		filePaths?: string[];
		exitCode?: number;
		errorKind?: string;
		model?: string;
		usage?: { input: number; output: number; costUsd?: number };
	};
}

/** خلاصه‌ی یک اپیزود — بعد از نوشته شدن هرگز تغییر نمی‌کند. */
export interface IEpisodeSummary {
	id: string;                  // ep_<threadId>_<ordinal>
	threadId: string;
	ordinal: number;
	range: { fromSeq: number; toSeq: number };
	createdAt: number;
	producedBy: 'llm' | 'deterministic';
	model?: string;
	frozen: true;
	body: IEpisodeBody;
}

/** ساختار مهندسی‌شده‌ای که جایگزین «نثر آزاد» می‌شود. */
export interface IEpisodeBody {
	goal: string;
	decisions:   { what: string; why: string; alternatives?: string[]; sourceIds: number[] }[];
	/** ← قلب این تسک: مسیرهایی که رفته شد و رد شد */
	rejected:    { approach: string; reason: string; evidence?: string; sourceIds: number[] }[];
	failures:    { attempt: string; error: string; resolution: 'fixed' | 'abandoned' | 'open'; sourceIds: number[] }[];
	corrections: { userSaid: string; ruleDerived?: string; sourceIds: number[] }[];
	invariants:  string[];        // قواعد دائمی کاربر («همیشه pnpm»، «هرگز force-push»)
	artifacts:   { files: string[]; symbols: string[]; commands: string[]; configs: string[] };
	state:       { done: string[]; inProgress: string[]; verified: string[] };
	next:        string[];
	openQuestions: string[];
}

/** حافظه‌ی کاریِ ارسال‌شونده — از ادغام قطعی اپیزودها ساخته می‌شود. */
export interface IWorkingBrief {
	threadId: string;
	revision: number;             // فقط روی مرز اپیزود +۱ می‌شود (D5)
	builtFromEpisodes: number[];
	builtAtSeq: number;
	tokens: number;
	text: string;                 // بلاک رندرشده‌ی <working_memory>
	merged: IEpisodeBody;         // نسخه‌ی ساخت‌یافته برای UI و دیباگ
}
```

سیاست‌ها در `src/vs/workbench/contrib/void/common/ledgerPolicy.ts` (همه قابل override از settings):

| ثابت | پیش‌فرض | توضیح |
|---|---|---|
| `EPISODE_TARGET_TOKENS` | 60_000 | وقتی journal خلاصه‌نشده از این بیشتر شد، اپیزود بسته می‌شود |
| `EPISODE_MIN_TOKENS` | 12_000 | زیر این حد اپیزود بسته نمی‌شود (مگر پایان thread) |
| `EPISODE_SUMMARY_MAX_TOKENS` | 900 | سقف بدنه‌ی هر اپیزود |
| `BRIEF_MAX_TOKENS` | 4_000 | سقف حافظه‌ی کاری |
| `TAIL_MIN_MESSAGES` | 8 | حداقل پیام عیناً |
| `TAIL_BUDGET_RATIO` | 0.45 | سهم tail از بودجه‌ی ورودی |
| `RECALL_MAX_TOKENS` | 8_000 | سقف نتایج بازگشایی در یک نوبت |
| `SEND_TARGET_RATIO` | 0.60 | هدف پرشدگی پنجره قبل از اقدام |
| `INLINE_MAX_CHARS` | 64_000 | بالاتر از این، محتوا به blob می‌رود |
| `JOURNAL_ROTATE_BYTES` | 8 MiB | چرخش فایل journal |
| `CACHE_IDLE_COMPACT_MS` | 3_600_000 | تریگر زمانی (هم‌راستا با F2): بعد از یک ساعت بی‌کاری، بستن اپیزود «مجانی» است |

---

## ۶. الگوریتم‌ها

### ۶-۱. بستن اپیزود (episode boundary)
اپیزود وقتی بسته می‌شود که **همه‌ی** شرط‌های زیر برقرار باشند:

1. توکن‌های خلاصه‌نشده ≥ `EPISODE_TARGET_TOKENS` **یا** (بی‌کاری > `CACHE_IDLE_COMPACT_MS` و توکن‌ها ≥ `EPISODE_MIN_TOKENS`) **یا** فراخوان دستی `/compact`
2. مرز روی یک پیام `user` باشد (هیچ جفت assistant→tool شکسته نشود)
3. `toSeq` حداقل `TAIL_MIN_MESSAGES` پیام با انتهای journal فاصله داشته باشد

بستن اپیزود **غیرهمزمان و غیرمسدودکننده** است: درخواست جاری با brief قبلی می‌رود؛ اپیزود
در پس‌زمینه ساخته و ثبت می‌شود و از درخواست **بعدی** اثر می‌گذارد. (استثنا: مسیر بازیابی
از خطای context overflow که همان‌جا منتظر می‌ماند.)

### ۶-۲. تولید بدنه‌ی اپیزود
- خروجی **JSON با schema بالا** خواسته می‌شود، نه markdown: `response_format` اگر provider
  پشتیبانی کند؛ وگرنه پرامپت «فقط JSON» + parser مقاوم (برش از اولین `{` تا آخرین `}`،
  تعمیر کامای اضافی و کوت تک).
- در پرامپت صریح: «هر ادعا `sourceIds` داشته باشد»، «حدس نزن»، «هر رویکردی که کاربر رد
  کرد یا شکست خورد **باید** در `rejected`/`failures` بیاید حتی اگر جزئی به‌نظر برسد»،
  «شناسه‌ها (مسیر، پیام خطا، نام) را هرگز خلاصه نکن».
- **fallback قطعی (بدون LLM):** استخراج مکانیکی —
  `invariants` از regex دستوری کاربر (`از این به بعد`، `همیشه`، `هرگز`، `always`, `never`, `do not`)،
  `failures` از پیام‌های ابزار با `exitCode != 0` یا الگوی خطا،
  `artifacts.files` از مسیرهای دیده‌شده در پارامترهای ابزار،
  `corrections` از پیام‌های کاربر که بلافاصله بعد از یک پیام assistant با نشانه‌ی نفی می‌آیند.
  کیفیتش پایین‌تر است ولی **هرگز شکست نمی‌خورد**؛ `producedBy: 'deterministic'` می‌گیرد.
- اعتبارسنجی: اگر خروجی LLM در `rejected`/`invariants` خالی بود ولی استخراج مکانیکی چیزی
  پیدا کرد، نتیجه‌ی مکانیکی **ادغام** می‌شود (اتحاد، نه جایگزینی).

### ۶-۳. ادغام قطعی brief (D3) — قوانین دقیق
نرمال‌سازی کلید: `trim` + کوچک‌سازی + یکسان‌سازی فاصله + حذف نقطه‌گذاری انتهایی.

| بخش | قانون ادغام | سقف |
|---|---|---|
| `invariants` | اتحاد؛ تکراری حذف؛ در تعارض، جدیدتر برنده و قدیمی با نشانه‌ی `(superseded)` نگه داشته می‌شود | 40 |
| `rejected` | اتحاد بر کلید `approach`؛ `reason` از جدیدترین؛ **هرگز حذف نمی‌شود مگر با سقف** (بیرون‌ریزی: قدیمی‌ترینِ بدون ارجاع اخیر) | 30 |
| `corrections` | اتحاد بر `ruleDerived ?? userSaid` | 20 |
| `decisions` | اتحاد بر `what`؛ **اگر تصمیمی بعداً در `rejected` ظاهر شد، از `decisions` خارج و به `rejected` منتقل می‌شود** (ماشین حالتِ صحت) | 25 |
| `failures` | فقط `resolution != 'fixed'`؛ حل‌شده‌ها به یک شمارنده تبدیل می‌شوند | 15 |
| `artifacts.*` | رتبه‌بندی بر اساس بسامد تکرار در اپیزودها | 60 / 40 / 20 / 20 |
| `state`, `next` | فقط از **آخرین** اپیزود (طبق تعریف، وضعیت جاری است) | — |
| `goal` | `original_goal` از اپیزود ۱ + `current_goal` از آخرین اپیزود | — |
| `openQuestions` | اتحاد منهای مواردی که در `decisions` بعدی پاسخ گرفته‌اند | 10 |

اگر بعد از ادغام از `BRIEF_MAX_TOKENS` بیشتر شد، به‌ترتیب کوتاه می‌شود:
`artifacts` → `failures(fixed)` → `decisions` قدیمی → `openQuestions`.
**`invariants`، `corrections` و `rejected` هرگز اولین قربانی نیستند** — اینها دلیل وجود این تسک‌اند.

### ۶-۴. رندر (ترتیب پایدار)

```
<working_memory revision="12" episodes="1-8" covers_seq="1-4193">
  <goal original="…" current="…"/>
  <invariants>…</invariants>
  <rejected_approaches>
    <item approach="…" reason="…" episode="3"/>
  </rejected_approaches>
  <open_failures>…</open_failures>
  <user_corrections>…</user_corrections>
  <decisions>…</decisions>
  <artifacts files="…" symbols="…" commands="…"/>
  <state done="…" in_progress="…" verified="…"/>
  <next>…</next>
  <recall_hint>برای دیدن عین گفتگوی قدیمی از ابزار recall_history استفاده کن.</recall_hint>
</working_memory>
```

مرتب‌سازی درون هر بخش **قطعی** است (اپیزود صعودی، سپس الفبایی) تا خروجی بازتولیدپذیر باشد.

### ۶-۵. پایداری prompt-cache (D5)
- `brief.text` فقط وقتی عوض می‌شود که `revision` بالا برود؛ `revision` فقط با انجماد یک
  اپیزود جدید یا تغییر pin/rule زیاد می‌شود.
- Assembler یک assert سبک دارد: اگر بین دو درخواست متوالی بدون تغییر `revision` بایت‌های
  prefix عوض شده باشند → `console.warn` + شمارنده‌ی متریک `ledger.cacheBreak`.
- ترتیب مونتاژ همیشه: `system → brief → pinned → recalled → tail` (پرتغییرترین بخش انتهای payload).

### ۶-۶. بازیابی (L3)
دو ابزار داخلی جدید در `voidInternalToolService`:

```
recall_history({ query, threadScope?: 'current' | 'all', limit? })
  → [{ episode, seqRange, role, ts, snippet, score, why }]
expand_history({ fromSeq, toSeq })   // سقف RECALL_MAX_TOKENS، بریدن از وسط با نشانه
```

رتبه‌بندی: `0.45·BM25 + 0.25·cosine + 0.15·تازگی + 0.15·هم‌پوشانی مسیر فایل با context جاری`.
بدون embedding، وزن cosine به BM25 منتقل می‌شود (D6).
نتایج `why` دارند (کدام ترم‌ها مچ شدند) — هم برای دیباگ، هم برای پنل شفافیت C2.

---

## ۷. فازهای اجرا

هر فاز = یک commit مستقل + پورت live-patch + تست owner. هیچ فازی مسیر ارسال را نمی‌شکند.

### فاز ۰ — ژورنال (بدون تغییر رفتار)
- `common/ledgerTypes.ts`، `common/ledgerPolicy.ts`
- `browser/contextLedgerService.ts`: `append()`, `readRange()`, `readTail()`, `stats()`
  - نوشتن append با صف و flush هر ۳۰۰ms یا ۶۴KB (هرکدام اول)؛ چرخش فایل؛ blob برای غول‌ها
  - قفل چندپنجره‌ای: `meta.json` + `lastSeq` با compare-and-set؛ در تعارض، seq از فایل بازخوانی می‌شود
- اتصال نوشتن از `chatThreadService._addMessageToThread` و مسیر tool result — **فقط نوشتن**؛ مسیر خواندن دست‌نخورده
- مهاجرت یک‌باره: threadهای موجود از `THREAD_STORAGE_KEY` به journal **کپی** می‌شوند
  (`migratedAt` در meta). مهاجرت فقط-کپی است و `THREAD_STORAGE_KEY` دست‌نخورده می‌ماند تا
  وقتی flag پیش‌فرض روشن بماند و owner تأیید کند — این تنها راهی است که تضمین
  «flag=off ⇒ رفتار دقیقاً امروز» در فاز ۲ معنا پیدا کند
- ✅ خروجی قابل تست: `.inverse/ledger/<id>/journal/000001.jsonl` پر می‌شود و IDE کند نمی‌شود

### فاز ۱ — اپیزودها
- `browser/episodeSummarizer.ts`: تشخیص مرز، پرامپت JSON، parser مقاوم، fallback مکانیکی، انجماد روی دیسک
- اجرای پس‌زمینه بعد از پایان هر turn
- ✅ بعد از یک گفتگوی طولانی، `episodes/ep-0001.json` با `rejected`/`invariants` پرشده وجود دارد

### فاز ۲ — brief و assembler (تعویض مسیر ارسال)
- `browser/workingBriefBuilder.ts` (ادغام قطعی) + `browser/contextAssembler.ts`
- `_maybeCompactThreadForSend` به assembler جدید سوئیچ می‌شود، پشت flag `ni.context.ledger.enabled`
  (پیش‌فرض روشن، قابل خاموش کردن برای مقایسه)
- `conversationCompactor` **حذف نمی‌شود**: مسیر امن برای threadهای مهاجرت‌نشده و حالت flag=off
- ✅ payload ارسالی مستقل از طول thread ثابت می‌ماند

### فاز ۳ — بازیابی
- `DB_VERSION 2` + storeهای جدید + ایندکس‌گذاری هنگام append (async، idle)
- ابزارهای `recall_history` / `expand_history` + backfill تدریجی برای threadهای قدیمی
- ✅ سؤال درباره‌ی چیزی از ۲۰۰ نوبت قبل، با یک فراخوان ابزار جواب درست می‌گیرد

### فاز ۴ — اندازه‌گیری و شفافیت (تغذیه‌ی C2/C7/Q1)
- توکن‌شمار واقعی: `usage` برگشتی provider ثبت می‌شود؛ تخمین `chars/4` فقط پیش از ارسال و با
  ضریب کالیبراسیون per-model که از نسبت تخمین/واقعی یاد گرفته می‌شود
- `ContextUsageReport` از assembler (دقیقاً همان شکلی که C2 می‌خواهد)
- دستورهای `/compact`، `/recall <query>`، `/memory` + کارت جمع‌شونده‌ی brief در SidebarChat
- `getSessionCost` واقعی می‌شود (Q1)
- ✅ gauge با `usage` واقعی provider ±۵٪ می‌خواند

### فاز ۵ — یکپارچه‌سازی سه مسیر (D4)
- `agentExecutor._compactHistoryIfNeeded` → assembler مشترک؛ `history.length = 0` حذف
- `workflowAgentService._appendAgentConversation` → `ledger.append`؛ `splice`/`shift` حذف
- کلید حافظه `conversationId` (نه `agentId`) — باگ هم‌زمانی M1 اینجا بسته می‌شود
- ✅ هیچ مسیری در کد باقی نمی‌ماند که پیام را واقعاً دور بریزد

---

## ۸. اعداد هدف

- گفتگوی ۱۰M توکنی ≈ ۱۶۷ اپیزود × ۶۰k (طبق `EPISODE_TARGET_TOKENS`)؛ هر اپیزود ~۹۰۰ توکن
  ⇒ brief خام ~۱۵۰k ⇒ بعد از ادغام قطعی و سقف‌ها: **~۳-۴k توکن**
- payload هر نوبت: `system(~10k) + brief(4k) + recalled(≤8k) + tail(≤40k)` ⇒ **زیر ۶۰k و ثابت**
- هزینه‌ی خلاصه‌سازی: **یک LLM call به‌ازای هر ~۶۰k توکن** (~۱۶۷ call در کل عمر گفتگوی ۱۰M)
- مصرف دیسک: ۴۰MB journal + ~۵۰۰KB اپیزودها + ایندکس

---

## ۹. ریسک‌ها و تخفیف

| ریسک | تخفیف |
|---|---|
| LLM خروجی JSON نامعتبر بدهد | parser مقاوم → یک retry با پرامپت سخت‌گیرتر → fallback مکانیکی |
| اپیزود مهم بد خلاصه شود | `sourceIds` نگه داشته می‌شود؛ کاربر می‌تواند اپیزود را باز کند؛ brief همیشه `recall_hint` دارد |
| نوشتن روی دیسک fail شود (مجوز/فضا) | `withInverseWriteAccess` + fallback in-memory + هشدار (نه خطا) |
| دو پنجره‌ی IDE روی یک thread | قفل `meta.json` + بازخوانی `lastSeq` در تعارض |
| رشد بی‌رویه‌ی `rejected` | سقف ۳۰ + بیرون‌ریزی قدیمی‌ترینِ بدون ارجاع — و همه‌شان همچنان در اپیزودها و journal هستند |
| کندی UI موقع مهاجرت | مهاجرت idle و chunked (۵۰ پیام در هر tick) با نوار پیشرفت |
| شکستن prompt-cache | assert بند ۶-۵ + متریک `ledger.cacheBreak` |

---

## ۱۰. معیارهای پذیرش

**عملکرد و مقیاس**
- [ ] thread مصنوعی ۱۰M توکنی: payload هر درخواست < ۶۰k توکن و **مستقل از طول thread**
- [ ] زمان مونتاژ (p95) < ۱۵۰ms؛ زمان append (میانگین مستهلک) < ۵ms؛ IDE در طول تست قفل نمی‌شود
- [ ] بعد از restart، brief **بایت‌به‌بایت** همان است (هیچ خلاصه‌سازی دوباره‌ای رخ نمی‌دهد)

**حفظ اطلاعات (قلب تسک)**
- [ ] تست «۲۰۰ تا»: یک invariant در اپیزود ۱ تزریق شود؛ بعد از ۲۰۰ اپیزود **عیناً** در brief باشد
- [ ] رویکردی که در اپیزود ۳ رد شد، در اپیزود ۵۰ دوباره پیشنهاد نشود (ارزیابی دستی روی ۳ سناریو)
- [ ] هیچ مسیری داده حذف نکند: تست واحد + گیت grep روی `history.length = 0` و `splice` در مسیرهای حافظه
- [ ] `recall_history` روی چیزی از ۲۰۰ نوبت قبل، نتیجه‌ی درست با `seq` صحیح برگرداند
- [ ] `expand_history` عین متن اصلی را برگرداند (هش‌برابری با journal)

**تاب‌آوری**
- [ ] provider قطع باشد → اپیزود `deterministic` ساخته می‌شود، ارسال بلاک نمی‌شود
- [ ] بدون provider embedding → بازیابی با BM25 کار می‌کند، هیچ خطایی در کنسول نیست
- [ ] flag خاموش → رفتار دقیقاً همان `conversationCompactor` امروز

**فرایند (طبق `AGENTS.local.md`)**
- [ ] پورت `tools/live-patch.py` برای هر ۵ فاز + `--verify` سبز
- [ ] تست owner روی نسخه‌ی نصبی (گیت ۲)
- [ ] بدون کپی کد از هیچ منبع بیرونی (گیت لایسنس)

---

## ۱۱. تست‌ها

`src/vs/workbench/contrib/void/test/browser/contextLedger.test.ts`

1. `journal`: append/rotate/blob/بازخوانی range؛ گسست seq تشخیص داده شود
2. `boundary`: هرگز روی جفت assistant→tool نبرد؛ حداقل tail حفظ شود
3. `merge`: هر ۹ قانون جدول ۶-۳ یک تست؛ مخصوصاً «تصمیم رد شده از decisions به rejected منتقل شود»
4. `brief stability`: دو build متوالی با ورودی یکسان → رشته‌ی یکسان
5. `budget`: overflow → ترتیب کوتاه‌سازی رعایت شود و `invariants/rejected/corrections` سالم بمانند
6. `deterministic fallback`: بدون LLM، بدنه‌ی معتبر با `invariants` استخراج‌شده تولید شود
7. `assembler`: payload زیر بودجه؛ ترتیب بخش‌ها ثابت
8. fixture generator: ساخت thread مصنوعی N توکنی برای تست‌های مقیاس

---

## ۱۲. نسبت با بقیه‌ی تسک‌ها

| تسک | نسبت |
|---|---|
| **M1** ماندگاری گفتگو | زیرمجموعه‌ی فاز ۰ و ۵ می‌شود (journal همان persistence است) |
| **M2** بازیابی برداری | زیرساخت مشترک با فاز ۳؛ حافظه‌ی پایدار هم روی همین ایندکس می‌نشیند |
| **M3** ثبت خودکار | `invariants` و `corrections` اپیزودها ورودی مستقیم auto-capture هستند |
| **M4** @Docs | همان ایندکس، namespace متفاوت |
| **C2** gauge | `ContextUsageReport` فاز ۴ دقیقاً ورودی C2 است |
| **C7** UX compaction | فاز ۴؛ کارت summary روی `IWorkingBrief.merged` رندر می‌شود |
| **F2** compaction مکانیکی | fallback قطعی ۶-۲ + تریگر `CACHE_IDLE_COMPACT_MS` همان ایده‌اند، درون این معماری |
| **F4** knowledge files | `invariants` می‌تواند به فایل knowledge صادر شود |
| **Q1** هزینه | توکن‌شمار واقعی فاز ۴ |
| **C4** pinned | pinned از compaction مصون است — assembler آن را قبل از recalled می‌گذارد |

---

## ۱۳. وضعیت اجرا (۱۴۰۵/۰۶/۱۴ — session اول پیاده‌سازی)

**پیاده‌سازی‌شده روی سورس** (شاخه‌ی `feat/context-ledger`):

| کامیت | محتوا |
|---|---|
| `938d608` | قراردادهای `ledgerTypes` + `ledgerPolicy` |
| `cda503d` | flag سراسری `contextLedgerEnabled` + toggle در Settings |
| `ef028bc` | فاز ۰ — سرویس journal (CAS چندپنجره‌ای، blob، write-once اپیزودها) |
| `bb3dd15` | فاز ۱ — خلاصه‌ساز اپیزود (schema ساخت‌یافته + fallback مکانیکی) |
| `33bf175` | فاز ۲الف — ادغام قطعی brief (۹ قانون) |
| `f62ec41` | فاز ۲ب — assembler بودجه‌محور + پایداری prefix (D5) |
| `2434cc1` | اتصال مسیر چت (هوک نوشتن، مهاجرت copy-only، بستن اپیزود) |
| `2968638` | فاز ۵ — executor + workflow روی Ledger + کلید conversationId |
| `8458f3a` | M2 — بازیابی hybrid حافظه (برداری + واژگانی + pin) |
| `bfa2df8` | ابزارهای recall/expand + هزینه‌ی واقعی session |

**تأییدشده با تست standalone:** merge laws ۹گانه، رندر بایت‌به‌بایت پایدار،
parser مقاوم JSON، استخراج مکانیکی، مرز اپیزود، flush/CAS/blob/write-once سرویس
journal (با stub)، و مسیر کامل چت (مهاجرت → assembly → دو بستن اپیزود متوالی
با revision bump). دو باگ واقعی در همین تست‌ها پیدا و رفع شد: فراخوانی
`readRange` بدون threadId و انتخاب مجدد مرز قبلی در بستن متوالی.

**باقی‌مانده (به ترتیب):**
1. **پورت live-patch** (دروازه‌ی ۴ `AGENTS.local.md`) — حجم بالای JS دستی؛ session جداگانه
2. تست owner روی نسخه‌ی نصبی + تست مقیاس ۱۰M (بند ۱۱-۸)
3. ثبت `usage` واقعی provider (نیازمند تغییر OnFinalMessage در ۶ provider — فاز ۴ کامل)
4. M3 (auto-capture از `invariants` اپیزودها + تب Memory) و M4 (docs KB) روی همین زیرساخت
5. `/compact` خطی و کارت brief در UI (C7)

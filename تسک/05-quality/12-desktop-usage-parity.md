# Q12 — `usage` روی مسیر desktop نمی‌رسد (شکاف web ↔ electron-main)

- **اولویت:** **P0** | **برآورد:** S | **وضعیت:** 🟡 (سورس + تست پاریتی سبز؛ پورت live-patch و تست owner باز) | **وابستگی:** —
- **کشف:** ۲۰۲۶-۰۹-۰۸، حین [ممیزی سه‌گانه‌ی تسک‌ها](task-vs-code-audit-2026-09-08.md)
- **اثر روی تسک‌های موجود:** [Q1](01-cost-usage-tracking.md) (هزینه)، [M6](../01-memory/06-ledger-hardening.md) (ادعای «usage واقعی»)، [C2](../02-context/02-context-gauge-ui.md) (gauge روی عدد واقعی)

## مسئله

دو پیاده‌سازی موازی از `sendLLMMessage` داریم. نسخه‌ی `common` (وب) شیء `usage`
را به `onFinalMessage` می‌دهد؛ نسخه‌ی `electron-main` — **همانی که در اپ نصب‌شده
اجرا می‌شود** — نمی‌دهد:

| provider | `common/llmMessage/sendLLMMessage.impl.ts` | `electron-main/llmMessage/sendLLMMessage.impl.ts` |
|---|---|---|
| OpenAI-compatible | خط ۴۶۷ — `…, usage)` ✅ | خط ۴۶۸ — بدون `usage` ❌ |
| Anthropic | خط ۶۷۰ — `…, usage)` ✅ | خط ۶۶۷ — بدون `usage` ❌ |

و کانال desktop صراحتاً همان نسخه‌ی electron-main را صدا می‌زند
(`electron-main/sendLLMMessageChannel.ts:12`).

```bash
grep -n "onFinalMessage({" src/vs/workbench/contrib/void/common/llmMessage/sendLLMMessage.impl.ts
grep -n "onFinalMessage({" src/vs/workbench/contrib/void/electron-main/llmMessage/sendLLMMessage.impl.ts
# خطوط ۴۶۷/۶۷۰ در اولی usage دارند؛ ۴۶۸/۶۶۷ در دومی ندارند
```

## چرا P0 است

این یک باگ آرایشی نیست — **ورودیِ سه قابلیتِ دیگر را خالی می‌کند** و همه‌شان
بی‌سروصدا به تخمین fallback می‌کنند:

- `getSessionCost` به‌جای `real` می‌رود سراغ کالیبراسیون/تخمین → عدد هزینه روی
  دسکتاپ هیچ‌وقت واقعی نیست، ولی مثل عدد واقعی نمایش داده می‌شود.
- ادعای «usage واقعی» در M6 روی دسکتاپ برقرار نیست؛ M6 با فرض بسته‌شدنِ این
  مسیر ✅ خورده بود.
- gauge ی که در [C2](../02-context/02-context-gauge-ui.md) می‌سازیم روی همان عدد تخمینی
  می‌نشیند و «شفافیت مصرف» را به یک عدد ساختگی تبدیل می‌کند.

بدترین وجهش این است که **هیچ گیتی این را نمی‌گیرد**: هر دو فایل typecheck سبز
می‌گیرند، تست‌ها سبزند، و تفاوت فقط در یک آرگومان اختیاری است.

## معیار پذیرش

1. هر چهار نقطه‌ی `onFinalMessage` در `electron-main` که معادل web شان `usage`
   می‌فرستد، `usage` بفرستد — با همان شکل و همان واحد.
2. یک تست که **برابری قرارداد دو مسیر** را چک کند، نه فقط وجود usage در یکی:
   امضای callback نهایی در `common` و `electron-main` باید هم‌ریخت باشد.
3. تست دستی روی نسخه‌ی نصبی: یک پیام با هر یک از OpenAI-compatible و Anthropic،
   و دیدن اینکه `_ledgerSessionUsage` پر می‌شود (نه مسیر تخمین).
4. بعد از سبزشدن، مارکر [Q1](01-cost-usage-tracking.md) و بند usage در
   [M6](../01-memory/06-ledger-hardening.md) بازبینی شوند.

## ریشه‌ی ساختاری (برای Q3)

این شکاف نمونه‌ی کوچکِ همان مسئله‌ی [Q3](03-unify-agent-stacks.md) است: دو پیاده‌سازی از یک قرارداد که دستی هم‌گام نگه داشته می‌شوند. راه‌حل پایدار، استخراج منطق مشترک provider به یک ماژول و نگه‌داشتن فقط لایه‌ی transport به‌صورت جدا است. تا آن زمان، بند ۲ معیار پذیرش (تست برابری قرارداد) گیت موقتِ همین دریفت است.

## پیشرفت ۲۰۲۶-۰۹-۰۸ (task Q12 — اجرا شده روی سورس)

**G1 (سورس) بسته شد.** تحلیل ممیزی دقیقاً با کد فعلی مطابقت داشت (خطوط ۴۶۷/۶۷۰ در `common` و ۴۶۸/۶۶۷ در `electron-main` قبل از اصلاح؛ بعد از اصلاح: ۴۸۱/۶۸۴).

- **مقایسه‌ی کامل دو فایل (هر ۷ نقطه‌ی فراخوانی در هر فایل):** به‌جز `usage` هیچ فیلد دیگری از قرارداد `onFinalMessage` دریفت نکرده (FIM×۳، Gemini، Bedrock در هر دو طرف یکسان‌اند). سه دریفتِ غیرقراردادی پیدا شد و عمداً دست نخورد (مربوط به Q3): ۱) گارد stream قطع‌شده در مسیر OpenAI-compatible دو طرف پیاده‌سازی متفاوت دارد (desktop از `streamIntegrity` helpers استفاده می‌کند، web اینلاین)، ۲) گارد قطع stream در Gemini **فقط** روی desktop هست، ۳) متن خطای rate-limit مسیر Gemini فقط در desktop لینک Help دارد.
- **اصلاح (۲ نقطه + لوله‌کشی):** در `electron-main/llmMessage/sendLLMMessage.impl.ts`: ۱) `stream_options: { include_usage: true }` به درخواست OpenAI-compatible (بدون این، usage هرگز نمی‌رسید)، ۲) استخراج `usage` از chunk نهایی، ۳) محاسبه‌ی `usage` از `response.usage` آنتروپیک، ۴) ارسال `usage` در هر دو نقطه‌ی `onFinalMessage` — همان شکل/واحد/نام‌فیلد نسخه‌ی web (`{ input, output }` از `LLMUsage`).
  نکته درباره‌ی «هر چهار نقطه» در بند ۱ معیار پذیرش: در عمل فقط ۲ نقطه در electron-main فاقد usage بود (عدد «چهار» در جدول ممیزی = ۲ ردیف × ۲ فایل)؛ دو مسیر دیگر (Gemini/Bedrock) در هیچ‌کدام از دو طرف usage نمی‌فرستند.
- **تست برابری قرارداد (بند ۲):** `src/vs/workbench/contrib/void/test/node/sendLLMMessageParity.test.ts` — سورس هر دو فایل را parse می‌کند و (الف) تعداد نقاط فراخوانی، (ب) مجموعه‌ی فیلدهای هر نقطه به‌صورت تناظر یک‌به‌یک، (ج) عضویت فیلدها در تایپ `OnFinalMessage`، و (د) لنگرهای usage (فرستادن در دو مسیر success + وجود `include_usage` در هر دو فایل) را چک می‌کند — هر دریفت آینده‌ای (نه فقط usage) را می‌گیرد. اجرا و تأیید شد با رانر خود ریپو (`node test/unit/node/index.js --run …`): **۵ passing**؛ و اعتبارسنجی red/green شد (با بازگردانی موقت باگ، دقیقاً با پیام diff مناسب fail می‌کند). برای اجرای کامل در `npm run test-node` به کامپایل out/ نیاز دارد (فایل تست به‌تنهایی ترنسپایل و از طریق رانر اجرا شد).

**مانده (تا ✅):**
1. ~~commit توسط orchestrator~~ — انجام شد (commit موج ۱، 2026-09-08). تست parity به
   لیست‌های `files` و `tests` در `tools/typecheck-slice.json` هم اضافه شد (۱۰۰ تست standalone سبز).
2. پورت به `tools/live-patch.py` + `--verify` سبز (گیت ۴ AGENTS.local؛ خارج از scope ویرایش این task بود) — نکته: پچ باید هم `onFinalMessage` های minified و هم `stream_options` را در باندل main بپوشاند.
3. تست owner روی نسخه‌ی نصبی (بند ۳ معیار پذیرش): یک پیام با هر یک از OpenAI-compatible و Anthropic و دیدن پرشدن `_ledgerSessionUsage` (نه مسیر تخمین).
4. بعد از سبزشدن: بازبینی مارکر [Q1](01-cost-usage-tracking.md) و بند usage در [M6](../01-memory/06-ledger-hardening.md) (بند ۴ معیار پذیرش) + به‌روز‌کردن ردیف Q12 در جدول وضعیت README.
5. بدهی لینت فایل (موج ۱): ~۳۸۷ مورد auto-fixable در commit جدا پرداخت شد؛ ~۱۵ مورد سخت
   (`no-explicit-any`×۱۰، `code-no-any-casts`×۳، نقض import-pattern×۱، type-assertion×۱)
   می‌ماند — همان خانواده‌ی «نیازمند بازطراحی dispatch» که در [Q11](11-lint-debt-core-chat-files.md)
   ثبت شده. تا پرداخت نشود، هر commit این فایل `--no-verify` می‌خواهد.

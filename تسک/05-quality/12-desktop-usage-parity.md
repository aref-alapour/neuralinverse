# Q12 — `usage` روی مسیر desktop نمی‌رسد (شکاف web ↔ electron-main)

- **اولویت:** **P0** | **برآورد:** S | **وضعیت:** 🔴 | **وابستگی:** —
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

این شکاف نمونه‌ی کوچکِ همان مسئله‌ی [Q3](03-unify-agent-stacks.md) است: دو
پیاده‌سازی از یک قرارداد که دستی هم‌گام نگه داشته می‌شوند. راه‌حل پایدار، استخراج
منطق مشترک provider به یک ماژول و نگه‌داشتن فقط لایه‌ی transport به‌صورت جدا است.
تا آن زمان، بند ۲ معیار پذیرش (تست برابری قرارداد) گیت موقتِ همین دریفت است.

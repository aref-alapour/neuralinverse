# G8 — پورت‌های اختیاری پرارزش (پورت A8)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P2 (Wave 5) | **برآورد:** M جمعاً | **وضعیت:** 🔴 | **وابستگی:** G5، G6

## الف) نمای Jobs
**منبع (تأییدشده):** `comfy_execution/jobs.py` (550 خط): `JobStatus` 23-31،
`validate_job_id` 34-50 (UUID کانونیک lowercase)، `get_all_jobs` 421-482 (نمای یکپارچه
روی running/queued/history)، `classify_job_for_cancel` 485-502 (TOCTOU-safe)،
`cancel_job` 505-550. مسیرهای HTTP در server.py:821-1043.
**در ما:** نمای status/cancel روی صف G6 + run history — اتصال طبیعی به
`backgroundAgentService.ts` (که با A1 تسک‌های agent هم روی آن می‌آیند).

## ب) History با سقف
**منبع:** `MAXIMUM_HISTORY_SIZE = 10000` در execution.py:**1249**؛ درج و eviction FIFO
در 1286-1306 (تصحیح handoff: بازه 1280-1291 فقط cap-check را می‌پوشاند).
**در ما:** نگاشت به `composerHistory.ts` + workspace storage؛ همان الگوی سقف.

## ج) رجیستری جایگزینی نود
**منبع:** `app/node_replace_manager.py` (تأییدشده): `apply_replacements` 61-111
(input/output mapping + re-index لینک‌ها 101-111)، اعمال در server.py:**1110 قبل از
validate_prompt**. ارزان و future-proof برای تغییر نام نودها در آپدیت‌ها.
**در ما:** قبل از G2 اعمال شود؛ جدول mapping در `workflow-engine/` نگهداری.

## د) الگوی نود API (پولی) — پرارزش‌ترین
**منبع (تأییدشده):** `comfy_api_nodes/util/client.py` (1028 خط): ثابت‌های واقعی —
`_MAX_RETRY_AFTER_WAIT=150.0` (88؛ سقف Retry-After خصمانه)، `sync_op` 120
(`retry_backoff=2.0`, `max_retries_on_rate_limit=16`)، `poll_op` 168
(`poll_interval=5.0`, `max_poll_attempts=480`, `retry_backoff_per_poll=1.4`).
`nodes_anthropic.py`: `IO.Hidden.auth_token_comfy_org` (203 — auth در مرز، نه در
گراف)، `price_badge` (208).
**در ما:** برای نودهای سرویس خارجی روی موتور جدید (و هم‌راستا با Q1 هزینه‌ها):
retry با backoff سقف‌دار، job های poll-based، **badge قیمت زنده** (عبارت هزینه که
UI ارزیابی می‌کند)، تزریق credential در executor نه در گراف. (توجه: فایل
`util/server.py` که handoff گفته بود **وجود ندارد** — فهرست درست: `_helpers, client,
common_exceptions, conversions, download_helpers, request_logger, upload_helpers,
validation_utils`.)

## هـ) بهداشت secret (از قلم‌افتاده‌ی handoff — پورت شود)
**منبع:** `SENSITIVE_EXTRA_DATA_KEYS` (execution.py:157)؛ secret ها در **slot ۵**
آیتم صف، فقط لحظه‌ی اجرا re-inject (main.py:388-391)، از history حذف (398) و از
queue listings هم حذف (`_remove_sensitive_from_queue`).
**در ما:** هر کلید sensitive در ورودی workflow (API key های نود API) همین چرخه را
طی کند — هرگز در serialized graph ذخیره/لاگ نشود. هم‌راستا با قاعده‌ی «هرگز secret
پرینت/کامیت نشود» در AGENTS.local.md.

## و) سایر ریزها (از قلم‌افتاده‌ها)
- **`on_prompt_handlers`** (server.py:267, 1457-1461، اجرا در 1076): هوک mutation
  JSON قبل از number-assignment و validation — نقطه‌ی اتصال تمیز برای policy های
  enterprise ما
- **طبقه‌بندی خطای actionable** (execution.py:641-647): در TS به‌صورت هوک
  `classifyFailure(error): {tip, category}` — پیام‌های راهنما روی خطای نود
- **enrichment خروجی** (`enrich_output_with_assets` → `asset_enrichment.py`): فقط
  اگر سیستم asset بخواهیم (فعلاً skip)

## معیارهای پذیرش (خلاصه)
- [ ] jobs: cancel یک job queued و یک running، هر دو مسیر درست
- [ ] history: با 10001 اجرا، قدیمی‌ترین حذف می‌شود
- [ ] replacement: گراف با نام نود قدیمی → قبل از validate نگاشت و اجرا می‌شود
- [ ] API-node: retry از سرور خصمانه (Retry-After بزرگ) → سقف 150s رعایت می‌شود؛
      کلید API در serialized گراف نیست
- [ ] failure tip: خطای معروف → پیام راهنما در پنل خطا

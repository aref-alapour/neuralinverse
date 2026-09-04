# پورت‌های ComfyUI (موتور گراف اجرا) — کاتالوگ راستی‌آزمایی‌شده

> منبع: `C:\Users\jobal\dev\comfyui` — نسخه **0.34.0**، HEAD دقیقاً `acb2a019`
> (هر دو تأیید شدند). پایتون؛ ارزشش برای ما **موتور اجرای گراف** است
> (validation/topology/caching/queue)، نه بخش‌های diffusion/VRAM.
>
> مرجع: `COMFYUI-HANDOFF.md` + راستی‌آزمایی مستقل (سپتامبر ۲۰۲۶) — همه‌ی شماره
> خط‌ها و مکانیزم‌های تسک‌های G با کد واقعی چک شده‌اند.

## قواعد ثابت (از تصمیمات ثبت‌شده‌ی پروژه)

1. کد مستقیم پورت می‌شود (تصمیم owner؛ پروژه داخلی).
2. **Provenance اجباری:** هر فایل پورت‌شده هدر
   `// Ported from comfyui/<path> (GPL-3.0, comfy-org/comfyui @ acb2a019) — ported for internal use.`
   + نگهداری `workflow-engine/PORTED-FROM.md`.
3. **Containment مهندسی:** کل `workflow-engine/` **fork-only** است و هرگز وارد
   PR های upstream (که Apache-2.0 است) نمی‌شود — همان قاعده‌ی `تسک/`؛ در
   `AGENTS.local.md` ثبت شده.
4. قبل از پورت هر ماژول: `git -C C:/Users/jobal/dev/comfyui log --oneline -5 -- <path>`
   (upstream روزانه جلو می‌رود؛ commit مبنا در PORTED-FROM.md ثبت شود).
5. هیچ dependency به comfyui/freebuff اضافه نمی‌شود — کپی در درخت.

## نتیجه‌ی راستی‌آزمایی handoff

گزارش **دقیق و قابل‌اتکا** بود (۱۷ بخش بررسی شد؛ اکثراً VERIFIED). اصلاحات بارور:

| # | ادعا | واقعیت |
|---|---|---|
| 1 | front-jump داخل `PromptQueue` | در `server.py:1078-1086` با **منفی‌کردن number**؛ آیتم صف **۶تایی** است (slot ۵ = sensitive) |
| 2 | WS protocol در server.py:269-327 | آن بازه connection handler + **مذاکره‌ی feature-flags** است؛ emit رویدادها پراکنده (فهرست کامل در G6) |
| 3 | `get_input_data` در 243-319 | در **159-227**؛ 243-319 = `_async_map_node_over_list` (شامل `slice_dict` در 253) |
| 4 | error payload در 743 | 743 = `execution_start`؛ خطاها در 692-699/700-712/522-539/649-655 |
| 5 | `CHECK_LAZY_STATUS` صفت کلاس | **وجود ندارد**؛ متد instance `check_lazy_status` (probe در 506) |
| 6 | تاپل ANCESTOR دو-عنصری | **سه‌عنصری**: (index, **socket**) |
| 7 | `handle_execution_error` همه‌کاره | فقط فرمت/send؛ توقف خواهرها = break در 784-793؛ وابسته‌ها در validate_prompt 1211-1228 |
| 8 | `util/server.py` در comfy_api_nodes | **وجود ندارد** |
| 9 | تاکسونومی خطا کامل | +۳ رشته از قلم افتاده: `exception_during_inner_validation`، `exception_during_validation`، `prompt_outputs_failed_validation` |
| 10 | `is_link` در 987 | 987 داخل `__value__` unwrap است؛ تشخیص در validate_inputs **917-930**؛ و **wrap سمت frontend است** (serializer ما!) |

## گنج‌های از-قلم-افتاده (در تسک‌ها لحاظ شد)

- **`cache_provider.py`** — کش خارجی قابل‌اتصال (Redis/S3 برای background agents)
- **بهداشت secret** — `SENSITIVE_EXTRA_DATA_KEYS`، slot جدا در صف، حذف از history/listings (G8-هـ)
- **semantics قطع × کش** — خروجی هر نود لحظه‌ی تکمیل کش می‌شود → خروجی جزئی بعد از interrupt زنده است (G5-8)
- **پیشوندهای deterministic ephemeral** — پیش‌شرط کش زیرگراف‌ها (G1-5)
- **`get_output_from_returns`** — پروتکل برگشتی NodeOutput/expand (G3-11)
- **flags صف** (`free_memory` = ریست کش) — G6-6
- **`on_prompt_handlers`** — هوک mutation قبل از validation — نقطه‌ی اتصال enterprise (G8-و)
- **پک فیکسچر تست کامل** — `tests/execution/testing_nodes/testing-pack/` شامل WhileLoop/Blocker/Conditions (G3)
- **مذاکره‌ی feature-flags در WS** — G6

## رتبه‌بندی ترجمه (پایتون → TS)

- **ترجمه‌ی مستقیم:** `validation.py`، `graph_utils.py` (is_link/GraphBuilder/Blocker)،
  `graph.py` (DynamicPrompt/TopologicalSort/ExecutionList — `asyncio.Event`→promise)،
  PromptQueue + منطق front-negation، `jobs.py`، `node_replace_manager.py`،
  تاکسونومی خطا + NodeErrors، جدول hidden inputs، batch zipping، نام‌های رویداد،
  طرح mtime+memo فولدرها
- **تطبیق:** loop اصلی `execution.py` (torch/OOM/classify → هوک‌های موتور)، `caching.py`
  (قرارداد serialization مقادیر + سم UNHASHABLE صریح)، `IsChangedCache`، `progress.py`
  (tqdm/preview نمی‌آید)، route ها (aiohttp → سرویس ما)
- **بازطراحی (قرارداد بماند، کد نه):** V3 node API (metaclass/clone/locked-method —
  در G4 فقط interface تایپ‌شده ساختیم)، `RAMPressureCache` (torch/psutil)، خودِ اجرای
  نود (callable پایتون → تابع JS). نکته: async نودها جایی است که JS از پایتون
  **ساده‌تر** درمی‌آید (external-block مستقیم روی native async)

## موج‌ها (از handoff، با وضعیت ما)

| Wave | محتوا | تسک |
|---|---|---|
| 0 | ممیزی + تصمیم extend-vs-replace + اسکلت | **G0** (ممیزی انجام شد ✔ — پیشنهاد: side-by-side + adapter) |
| 1 | graph types + validation + فیکسچرها | **G1، G2** |
| 2 | executor + قرارداد نود + مهاجرت ۳ نود | **G3، G4** |
| 3 | کش + اجرای مجدد جزئی (دموی اصلی) | **G5** |
| 4 | صف/interrupt/progress + nodeInfo | **G6، G7** |
| 5 | پورت‌های اختیاری | **G8** |
| 6 | Track B (سرویس embed) — مستقل | **G9** |

## پیوند با سایر تسک‌ها

- نود adapter «Agent Step» (G4) روی `agentExecutor` فعلی → هیچ agent ای دوباره‌نویسی نمی‌شود
- کش خارجی (G5-8) بعداً کش background agents (A1) هم می‌شود
- الگوی نود API با قیمت زنده (G8-د) ↔ داشبورد هزینه Q1
- A6 (planner/worker) در آینده می‌تواند روی همین موتور به‌صورت گراف اجرا شود

# G7 — خروجی schema نودها (object_info) و combo های فایل‌سیستمی (پورت A7)

- **اولویت:** P1 (Wave 4) | **برآورد:** S/M | **وضعیت:** 🔴 | **وابستگی:** G4
- **منبع (راستی‌آزمایی‌شده):** `server.py:751-798` (`node_info`)، `folder_paths.py`

## چه چیزی پورت می‌شود
`workflow-engine/nodeInfo.ts` — یک تابع که برای هر نود ثبت‌شده:
`{input, inputOrder, output, outputIsList, outputNames, name, displayName,
description, category, outputNode, deprecated/experimental, searchAliases}` تولید
می‌کند. **منبع واحد حقیقت** برای پالت، autocomplete و چک نوع اتصال‌ها.

**فیلدهای اضافه از راستی‌آزمایی (handoff نیاورده بود):** `is_input_list` (758)،
`python_module` (765)، `has_intermiate_output` (772-775)، `output_tooltips` (780-781)،
`dev_only` (787-788)، `api_node` (790-791)، `search_aliases` (793)،
`essentials_category` (795-796). نکته: خرابی serialize یک نود نباید کل payload را
بشکند (per-node try/catch).

## combo های فایل‌سیستمی
الگوی `folder_paths.py` (تأییدشده): لیست فایل‌ها با **اعتبارسنجی mtime دایرکتوری**
(499 — mtime دایرکتوری با add/remove فایل عوض می‌شود) + کش سراسری `filename_list_cache`
+ **memo per-request با `CacheHelper`** (خط 104؛ در route با `with cache_helper:`
فعال می‌شود تا ده‌ها INPUT_TYPES در یک پاس، یک اسکن ببینند).
در VS Code: workspace fs API + FileWatch برای invalidation.

## در ما
- پالت `panels/nodePalette.ts` از nodeInfo تغذیه شود (الان از nodeRegistry مستقیم)
- combo های live: لیست agent ها، لیست workflow ها، لیست skill ها (پس از E2)،
  دایرکتوری‌های watched
- autocomplete نام نود و نام ورودی در propertyPanel

## معیارهای پذیرش
- [ ] پالت و validation هر دو از nodeInfo می‌خوانند (تست: تعریف نود جدید → هر دو
      بدون تغییر کد UI به‌روز)
- [ ] افزودن فایل به پوشه‌ی watched → combo بدون restart تازه می‌شود
- [ ] نود ثبت‌شده‌ی معیوب → در nodeInfo با خطای per-node ظاهر می‌شود، بقیه سالم

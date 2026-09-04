# G2 — موتور Validation (پورت A2)

- **اولویت:** P0 (Wave 1) | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** G1
- **منبع (راستی‌آزمایی‌شده):** `execution.py:846-1120` (`validate_inputs`)، `1128-1247` (`validate_prompt`)، `comfy_execution/validation.py` (58 خط)

## چه چیزی پورت می‌شود
`workflow-engine/validation.ts`:

1. **اعتبارسنجی بازگشتی از نودهای خروجی** (`OUTPUT_NODE=true`) با memoization؛
   `prompt_no_outputs` در 1169.
2. **تشخیص cycle** با پیام قابل‌خواندن `"id (class) -> id (class)"` — `dependency_cycle`
   در 860 (با `cycle_path` + `cycle_nodes`).
3. **ساختار خطای ساخت‌یافته per-node** — قرارداد render شدن در canvas:
   `NodeErrors {errors: [{type, message, details, extra_info}], dependent_outputs, class_type}`
   (ساخت در 1220-1224).
4. **تاکسونومی خطا** (همه با شماره خط تأییدشده): `required_input_missing` (905)،
   `bad_linked_input` (920)، `return_type_mismatch` (940)، `value_smaller_than_min`
   (1022)، `value_bigger_than_max` (1035)، `value_not_in_list` (1070)،
   `invalid_input_type` (1006)، `custom_validation_failed` (1101)، `missing_node_type`
   (1135/1152 — پیام «custom node may not be installed» با `_meta.title`)
   + **سه مورد از قلم‌افتاده‌ی handoff:** `exception_during_inner_validation` (967)،
   `exception_during_validation` (1192)، `prompt_outputs_failed_validation` (1239).
5. **سازگاری نوع با set-semantics** (`validation.py:4-58`): split با کاما (46-47)،
   `"*"` = wildcard (28, 50-51)، overlap = سازگار در حالت non-strict (57-58)،
   strict = subset (53-55)؛ idiom قدیمی `__ne__` در 24؛ `IO.MatchType` passthrough
   (33-34)؛ list-received در برابر Combo (38-39).
6. **coerce درجای** INT/FLOAT/STRING/BOOLEAN (992-1003 — مقدار coerce شده در inputs
   بازنویسی می‌شود)؛ combo-memberhip با **سرکوب لیست گزینه‌ها > ۲۰** (1063-1065).
7. **هوک `validateInputs` نود** با انواع link حل‌شده (`received_types` در 936، تزریق
   به‌عنوان kwarg در 1088-1089، پشتیبانی `**kwargs` با `validate_has_kwargs` در 893/1019).
8. **partial_execution_targets** (server.py:1106-1108 → فیلتر OUTPUT_NODE در
   execution.py:1163-1165) — اجرای زیرمجموعه.

## اتصال به UI
خروجی validation مستقیم به `edges/edgeValidator.ts` و رندر خطای نود در canvas
(propertyPanel + نوار قرمز نود) وصل می‌شود — خطاها value هستند نه exception.

## معیارهای پذیرش
- [ ] فیکسچرهای تست: valid / cycle / missing-input / type-mismatch / out-of-range /
      combo-violation / node-type-missing → ساختار خطا **byte-equivalent** با پایتون
- [ ] coerced value در گراف بازنویسی می‌شود (رفتار درجا حفظ شود)
- [ ] edgeValidator موجود از همان NodeErrors تغذیه می‌شود (یک منبع حقیقت)
- [ ] تست‌های آینه: `tests-unit/execution_test/validate_node_input_test.py`

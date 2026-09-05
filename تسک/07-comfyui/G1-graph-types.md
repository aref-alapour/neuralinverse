# G1 — فرمت گراف و DynamicGraph (پورت A1)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P0 (Wave 0/1) | **برآورد:** S/M | **وضعیت:** 🔴 | **وابستگی:** G0
- **منبع (راستی‌آزمایی‌شده):** `script_examples/basic_api_example.py`، `comfy_execution/graph_utils.py`، `comfy_execution/graph.py:21-62`

## چه چیزی پورت می‌شود
`workflow-engine/graph.ts`:

1. **فرمت prompt:** `WorkflowGraph = Map<NodeId, {classType, inputs: Record<string, unknown>}>`
2. **نمایش link:** آرایه‌ی ۲تایی `[sourceNodeId, outputSlotIndex]`؛ تشخیص با `isLink`
   (`graph_utils.py:1-10` — لیست طول-۲ با [string, number]).
   **تصحیح:** در `validate_inputs` تشخیص با `isinstance(val, list) && len==2` در
   خطوط **917-930** است؛ خط 987 داخل unwrap است.
3. **escape-hatch `{"__value__": [...]}`:** مقدار widget که ذاتاً list است باید
   wrap شود چون لیست = سینتکس link. **نکته‌ی مهم از راستی‌آزمایی:** unwrap فقط در
   `execution.py:983-990` (سمت validate) انجام می‌شود — **wrap کردن کار serializer
   فرانت‌اند است**؛ پس `composerSerializer.ts` ما باید سمت wrap را پیاده کند.
4. **DynamicPrompt** (`graph.py:21-62`): گراف پایه + نودهای **ephemeral** اضافه‌شده
   در runtime با سه نگاشت (`ephemeral_prompt/ephemeral_parents/ephemeral_display`)؛
   `get_real_node_id` (45-48، پیمایش زنجیره‌ی parent) و `get_display_node_id` (53-56)
   — رویدادهای نودهای داینامیک به نود مرئیِ سازنده نسبت داده می‌شوند.
5. **پیشوندهای deterministic برای ephemeral:** `GraphBuilder.set_default_prefix`/
   `alloc_prefix` (`graph_utils.py:26-42`) با الگوی `root.call_index.graph_index` —
   این پیشوندها id های زیرگراف را برای **cache-stability** deterministic می‌کنند
   (مورد از قلم‌افتاده‌ی handoff؛ بدون آن کش زیرگراف‌ها بی‌فایده است).

## تفاوت‌های TS
- `Map` به‌جای dict پایتون — **ترتیب درج** برای signature ها حیاتی است (G5)؛ هرجا
  پایتون `sorted(inputs.keys())` دارد مرتب‌سازی را صریح پورت کن
- disposable ها با `IDisposable` طبق قرارداد VS Code

## معیارهای پذیرش
- [ ] گراف‌های serializer-سازگار round-trip می‌شوند (فیکسچر: گراف ساده + گراف با link + گراف با مقدار list-wrap)
- [ ] نود ephemeral اضافه‌شده در runtime → رویدادش به display node صحیح نسبت داده می‌شود
- [ ] `isLink` مقادیر list واقعی wrap‌نشده را به‌عنوان link تشخیص نمی‌دهد اگر valid نباشد (رفتار validate)

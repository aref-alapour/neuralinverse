# G4 — قرارداد نود تایپ‌شده (پورت A4)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P0 (Wave 2، هم‌زمان با G3) | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** G1
- **منبع (راستی‌آزمایی‌شده):** `nodes.py` (CheckpointLoaderSimple در 616، KSampler در 1597، NODE_CLASS_MAPPINGS در 2066)، `comfy/comfy_types/node_typing.py`، `comfy_api/latest/_io.py`

## قرارداد TS (طبق طرح handoff + تصحیح‌ها)

```ts
interface WorkflowNodeDef {
  id: string;                       // class_type
  displayName?: string; category: string;
  inputTypes(): NodeInputSpec;      // {required, optional, hidden}
  outputs: readonly string[];       // RETURN_TYPES
  outputNames?: readonly string[];
  isOutputNode?: boolean;           // OUTPUT_NODE
  execute(inputs, ctx): Promise<NodeResult | 'PENDING'>;
  isChanged?(inputs): unknown;      // IS_CHANGED
  validateInputs?(inputs, linkTypes): true | string;
  checkLazyStatus?(available: string[]): string[];  // ← تصحیح مهم (پایین)
  notIdempotent?: boolean;
  hasIntermediateOutput?: boolean;
  inputIsList?: boolean; outputIsList?: boolean;
}
```

**تصحیح‌های راستی‌آزمایی:**
- **`CHECK_LAZY_STATUS` به‌عنوان صفت کلاس وجود ندارد** — V1 با **متد instance به
  نام `check_lazy_status`** کار می‌کند (probe در execution.py:506، فراخوانی 511)؛
  V3 با classmethod تشخیص داده می‌شود (504). در TS، متد اختیاری روی interface درست است.
- واژگان تکمیلی که رفتار موتور را تغذیه می‌کنند و باید در قرارداد باشند:
  `NOT_IDEMPOTENT`، `INPUT_IS_LIST`/`OUTPUT_IS_LIST`، `HAS_INTERMEDIATE_OUTPUT`،
  hidden-`UNIQUE_ID` (اثر مستقیم بر signature کش در G5).
- KSampler مرجع کامل widget spec است (seed max `0xffffffffffffffff`،
  `control_after_generate: true`).

## تصمیم V1/V3 (تأیید تحلیل مستقل)
V3 در پایتون فقط types نیست — **مسیر موازی کامل داخل execution.py است** (شاخه‌های
دوگانه در get_input_data 160-207، process_inputs 273-289، validate_inputs 880-885:
`VALIDATE_CLASS`، `PREPARE_CLASS_CLONE`، `make_locked_method_func`، DynamicCombo/
Autogrow). رتبه‌بندی ترجمه: **V3 = بازطراحی**، نه ترجمه. ما فقط قرارداد تایپ‌شده‌ی
ساده می‌سازیم و واژگان V1 (رشته‌های نوع، combo-as-list) را حفظ می‌کنیم تا فرمت
serialized سازگار بماند — همان توصیه‌ی handoff که حالا مستند شد.

## سایر پورت‌ها
- **ExecutionBlocker** (`graph_utils.py:140-155`): veto سطح-مقدار که از لینک‌ها عبور
  می‌کند؛ با پیام → خطای ساخت‌یافته `ExecutionBlocked`، بی‌پیام → short-circuit
  بی‌صدا (سایت‌های پایتون: execution.py 261-269 و 522-539).
- **کانال hidden inputs:** PROMPT / DYNPROMPT / UNIQUE_ID / EXTRA_PNGINFO (209-225) —
  نودها کل workflow را می‌بینند و metadata گزارش می‌کنند. Slot های auth (AUTH_TOKEN/
  API_KEY) به G8 موکول (الگوی نود API).
- **`GraphBuilder`** برای زیرگراف runtime (از G1).

## مهاجرت نودهای موجود
`nodeRegistry.ts` فعلی ۶ نوع نمایشی دارد (trigger/agent/conditional/transform/output/
group) با configSchema فرم‌محور. مهاجرت: هر نوع → یک `WorkflowNodeDef` با execute
واقعی (conditional = نود branch با خروجی‌های true/false؛ transform = نود داده‌ی
خالص؛ agent = adapter روی agentExecutor فعلی). **اولین سه نود (agent/conditional/
transform) هدف Wave 2 هستند.**

## معیارهای پذیرش
- [ ] پالت canvas از `WorkflowNodeDef` های رجیسترشده تغذیه می‌شود (مسیر category با /)
- [ ] گراف سریالایزشده‌ی composer از همان نودها روی موتور جدید اجرا می‌شود (headless)
- [ ] ExecutionBlocker با پیام → خطای ساخت‌یافته؛ بی‌پیام → حذف بی‌صدا نودهای پایین‌دست
- [ ] checkLazyStatus با نام ورودی‌های هنوز‌لازم کار می‌کند (فیکسچر lazy از testing-pack)

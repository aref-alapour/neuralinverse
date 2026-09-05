# G3 — اجرای توپولوژیک با re-staging (پورت A3 — قلب موتور)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P0 (Wave 2) | **برآورد:** L | **وضعیت:** 🔴 | **وابستگی:** G1، G2، G4 (هم‌زمان)
- **منبع (راستی‌آزمایی‌شده):** `comfy_execution/graph.py:106-342`، `execution.py:438-662` (execute)، `730-843` (execute_async)، `159-227` (get_input_data)

## هسته‌ی معناشناسی (دقیقاً از کد)

1. **پیمایش:** `TopologicalSort` 106-191 + `ExecutionList` 193-342 — **worklist
   تکرارشونده (stack) است، نه DFS بازگشتی**؛ ورودی‌های `lazy` دنبال نمی‌شوند
   (159-160)، نودهای کش‌شده skip ولی لینک‌هایشان ثبت می‌شوند (161).
2. **bookkeeping بلوک:** `blockCount`/`blocking` (110-111)، strong-link (130-136)؛
   `get_ready_nodes()` = `blockCount===0` (181-182).
3. **مکانیزم واحد re-staging (تأیید مستقیم):** `PENDING` از **سه سایت** برمی‌گردد —
   lazy (507-520 بعد از `make_input_strong_link` 519)، async (554-562 با
   `add_external_block` + unblock)، subgraph (579-613 با `add_ephemeral_node` +
   `ensure_subcache_for`). پاسخ `execute_async`: `unstage_node_execution()` (794-795) →
   نود دوباره وارد صف ready می‌شود. **این سه رفتار را به سه feature جدا نشکنان.**
4. **async در TS ساده‌تر از پایتون است:** coroutine ها به‌صورت task پارک می‌شوند
   (execution.py:292-303) + `CurrentNodeContext` — در TS، async function بومی مستقیم
   روی همان مکانیزم external-block نگاشت می‌شود؛ `unblockedEvent.set()` → resolved promise.
5. **`ux_friendly_pick_node`** (275-312): اولویت output → async → ۱-hop → ۲-hop →
   fallback — پیش‌نمایش‌ها زودتر ظاهر می‌شوند.
6. **cycle داینامیک:** `get_nodes_in_cycle` (325-342، dissolve معکوس)؛ blame در
   `stage_node_execution` 252-261 نودی را ترجیح می‌دهد که display id اش فرق دارد (ephemeral).
7. **tri-state:** `ExecutionResult` در execution.py:52-55 (نه graph.py — تصحیح handoff).
8. **خطا:** «توقف خواهرها» = break در loop اجرا (784-793)؛ «نشانه‌گذاری وابسته‌ها» =
   `dependent_outputs` در validate_prompt (1211-1228). جزئیات send رویدادها → G6.
9. **حل ورودی‌ها:** `get_input_data` **159-227** (تصحیح: نه 243-319) — لینک از کش
   خروجی upstream، ثابت‌ها به آرایه‌ی ۱عنصری، hidden inputs در **209-225** (PROMPT،
   DYNPROMPT، EXTRA_PNGINFO، UNIQUE_ID؛ و AUTH_TOKEN/API_KEY/USAGE_SOURCE برای
   نودهای API — ببین G4/G8).
10. **batch zipping:** `slice_dict` در **253-254** داخل `_async_map_node_over_list`
    (243-319): `{k: v[i if len(v)>i else -1]}` — **تکرار آخرین عنصر = broadcast ضمنی**؛
    `INPUT_IS_LIST` در 245، مسیر تک‌فراخوان 311-312، ادغام `OUTPUT_IS_LIST` در
    `merge_result_data` 322-341.
11. **پروتکل برگشتی نود (از قلم‌افتاده):** `get_output_from_returns` 351-414 — دوگان
    dict/NodeOutput، fan-out ExecutionBlocker به همه‌ی RETURN_TYPES، پروتکل `expand`
    زیرگراف. + `HAS_INTERMEDIATE_OUTPUT` (424-427؛ بازارسال UI نودهای میانی کش‌شده در 812-823).

## معیارهای پذیرش
- [ ] گراف تست async (دو نود آهسته + یک مصرف‌کننده sync) **درهم‌تنیده** اجرا می‌شود نه سریالی
- [ ] نود Switch/lazy فقط شاخه‌ی انتخاب‌شده را اجرا می‌کند
- [ ] هر سه رفتار (lazy/async/subgraph) از یک مسیر re-staging می‌آیند (تست واحد مشترک)
- [ ] broadcast ورودی کوتاه‌تر با تکرار آخرین عنصر (تست slice_dict)
- [ ] فیکسچرهای آینه: `tests/execution/test_execution.py` (1036 خط: lazy_input، cache
      full/partial، cycle + dynamic cycle، for-loop، parallel sleep، block list) +
      `test_async_nodes.py` (16 تست) + پک `tests/execution/testing_nodes/testing-pack/`
      (شامل `TestWhileLoopOpen/Close` و `TestExecutionBlockerNode` و نودهای conditions!)

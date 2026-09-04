# A5 — حالت Plan درجه‌یک (Plan Mode)

- **اولویت:** P2 | **برآورد:** M | **وضعیت:** 🔴 (فقط prompt-level) | **وابستگی:** A2
- **هم‌ارز در Cursor:** Toggle Plan — مدل اول برنامه می‌دهد، تو تأیید می‌کنی، بعد اجرا

## هدف
Plan به‌عنوان یک حالت first-class: toggle در chat/agent → ابزارها فقط-خواندنی → مدل
برنامه‌ی گام‌به‌گام + فایل‌های درگیر تولید می‌کند → کاربر تأیید/ویرایش/رد می‌کند →
اجرا با همان برنامه به‌عنوان brief وظیفه.

## وضعیت فعلی در کد
- Power Mode ابزارهای `plan_mode_enter/exit` + `todo_write` دارد (`planModeTools.ts`) —
  ولی محصول‌سازی نشده
- NI autonomy service صراحتاً plan-approval ندارد («full autonomy, no plan-approval
  gate» — `neuralInverseAgentService.ts:187`)
- `agentTaskDecomposer.ts` تجزیه‌ی وظیفه با LLM دارد (پایه‌ی تولید برنامه)

## طرح پیاده‌سازی
1. toggle «Plan» کنار انتخاب حالت chat (`SidebarChat` حالت‌های ask/reason/copilot/agent)
2. در حالت plan: ScopedToolRegistry فقط ابزارهای خواندنی (read/search/gitStatus/…)؛
   ابزار نوشتن/ترمینال مسدود + پیام روشن به مدل
3. خروجی برنامه با قالب ساخت‌یافته: هدف / گام‌ها (فایل درگیر به ازای هر گام) /
   ریسک‌ها — رندر به‌صورت کارت قابل ویرایش (لیست checkbox)
4. کاربر: **Approve** (اجرا با برنامه به‌عنوان پیام اول + تزریق در system prompt) /
   **ویرایش گام‌ها** / **Reject** (بازگشت به گفتگو)
5. `requirePlanApproval` در `.neuralinverseagent` (پیش‌فرض false تا رفتار فعلی عوض نشود)؛
   اگر true، autonomy service قبل از اجرای ابزار نوشتن، حالت plan را طی کند
6. todo های اجرا (از `todo_write` موجود) در `AgentActivityBox` زنده آپدیت شوند

## معیارهای پذیرش
- [ ] در حالت plan هیچ ابزار نوشتن/اجرایی اجرا نمی‌شود (حتی اگر مدل اصرار کند)
- [ ] برنامه‌ی ساخت‌یافته قابل ویرایش قبل از تأیید است
- [ ] بعد از Approve، اجرا از همان برنامه شروع می‌شود و todo ها زنده پیش می‌روند
- [ ] با `requirePlanApproval: false` رفتار فعلی (خودمختار) دست‌نخورده است

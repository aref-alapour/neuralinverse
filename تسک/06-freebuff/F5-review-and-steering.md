# F5 — جریان بازبینی و هدایت mid-run: propose/apply + best-of-N + steering + ابزارهای UX

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P1 (الف/د) / P2 (ب/ج) | **برآورد:** M/L | **وضعیت:** 🔴 | **وابستگی:** A1 (sub-agent برای ب)، A3 (کنار الف)
- **منبع الگو:** freebuff (راستی‌آزمایی‌شده)

## الف) تفکیک propose/apply — ویرایش امن برای بازبینی

**منبع:** `common/src/tools/params/tool/propose-str-replace.ts` + `propose-write-file.ts` —
«دقیقاً مثل نسخه‌ی معمولی کار می‌کند ولی روی دیسک نمی‌نویسد؛ unified diff برمی‌گرداند»؛
پیشنهادهای متعدد روی یک فایل درست stack می‌شوند؛ فیلد یک‌جمله‌ای `instructions` روی
write_file به‌عنوان خط خلاصه‌ی diff در UI بازبینی.

**پیاده‌سازی:** در حالت‌های نیازمند تأیید (A4): به‌جای اجرای مستقیم ویرایش، shadow
tool های `propose_*` → رندر inline به‌صورت diff decoration در ادیتور (VS Code خودش
این UX را دارد) → دکمه‌ی Apply = `workspace.applyEdit`. یعنی: مدل پیشنهاد می‌دهد،
کاربر با دیدن diff تأیید می‌کند. کاملاً هم‌راستا با approval سه‌سطحی موجود.

## ب) best-of-N برای ویرایش‌های سخت

**منبع:** `agents/editor/best-of-n/` — `editor-multi-prompt.ts` (L97-111): به ازای هر
استراتژی prompt، یک implementor موازی spawn (تنها ابزارشان `propose_*` است!)؛
`best-of-n-selector2.ts`: outputSchema الزامی `{implementationId, reason,
suggestedImprovements}` — انتخاب‌گر diff ها را مقایسه می‌کند؛ برنده توسط coordinator
به‌صورت ویرایش واقعی replay می‌شود. (نسخه‌ی thinker هم دارد: `agents/thinker/best-of-n/`.)

**پیاده‌سازی:** بعد از A1/A6: حالت «deep edit» — N=۲-۳ implementor با پرامپت‌های
متفاوت روی یک فایل، انتخاب‌گر انتخاب می‌کند. فقط برای ویرایش‌های سخت/حیاتی (opt-in)،
چون هزینه×N می‌شود. با `outputValidator` ما schema انتخاب ساده است.

## ج) Steering — پیام کاربر وسط کار agent، بدون abort

**منوع:** `sdk/src/run.ts` گزینه‌ی `drainSteeringMessages` (L200-205، drain در L832)؛
`cli/src/utils/steering-buffer.ts`؛ مصرف در `run-agent-step.ts` (L706+): پیام‌های
صف‌شده در مرز step بعدی به تاریخچه تزریق می‌شوند و turn زنده می‌ماند؛ باقی‌مانده‌ها
جلوی صف دوباره قرار می‌گیرند و حباب چت‌شان جمع می‌شود.

**پیاده‌سازی:** این یکی از ارزان‌ترین قابلیت‌ها با بیشترین اثر UX است:
1. در `SidebarChat`: وقتی thread در حال run است، ورودی فعال بماند (الان عملاً بلاک
   است) با placeholder «پیام هدایتی بفرست…»
2. صف steering در chatThreadService/agentExecutor؛ تزریق در ابتدای iteration بعدی
   به‌عنوان پیام user تگ‌خورده `<steering>`
3. متریک: چند steering پیام واقعاً مسیر run را عوض کرد (گزارش در run history)

## د) واژگان typed برای گفتگوی agent↔UI

**منبع (همه تأییدشده):** `ask-user.ts` — `header ≤18` کاراکتر، حداقل ۲ گزینه،
`multiSelect`، `validation {minLength, maxLength, pattern, patternError}` (L43-61)،
فیلد آزاد «Other» خودکار (L121). `suggest-followups.ts` — کارت‌های پیشنهادی
کلیک‌شونده بعد از پاسخ. `write-todos.ts` — بازنویسی کل لیست todo (نه append؛
semantic تمیز). `render-ui.ts` — ویجت‌های typed که لینک‌ها «مرجع opaque»اند:
مدل هیچ‌وقت URL نمی‌نویسد، runtime جایگزین می‌کند (ضد phishing).

**پیاده‌سازی:** ممیزی `communicationTools.ts` (notify/progress داریم، پرسش ساخت‌یافته
نداریم):
- `ask_user` (با همان اسکیما) → رندر فرم در SidebarChat؛ مکمل intake questions محلی
  (کامیت `9bc1183`): intake قبل از شروع است، ask_user وسط run
- `suggest_followups` → کارت‌های زیر پاسخ نهایی
- `write_todos` → همین TODO list که در A5 (plan mode) لازم است — یک پیاده‌سازی، دو مصرف
- قاعده‌ی opaque-link برای هر ابزار آینده‌ای که URL نشان می‌دهد

## معیارهای پذیرش
- [ ] در حالت confirm: ویرایش به‌صورت پیشنهاد + inline diff + دکمه‌ی Apply جریان می‌گیرد
- [ ] steering: وسط run پیام فرستادم → در iteration بعد اعمال شد، run abort نشد
- [ ] ask_user با validation (pattern) فرم درست رندر و اعتبارسنجی می‌کند
- [ ] write_todos لیست زنده را بازنویسی می‌کند (نه duplicate)
- [ ] (P2) best-of-N روی یک ویرایش سخت، برنده را با diff قابل مقایسه انتخاب می‌کند

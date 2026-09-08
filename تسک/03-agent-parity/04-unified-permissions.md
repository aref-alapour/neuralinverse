# A4 — سیستم مجوز یکپارچه + پیش‌نمایش (Unified Permissions)

- **اولویت:** P1 | **برآورد:** ~~M~~ → **S/M** | **وضعیت:** 🔴 | **وابستگی:** [A7](07-native-chat-bridge.md) ✅ بسته
- **هم‌ارز در Cursor:** سطح‌های auto-run (خواندن/نوشتن/ترمینال) با یک UX واحد

> ## ⚠️ بازنویسی دامنه ۲۰۲۶-۰۹-۰۸ — نصف این تسک قبلاً انجام شد
>
> صورت‌مسئله‌ی قدیمی («سه مدل مجوز موازی») دیگر درست نیست. تصویر واقعی بعد از
> موج‌های ۱ و ۲:
>
> | مسیر | مجوز امروز | وضعیت |
> |---|---|---|
> | سایدبار Void | `approvalTypeOfBuiltinToolName` + `autoApprove` (`chatThreadService.ts:1018`) | مرجع فعلی |
> | **پل چت بومی** | ✅ **همان map و همان تنظیم** (`f332502e5dc`) | **یکی شد** |
> | Power Mode | `askPermission` جدا (`powerModeProcessor.ts:58`، caller در `:366`) | 🔴 جدا |
> | workflow executor | فقط blocklist رجکسی (`neuralInverse/browser/tools/terminalTools.ts:68` — `BLOCKED_PATTERNS`) | 🔴 ضعیف‌ترین |
> | هسته‌ی VS Code | `languageModelToolsConfirmationService` | مرجع بالقوه |
>
> پس **دو مسیر اصلی از قبل یکی شده‌اند** و کار باقی‌مانده دو چیز است، نه ساختن
> `IPermissionService` از صفر.
>
> ⚠️ ضعیف‌ترین حلقه را دست‌کم نگیر: executor برای `run_command` **هیچ تأییدی**
> نمی‌گیرد و فقط یک blocklist رجکسی دارد. blocklist سیاست امنیتی نیست — هر
> دستوری که الگو را نخورد بی‌پرسش اجرا می‌شود.

## هدف (بازنویسی‌شده)

**۱. تصمیم مرجع.** نقشه‌ی خودمان (`approvalTypeOfBuiltinToolName`) مرجع بماند،
یا به `languageModelToolsConfirmationService` هسته مهاجرت کنیم؟ توصیه: نقشه‌ی
خودمان بماند چون BYOLLM و ابزارهای void را می‌شناسد، ولی **مرزِ اجرا** یکی شود.
این تصمیم قبل از کد نوشته و ثبت شود.

**۲. آوردن دو مسیر باقی‌مانده به همان مرز:** Power Mode و workflow executor.

## وضعیت فعلی در کد
- `void/common/toolsServiceTypes.ts:21` — `approvalTypeOfBuiltinToolName` + دسته‌های
  `autoApprove` در settings
- `neuralInverseAgentConfigService` + `.neuralinverseagent` — tier per-tool + block/allow list
- `powerMode` — `bashSecurity.ts` (پارس فرمان و رتبه‌بندی خطر)
- `neuralInverse/browser/tools/terminalTools.ts` — `runCommand` با blocklist استاتیک،
  بدون تأیید انسانی، timeout پیش‌فرض ۳۰s
- approval gate های workflow (`approvalGate.ts`) — جدا از همه‌ی این‌ها

## طرح پیاده‌سازی
1. **مدل واحد:** `PermissionRequest { tool, args, riskTier, source }` و
   `PermissionDecision { allow | deny | ask }` با سیاست‌های تجمعی:
   workspace config > global settings > پیش‌فرض per-tool
2. **routing:** هر سه مسیر (chat tool loop، autonomy service، NI executor) قبل از
   اجرا از `IPermissionService` می‌پرسند؛ جواب ask → دیالوگ تأیید با
   **پیش‌نمایش** (دیف فایل برای ابزارهای نوشتن؛ فرمان پارس‌شده + مسیرهای درگیر برای ترمینال)
3. **پارس فرمان:** ادغام `bashSecurity.ts` در سرویس مرکزی (رتبه‌ی خطر: خواندن /
   نوشتن / شبکه / مخرب-نما) — blocklist فعلی فقط به‌عنوان آخرین لایه می‌ماند
4. **«همیشه اجازه بده»** در دیالوگ → نوشتن در config (per-tool یا per-pattern مثل
   `npm test*`) — تجربه‌ی Cursor-like
5. **sandbox (phase 2، تسک جدا):** محدودسازی شبکه/فایل در سطح OS — ویندوز: Job Object
   + restricted token؛ در سند معماری تسک ثبت شود ولی در این تسک انجام نشود
6. مهاجرت تدریجی: اول executor (بحرانی‌ترین)، بعد chat، بعد Power Mode

## معیارهای پذیرش
- [ ] `runCommand` در executor برای فرمان خطرناک (مثلاً `rm`) الگو-approved می‌خواهد
- [ ] «همیشه اجازه بده» برای `npm test*` فقط همان الگو را آزاد می‌کند
- [ ] پیش‌نمایش دیالوگ (دیف/فرمان) درست است
- [ ] سه stack بدون تغییر رفتار کاربر فعلی از سرویس جدید استفاده می‌کنند

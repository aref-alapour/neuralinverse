# A3 — چک‌پوینت‌های سطح فایل + Restore (معادل Checkpoints کروسر)

- **اولویت:** P1 | **برآورد:** ~~M~~ → **S/M (فقط اتصال)** | **وضعیت:** 🟡 دو پیاده‌سازی کامل داریم، هیچ‌کدام به چت وصل نیست | **وابستگی:** —
- **هم‌ارز در Cursor:** هر پیام agent یک checkpoint از فایل‌ها؛ دکمه‌ی Restore

> **اصلاح مارکر ۲۰۲۶-۰۹-۰۸ — این تسک «ساختن» نیست، «انتخاب و وصل‌کردن» است.**
> فرض اولیه («فقط checkpoint ایندکسی داریم») غلط بود. الان **دو** پیاده‌سازی
> کاملِ سطح‌فایل در درخت هست:
>
> | منبع | مسیر | مشخصات |
> |---|---|---|
> | **خودمان** (contrib ثبت‌شده‌ی firmware) | `neuralInverseFirmware/browser/engine/projectConfig/checkpointService.ts` | `createCheckpoint`/`rewindTo`/`forkFrom`، دیف git-format + `fileSnapshots` کامل برای rewind امن روی باینری، `.inverse/checkpoints/<id>.json`، سقف ۵۰ با هرس خودکار، ابزار `fw_checkpoint_create` |
> | **upstream ۱.۱۲۷** | `chat/browser/chatEditing/chatEditingCheckpointTimeline.ts` (+`Impl`) و `platform/agentHost/node/agentHostCheckpointService.ts` | timeline با undo/redo، persistence، diff، و نسخه‌ی git-tree برای agent host |
>
> `agentRollbackService.ts` در Void (فقط `messageIndex`) نه سومین پیاده‌سازی، بلکه
> چیزی است که باید **بازنشسته** شود.
>
> ```bash
> grep -n "fw_checkpoint_create" src/vs/workbench/contrib/neuralInverseFirmware/browser/engine/agentTools/firmwareAgentToolService.ts
> grep -n "fileSnapshots\|rewindTo\|forkFrom" src/vs/workbench/contrib/neuralInverseFirmware/browser/engine/projectConfig/checkpointService.ts
> ```
>
> **دامنه‌ی جدید:** (۱) تصمیم بگیر کدام منبع حقیقت است — پیشنهاد: upstream برای
> چت بومی، firmware برای مسیر firmware، و بازنشستگی `agentRollbackService`؛
> (۲) همه‌ی ابزارهای نویسنده‌ی فایل را به ثبت عملیات وصل کن؛ (۳) دکمه‌ی Restore در
> هر پیام؛ (۴) فایل‌های untracked و باینری را در تست پذیرش بیاور.

## هدف
الان rollback فقط «ایندکس پیام» است (`agentRollbackService.ts` — in-memory، بدون
اسنپ‌شات فایل). Cursor برای هر مرحله از کار agent اسنپ‌شات فایل می‌گیرد و کاربر با
یک کلیک به عقب برمی‌گردد — به‌علاوه‌ی thread هم عقب می‌رود. هدف: timeline چک‌پوینت
در UI + restore واقعی فایل‌ها.

## وضعیت فعلی در کد
- `agentRollbackService.ts` — checkpoint ایندکس پیام، بدون محتوا
- `editCodeService.ts` — `VoidFileSnapshot` / DiffArea per-file (پایه‌ی اسنپ‌شات موجود)
- پیام‌های chat: checkpoint دارد (`_addUserCheckpoint`) + rewind که آینده‌ی thread را قطع می‌کند
- `voidSCMService.ts` — هم‌زیستی با git (برای فایل‌های untracked باید فکر شود)

## طرح پیاده‌سازی
1. **استراتژی اسنپ‌شات (phase 1 — ساده و مطمئن):** قبل از هر batch ابزار که فایل را
   تغییر می‌دهد (writeFile/edit از طریق executor یا ابزارهای chat)، محتوای قبلی
   فایل‌های درگیر را در storage ذخیره کن:
   - مخزن: `.inverse/checkpoints/<runId>/<seq>/` — کپی کامل فایل‌های درگیر (فقط همان‌ها)
   - ثبت metadata: `{seq, messageId, files[], timestamp}`
2. **Restore:** بازگرداندن محتوای فایل‌ها + truncate کردن thread به همان پیام (مسیر
   rewind موجود) + اعلان «فایل‌های X, Y بازیابی شدند»
3. **UI:** در `AgentActivityBox` / حباب پیام‌های agent: منوی «…» → «Restore to here»؛
   بین دو checkpoint دیف خلاصه (فایل‌های تغییرکرده)
4. **پاکسازی:** نگهداری حداکثر ۲۰ checkpoint به ازای run؛ حذف کل run → حذف مخزن
5. **Phase 2 (بعداً):** اسنپ‌شات مبتنی بر git (auto-stash به ازای checkpoint) برای
   پشتیبانی از فایل‌های زیاد — جدا تسک می‌شود

## معیارهای پذیرش
- [ ] بعد از ۳ ویرایش فایل توسط agent، Restore به checkpoint اول همه را برمی‌گرداند
- [ ] thread هم‌زمان با فایل‌ها truncate می‌شود
- [ ] فایل untracked هم درست restore می‌شود
- [ ] سقف ۲۰ checkpoint رعایت و قدیمی‌ها پاک می‌شوند

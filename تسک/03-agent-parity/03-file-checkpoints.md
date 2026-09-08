# A3 — چک‌پوینت‌های سطح فایل + Restore (معادل Checkpoints کروسر)

- **اولویت:** P1 | **برآورد:** ~~M~~ → **S/M (فقط اتصال)** | **وضعیت:** 🟡 اجرای موج ۳ (۰۹-۰۸): منبع حقیقت انتخاب و وصل شد؛ پورت live-patch و تست owner باز | **وابستگی:** —
- **هم‌ارز در Cursor:** هر پیام agent یک checkpoint از فایل‌ها؛ دکمه‌ی Restore

> **تصمیم اجرا (موج ۳، ۲۰۲۶-۰۹-۰۸):**
>
> ۱. **منبع حقیقت: `ICheckpointService` فریمور** — اما قبل از اتصال بازنویسی شد،
>    چون پیاده‌سازی قبلی روی `globalThis.require('fs')` تکیه داشت و در رندررِ
>    سندباکس‌شده‌ی VS Code اصلاً اجرا نمی‌شد (`fw_checkpoint_create` در اپ نصبی
>    روی هر فراخوانی throw می‌کرد — همان درس «فایل + ثبت» بدون «سناریوی
>    قابل‌مشاهده»). I/O حالا از `IFileService` می‌گذرد؛ اسنپ‌شات باینری با
>    base64 باینری-امن شد (`checkpointSnapshot.ts` + ۱۰ تست standalone)؛ فایل
>    غایب با `absentFiles` صریح از فایل خالی تفکیک شد (سازگار با JSON قدیمی).
>    `forkFrom` و کشف فایل‌های تغییریافته از git فقط در محیط node کار می‌کنند
>    (best-effort، بدون crash).
> ۲. **یک مرز ثبت، نه دو:** wrapper جدید `withCheckpointing` در `toolsService`
>    کنار `withPlanModeGuard` روی همان executor map. سایدبار و پل چت بومی هر دو
>    از `toolsService.callTool[toolName]` عبور می‌کنند → هفت ابزار نویسنده‌ی
>    فایل (`rewrite_file`, `edit_file`, `multi_replace_file_content`,
>    `create_file_or_folder`, `delete_file_or_folder`, `write`, `edit`) روی هر
>    دو مسیر خودکار checkpoint می‌گیرند. `voidModelProvider` دست نخورد.
>    ترمینال عمداً مستثناست (اثر فایلی غیرمستقیم — به A4/F6 واگذار شد).
> ۳. **Restore:** فرمان پالت `Neural Inverse: Restore Workspace Checkpoint…`
>    (`checkpointRestoreActions.ts`) — QuickPick روی لیست checkpoint ها +
>    `rewindTo` + اعلان نتیجه. تایم‌لاین per-message سایدبار (CheckpointEntry)
>    دست‌نخورده ماند؛ timeline ابستریم هم متعلق به خود edit session های
>    upstream است و تغییر نکرد.
> ۴. **بازنشستگی `agentRollbackService`:** حذف کامل (فایل + ثبت + دو call
>    site در `neuralInverseAgentService`). رویداد `onDidRollback` صفر شنونده
>    داشت و هیچ رفتار قابل‌مشاهده‌ای از دست نرفت.

> **اصلاح مارکر ۲۰۲۶-۰۹-۰۸ — این تسک «ساختن» نیست، «انتخاب و وصل‌کردن» است.**
> فرض اولیه («فقط checkpoint ایندکسی داریم») غلط بود. الان **دو**
> پیاده‌سازی کاملِ سطح‌فایل در درخت هست:
>
> | منبع | مسیر | مشخصات |
> |---|---|---|
> | **خودمان** (contrib ثبت‌شده‌ی firmware) | `neuralInverseFirmware/browser/engine/projectConfig/checkpointService.ts` | `createCheckpoint`/`rewindTo`/`forkFrom`، دیف git-format + `fileSnapshots` کامل برای rewind امن روی باینری، `.inverse/checkpoints/<id>.json`، سقف ۵۰ با هرس خودکار، ابزار `fw_checkpoint_create` |
> | **upstream ۱.۱۲۷** | `chat/browser/chatEditing/chatEditingCheckpointTimeline.ts` (+`Impl`) و `platform/agentHost/node/agentHostCheckpointService.ts` | timeline با undo/redo، persistence، diff، و نسخه‌ی git-tree برای agent host |
>
> `agentRollbackService.ts` در Void (فقط `messageIndex`) نه سومین پیاده‌سازی، بلکه
> چیزی است که باید **بازنشسته** شود. (انجام شد — بالا.)
>
> ```bash
> grep -n "fw_checkpoint_create" src/vs/workbench/contrib/neuralInverseFirmware/browser/engine/agentTools/firmwareAgentToolService.ts
> grep -n "fileSnapshots\|rewindTo\|forkFrom" src/vs/workbench/contrib/neuralInverseFirmware/browser/engine/projectConfig/checkpointService.ts
> ```

## هدف
الان rollback فقط «ایندکس پیام» است (`agentRollbackService.ts` — in-memory، بدون
اسنپ‌شات فایل). Cursor برای هر مرحله از کار agent اسنپ‌شات فایل می‌گیرد و کاربر با
یک کلیک به عقب برمی‌گردد — به‌علاوه‌ی thread هم عقب می‌رود. هدف: timeline چک‌پوینت
در UI + restore واقعی فایل‌ها.

## وضعیت فعلی در کد
- ~~`agentRollbackService.ts` — checkpoint ایندکس پیام، بدون محتوا~~ (حذف شد)
- `editCodeService.ts` — `VoidFileSnapshot` / DiffArea per-file (پایه‌ی اسنپ‌شات موجود؛ تایم‌لاین سایدبار روی همین کار می‌کند)
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
- [x] فایل untracked هم درست restore می‌شود (اسنپ‌شات «غایب» → rewind حذف می‌کند؛ تست standalone)
- [x] سقف ۵۰ checkpoint رعایت و قدیمی‌ها پاک می‌شوند (تست standalone؛ از ۲۰ به ۵۰ سرویس فریمور تغییر کرد)
- [x] فایل باینری byte-to-byte برمی‌گردد (base64 + تست roundtrip)

## مانده برای owner (بعد از پورت live-patch)
- تست زنده: یک نوبت agent که فایل می‌سازد/ویرایش/حذف می‌کند → QuickPick فرمان Restore →
  فایل‌ها به حالت قبل برمی‌گردند؛ فایل باینری و untracked هم در تست باشد.
- تصمیم UX بعدی: دکمه‌ی Restore داخل خود پیام‌ها (به‌جای فرمان پالت) — به UI بومی
- thread-truncate هم‌زمان با rewind فایل‌ها (الان فقط فایل‌ها برمی‌گردند)

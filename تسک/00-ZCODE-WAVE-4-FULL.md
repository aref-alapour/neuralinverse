# پرامپت کامل موج ۴ برای zCode — از تصمیم تا بیلد نصبی

> **این تنها فایلی است که باید بدهی.** خودکفاست: onboarding، تله‌های محیطی،
> قواعد کامیت، دو تسک، و زنجیره‌ی بیلد+نصب در انتها.
> پایه: `3b1ef80c27c`.

---

## بخش ۰ — پرامپت شروع (یک بار، اول session)

```text
سلام. روی پروژه‌ی NeuralInverse کار می‌کنی — fork کد VS Code 1.127 + Void.
workspace: C:/Users/jobal/dev/neuralinverse

قبل از هر کاری این چهار کار را بکن و گزارش بده:
1. `AGENTS.local.md` را کامل بخوان. همه‌ی دروازه‌هایش الزامی است — مخصوصاً:
   بدون تأیید صریح مالک هیچ push/issue/PR، و clean-room.
2. `تسک/README.md` بخش «تعریف قطعی وضعیت» و «چهار شرط انجام‌شده» را بخوان.
3. `تسک/01-memory/00-OWNER-TEST-PROMPTS.md` را بخوان — این موج از نتیجه‌ی
   همان تست‌ها آمده، نه از حدس.
4. `git log --oneline -5` و `git status` بزن و بگو روی چه شاخه‌ای هستی.

── سه تله‌ی این کدبیس ──

الف) «grep چیزی پیدا نکرد» شاهدِ نبودن نیست: نام‌های snake_case؛ وصل‌شدن در
   لایه‌ای غیر از انتظار؛ و import ترانزیتی از باندل‌های .js که
   `grep --include=*.ts` نمی‌بیند.

ب) `npm run typecheck-client` در این فورک **وجود ندارد**. دستور درست:
   NODE_OPTIONS="--max-old-space-size=8192" npx tsc -p src/tsconfig.json --noEmit
   با هیپ پیش‌فرض ۴GB به OOM می‌خورد (خروج ۱۳۴).

ج) `node build/eslint.ts <file>` آرگومان را نادیده می‌گیرد و کل ریپو را lint
   می‌کند (>۱۰ دقیقه). برای یک فایل: `npx eslint <file>`.

── قواعد کد ──
تب؛ بدون `any`؛ import تکراری ممنوع؛ disposable ها بلافاصله register شوند؛
رشته‌های کاربر با `nls.localize`؛ هدر کپی‌رایت Neural Inverse روی فایل جدید.

── قاعده‌ی کامیت ──
هوک hygiene هشدارهای eslint را fatal می‌شمارد، و **جدا از eslint** فرمت و
indentation را هم چک می‌کند. `--no-verify` ممنوع است مگر با تأیید صریح مالک.
اگر فایلی بدهی لینت دارد: اول کامیت جدای `chore(lint):` (بدون تغییر رفتاری)،
بعد کامیت feature. اگر hygiene از «File not formatted» شکایت کرد:

  node --experimental-strip-types -e "
  import('./build/lib/formatter.ts').then(async f=>{
    const fs=await import('fs'); const p='<path>';
    const raw=fs.readFileSync(p,'utf8'); const out=f.format(p,raw);
    if(out!==raw) fs.writeFileSync(p,out);});"

حالا فقط گزارش بده و منتظر بمان.
```

## بخش ۱ — چک‌لیست پایان هر تسک

```text
قبل از اینکه بگویی تمام شد:
1. NODE_OPTIONS="--max-old-space-size=8192" npx tsc -p src/tsconfig.json --noEmit
2. npx eslint <هر فایلی که عوض کردی>  → طبق قاعده‌ی کامیت بپرداز
3. node tools/verify.mjs   (باید ۱۴۱ تست سبز بماند یا بیشتر شود)
4. چهار شرط «انجام شده» را صریح جواب بده:
   فایل ✔ / ثبت ✔ / caller واقعی ✔ / سناریوی قابل‌مشاهده ✔
   اگر یکی جواب ندارد، تسک 🟡 است نه ✅. بگو کدام باز است.
5. کامیت با پیام انگلیسی روشن. push نکن.
6. مارکر فایل تسک را به‌روز کن.

و: **هر تسک با یک دستور اثبات شروع می‌شود.** اگر تحلیل با کد نخواند، اول بگو —
سه بار تا حالا تحلیل غلط بوده، نه کد.
```

---

## آنچه از قبل رفع شد (دست نزن)

- باگ journaling لجر (`881c6ad42c2`) — نتیجه‌ی ابزار به‌جای placeholder ثبت می‌شود
- بدهی لینت `chatThreadService` (`9e4ea745916`، ۹۴۴ → ۰) — این فایل حالا تمیز است

---

## تسک ۱ — M7: یکی‌کردن دو سیستم حافظه ⭐ اول این

```text
تسک: تسک/01-memory/07-memory-systems-split.md را کامل بخوان.

این از تست زنده آمده. شکست مشاهده‌شده: مالک گفت «همیشه pnpm استفاده کن»، مدل
تأیید کرد ذخیره شد، بعد در چت جدید پرسید «پکیج منیجر رو عوض نکن — چرا؟» و مدل
رفت lockfile خواند و گفت «چون npm دارد» — خلافِ چیزی که ذخیره شده بود. و وقتی
پرسید «بخش Agent Memory در system prompt ات را نشان بده» گفت چنین بخشی نیست.

اثبات کن اول:
  ls ~/Desktop/escapezoom-html/.void-memory/     # حافظه اینجا نشست
  grep -n "memory_write" src/vs/workbench/contrib/void/browser/toolsService.ts
  grep -rn "agentMemoryService" src --include=*.ts | grep -v agentMemoryService.ts

خواهی دید memory_write در فایل می‌نویسد (.void-memory/<key>.md) و
agentMemoryService — موتور hybrid که کل M2 رویش ساخته شد — هیچ ابزاری برای
نوشتن ندارد. پس M2 از اول روی حافظه‌ی خالی کار می‌کرده.

**اول تصمیم را بنویس و از من تأیید بگیر. کد ننویس تا تأیید نگرفته‌ای** — این
تصمیم معماری است نه انتخاب پیاده‌سازی. سه گزینه در فایل تسک؛ توصیه گزینه‌ی الف
(agentMemoryService مرجع شود، چون تنها این یکی بازیابی معنایی دارد).

بعد از تأیید:
1. مدل ابزاری داشته باشد که در موتور M2 بنویسد.
2. `.void-memory/*.md` موجود از دست نرود — مهاجرت یا خواندن سازگاری عقب‌رو.
3. اگر هر دو ماندند، توضیح ابزار روشن کند کِی کدام صدا زده شود.

معیار پذیرش = تست ۲ از تسک/01-memory/00-OWNER-TEST-PROMPTS.md سبز شود:
ذخیره با یک جمله، پرسش در چت جدید با واژگان بی‌اشتراک، دیدن
`(matched: vector:0.xx)` در بلوک `Agent Memory`. تا جایی که می‌شود با تست
خودکار پوشش بده؛ بخش تعاملی برای مالک می‌ماند.
```

---

## تسک ۲ — A8: دو شکاف پاریتی چت بومی

> موازی با M7 قابل اجراست (فایل مشترک ندارند)، ولی **معیار پذیرش بند ۲ به M7
> وابسته است** — پس اگر یک session داری، بعد از M7.

```text
تسک: تسک/03-agent-parity/08-native-chat-parity-gaps.md را بخوان.

دو شکاف، هر دو در تست زنده دیده شدند:

۱. حافظه‌ی hybrid به چت بومی نمی‌رسد.
   generateSystemMessage (convertToLLMMessageService.ts:899) نسخه‌ی همگام
   getContextSummary() را صدا می‌زند؛ نسخه‌ی async که M2 ساخت فقط در
   prepareLLMChatMessages (:1015، مسیر سایدبار) استفاده می‌شود.

۲. ابزارهای recall لجر در چت بومی نیستند.
   مدل در تست سه بار گفت «recall_history در دسترس نیست». ledgerRecallContrib
   ثبتشان می‌کند ولی به فهرستی که voidModelProvider به مدل می‌دهد نمی‌رسند.
   یعنی ژورنال M5 پر می‌شود و از سطح اصلی محصول خوانده نمی‌شود.

اثبات کن اول:
  grep -n "getContextSummary" src/vs/workbench/contrib/void/browser/convertToLLMMessageService.ts
  grep -n "recall_history" src/vs/workbench/contrib/void/browser/ledgerRecallContrib.ts
  grep -n "copilotMcpTools\|getTools" src/vs/workbench/contrib/void/browser/voidModelProvider.ts

**مهم‌ترین بند، بند ۳ معیار پذیرش است — تست پاریتی.** دو رفع نقطه‌ای کافی نیست:
این سومین بار است که همین الگو تکرار می‌شود (E1 در موج ۳، و حالا این دو). پل
پیام سیستمی و فهرست ابزار جدای خودش را می‌سازد، پس هرچه فقط در سایدبار وصل شود
بی‌صدا غایب می‌ماند.

یک تست بنویس که هر قابلیتی را که سایدبار دارد و پل ندارد قرمز کند. الگویش تست
پاریتی Q12 است (تسک/05-quality/12-desktop-usage-parity.md) که برای شکاف
web/desktop نوشته شد و جواب داد. بدون آن گیت، شکاف چهارم هم با تست دستی مالک
پیدا می‌شود، ماه‌ها بعد.
```

---

## بخش ۳ — بیلد و نصب (بعد از سبزشدن هر دو تسک)

> این زنجیره یک بار کامل اجرا و راستی‌آزمایی شده ([Q14](05-quality/14-win32-packaging-broken.md)).
> چهار پیش‌نیاز CI که قبلاً می‌شکستند حالا شرطی‌اند.

```text
هر دو تسک سبز شد؟ حالا بسته‌ی نصبی بساز:

export VSCODE_SKIP_NODE_VERSION_CHECK=1 PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

npm run compile                                   # ~7 دقیقه، باید exit 0 و صفر خطای TS
npm run gulp vscode-win32-x64                     # ~20 دقیقه
npm run gulp vscode-win32-x64-inno-updater        # چند ثانیه — قبل از setup لازم است
npm run gulp vscode-win32-x64-system-setup        # ~2 دقیقه

خروجی: .build/win32-x64/system-setup/VSCodeSetup.exe

بعد تأیید کن که بسته درست است:
  node -e "const p=require('../VSCode-win32-x64/resources/app/product.json'),
    k=require('../VSCode-win32-x64/resources/app/package.json');
    console.log(k.version, p.commit)"

باید نسخه 1.127.0 و commit برابر HEAD باشد.

دو هشدار در لاگ **طبیعی‌اند و شکست نیستند**:
- «signtool.exe not found» — امضای Authenticode فقط روی ماشین با Windows SDK
- «appx/code_x64.appx not found» — منوی راست‌کلیک ویندوز، نیازمند MSIX tooling

**نصب را خودت انجام نده.** مسیر فایل را به مالک بده؛ نصب نیاز به بستن ادیتور و
تأیید UAC دارد.
```

---

## بخش ۴ — دست نزن

| مورد | چرا |
|---|---|
| `product.json` | کامیت‌نشده و گیت hygiene ردش می‌کند چون `extensionsGallery` به مارکت‌پلیس مایکروسافت اشاره دارد — تصمیم باز مالک |
| `.claude/` | untracked، تصمیم مالک |
| **Q9** (TLS) | کار محیطی مالک |
| **A1، A6** | تا تصمیم [Q13](05-quality/13-contribution-registration-gate.md) روی کد ثبت‌نشده کار می‌کنند |
| **G0–G9** | تصمیم محصولی مستقل |

## بخش ۵ — بعد از این موج

با سبزشدن M7 و A8، هر سه تست owner دوباره اجرا می‌شوند. اگر سبز بمانند
M1/M2/M5 از 🟡 به ✅ می‌روند و دسته‌ی حافظه می‌شود **۴ ✅ / ۰ 🟡 / ۲ 🔴**.

بیشترین بازده بعدی در کل بک‌لاگ **M3** است (ثبت خودکار حافظه از دل گفتگو) —
که پیش‌نیازش تازه با بسته‌شدن M7 واقعاً آماده می‌شود.

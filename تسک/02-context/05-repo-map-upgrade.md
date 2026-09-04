# C5 — ارتقای نقشه‌ی ریپو (Repo Map هوشمند به سبک Aider/Cursor)

- **اولویت:** P1 | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** C1
- **هم‌ارز در Cursor:** درک ساختار پروژه بدون باز کردن همه‌ی فایل‌ها

## هدف
نقشه‌ی فعلی (درخت دایرکتوری ساده با سقف ۲۰k کاراکتر در `directoryStrService.ts`) به
نقشه‌ی **رتبه‌بندی‌شده با اهمیت** ارتقا یابد: فایل‌های مهم‌تر (پرارجاع‌تر در import graph،
پرتغییرتر اخیراً) نمایش داده شوند + امضای symbol های کلیدی فایل‌های top؛ بودجه بر اساس
feature (autocomplete کم، agent زیاد).

## چرا مهم است
مدل با نقشه‌ی درست، فایل درست را خودش پیدا می‌کند و ابزار read کمتری مصرف می‌کند —
یعنی توکن کمتر، سرعت بیشتر، خطای مسیر کمتر. Aider ثابت کرده این تک‌قابلیت کیفیت
agent را به‌شدت بالا می‌برد.

## وضعیت فعلی در کد
- `src/vs/workbench/contrib/void/common/directoryStrService.ts` — درخت مسطح، سقف
  ۲۰k کاراکتر / ۱۰۰ نتیجه، بدون رتبه‌بندی
- `neuralInverse/browser/context/graph/dependencyGraph.ts` — گراف import موجود
- `tracker/changeTracker.ts` — حرارت ویرایش‌های اخیر موجود
- `input/astContextService.ts` + `index/workspaceSymbolIndex.ts` — استخراج امضا ممکن است

## طرح پیاده‌سازی
1. **امتیاز فایل:** `score = 0.5·centrality(dependencyGraph) + 0.3·editHeat(changeTracker)
   + 0.2·recency` — محاسبه‌ی دوره‌ای (روی تغییر ساختاری)، کش per-workspace
2. **فرمت نقشه:** درخت فشرده به سبک Aider:
   ```
   src/
     core/
       engine.ts        (class Engine, fn run, fn stop)   ★ import:42 | edits:11
       config.ts        (interface Config)                ★ edits:3
   ```
   — فقط فایل‌های بالای آستانه‌ی بودجه، به ترتیب امتیاز؛ امضاها از AST
3. **بودجه‌ی per-mode:** autocomplete: 2k / chat: 8k / agent: 16k توکن (قابل تنظیم
   از `contextBudgets` مرکزی که در C1 ساخته می‌شود)
4. **invalidation:** بازسازی کش روی رویدادهای ساختاری (فایل جدید/حذف/تغییر import)؛
   debounce 5s
5. گزینه‌ی تنظیم «repo map در پیام سیستم باشد یا به‌عنوان tool result اول» (برای
   مدل‌هایی که system بلند را بد می‌فهمند)

## معیارهای پذیرش
- [ ] روی این repo خودمان: نقشه، فایل‌های پرارجاع را با امضا نشان می‌دهد
- [ ] بودجه رعایت می‌شود (طول رشته ≤ بودجه × 4 کاراکتر)
- [ ] تغییر ساختاری (فایل جدید) طی < 10s در نقشه می‌آید
- [ ] در حالت autocomplete هیچ افت سرعتی حس نمی‌شود (از کش)

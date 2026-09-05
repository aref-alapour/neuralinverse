# G9 — Track B: اجرای خود ComfyUI به‌عنوان سرویس لوکال (اختیاری)

> ⚖️ **قانون clean-room (2۲۰۲۶-۰۹-۰۵):** این تسک فقط ایدهٔ طراحی از منبع را میگیرد — هیچ کدی عیناً/نزدیک‌به-عیناً کپی یا ترجمه نمی‌شود؛ پیاده‌سازی از صفر با معماری خودمان (بخش «⚖️ قانون لایسنس» در README این پوشه). هر جا میگوید «پورت کن»، یعنی «طرح را بفهم و native پیاده کن».

- **اولویت:** P2 (مستقل — تصمیم جداگانه‌ی محصول) | **برآورد:** M | **وضعیت:** 🔴 | **وابستگی:** — (از Track A مستقل است؛ با G1 ترکیب‌پذیر)
- **منبع:** `script_examples/basic_api_example.py` + `websockets_api_example.py` + `websockets_api_example_ws_images.py` (سومین فایل — از قلم‌افتاده‌ی handoff)

## هدف
بدون هیچ پورتی: ComfyUI به‌عنوان سرویس مدیریت‌شده‌ی لوکال کنار ادیتور برای تولید
تصویر/ویدیو (مثلاً آیکون‌سازی، mock asset، thumbnail، داکیومنت تصویری).

## کارها
1. **مدیریت پروسه:** spawn `python main.py --port <p> --disable-all-custom-nodes` از
   سرویس سمت extension-host (Desktop)؛ تشخیص/نصب Python در UX (الگوی local-provider
   auto-setup ما در modelManagement از قبل مشابه‌اش را دارد!)
2. **handshake سلامت/نسخه:** `GET /system_stats` (شامل `required_frontend_version` —
   چک drift نسخه)
3. **درایو API:** `POST /prompt` (صف گراف — **دقیقاً همان JSON فرمت Track A/G1**)،
   `GET /ws?clientId=` (رویدادها — همان نام‌های G6!)، `GET /object_info` (پالت
   بومی در canvas از کاتالوگ خود ComfyUI)، `POST /interrupt`، `GET /history/{id}`،
   `POST /upload/image`، `GET /view?filename=`
4. **همبستگی clientId** و بازیابی artifact ها داخل ادیتور (image preview در artifact pane)
5. **نمایش خطاها** در همان ساختار NodeErrors (خطاهای validation خود ComfyUI همان shape است)

## ترکیب Track A + B (نکته‌ی طراحی handoff — تأیید می‌شود)
موتور G1-G7 ما نودهای agent/workflow را بومی اجرا می‌کند و **زیرگراف تولید محتوا
را به‌صورت یک نود «ComfyUI Subgraph» به سرویس embed شده می‌سپارد** — خروجی از API
برمی‌گردد و مثل خروجی هر نود دیگری وارد dataflow/کش می‌شود (async node با external
block در G3 — دقیقاً همین کار build شده است).

## نکات
- اجرای فقط local؛ هیچ فرض شبکه‌ای
- آپدیت ComfyUI با ری‌استارت سرویس (clone جدا در `C:\Users\jobal\dev\comfyui` —
  نیازی به bundle داخل repo نیست)
- اگر پوشش تصویری لازم شد ولی Track A هنوز آماده نبود: این تسک به‌تنهایی قابل
  شروع است (فقط HTTP client + مدیریت پروسه)

## معیارهای پذیرش
- [ ] سرویس از داخل ادیتور بالا/پایین می‌آید (health سبز)
- [ ] گراف نمونه از editor صف می‌شود، رویدادها در UI می‌آیند، تصویر خروجی ذخیره و
      preview می‌شود
- [ ] drift نسخه → هشدار روشن قبل از ارسال گراف
- [ ] (بعد از G3) نود «ComfyUI Subgraph» به‌صورت async کار می‌کند و خروجی وارد کش می‌شود

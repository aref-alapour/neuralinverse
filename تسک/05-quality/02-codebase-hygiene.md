# Q2 — بهداشت کدبیس (Hygiene)

- **اولویت:** P0 | **برآورد:** S | **وضعیت:** 🔴 | **وابستگی:** —
- **هم‌ارز در Cursor:** هیچ — این تسک کیفیت داخلی است ولی برای «حرفه‌ای بودن» ضروری است

## هدف
پاک‌سازی چیزهایی که کدبیس را غیرحرفه‌ای نشان می‌دهند و ریسک می‌سازند.

## فهرست کارها
1. **فایل‌های `.bak` داخل repo** (حذف از git، در صورت نیاز نگهداری محلی + gitignore):
   - `src/vs/workbench/contrib/void/browser/chatThreadService.ts.bak`
   - `src/vs/workbench/contrib/void/browser/chatThreadService.ts.bak2`
   - `src/vs/workbench/contrib/void/browser/chatThreadService.ts.bak3`
   - `react/src/sidebar-tsx/AgentNetworkViz.tsx.bak` (مسیر دقیق را با glob چک کن)
   - `powerModeTerminalHost.ts.bak*`
2. **فایل مرده:** `void/neuralInverse/browser/backgroundAgentService.js` (js خام کنار ts)
3. **جلوگیری از تکرار:** الگوی `*.bak*` به `.gitignore` + یک pre-commit check ساده
   (یا حداقل خط در `AGENTS.local.md`)
4. **مرور TODO های بحرانی:**
   - قیمت‌ها/پنجره‌های context با `TODO!!! double check` در `modelCapabilities.ts`
     (فهرست به Q1 وصل است)
   - `getSessionCost()` (با Q1 بسته می‌شود)
   - autocomplete context TODO در `chatThreadService.ts:551`
5. ~~**بررسی live-patch marker ها**~~ → منتقل شد و کامل اجرا شد در
   [Q4 — یکپارچگی live-patch](04-live-patch-integrity.md) (ابزار `--verify`
   + `--status` + `--rebaseline` + manifest + selftest sandbox؛ ۲۰۲۶-۰۹-۰۵
   سبز). اینجا فقط مرجع می‌ماند؛ هر کاری در آن تسک انجام می‌شود.

## معیارهای پذیرش
- [ ] `git ls-files | grep -E '\.bak'` خالی است
- [ ] فایل js مرده حذف شده و هیچ import ای نشکسته
- [ ] `python tools/live-patch.py --verify` خروجی سبز/قرمز واضح می‌دهد
- [ ] فهرست TODO های باز در یک فایل `تسک/05-quality/tech-debt.md` جمع شده

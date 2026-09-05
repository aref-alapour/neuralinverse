# Upstream issue draft — @clude/sdk (io.github.sebbsssss/clude)

> وضعیت: پیش‌نویس محلی. طبق گیت همکاری (AGENTS.local.md بند ۱) چیزی منتشر
> نمی‌شود تا OK خودتان. متن انگلیسی آماده‌ی کپی در github issue است.

## Title

`list_memories` MCP tool is broken in hosted mode — calls `GET /api/cortex/memories`, which the hosted backend does not serve (404)

## Body

### Problem

On `@clude/sdk` **3.4.0** in hosted mode (`mcp-serve` with `CORTEX_API_KEY`), the
`list_memories` MCP tool always fails:

```
Cortex API error 404: <!DOCTYPE html> … Cannot GET /api/cortex/memories
```

Every other tool on the same server works against the same account
(`recall_memories`, `get_memory_stats`, `store_memory`, `update_memory`, …).

### Root cause

The MCP server's hosted branch builds the request itself:

```js
// dist/mcp/server.js (list_memories, hosted branch)
result = await cortexFetch("GET", `/api/cortex/memories?${params}`);
```

but the hosted backend has no such route. Notably, the SDK's own hosted client
class (`dist/sdk/index.js`) has **no `list()` method at all** — only
`recent(hours, types, limit)` → `GET /api/cortex/recent`. So the MCP tool's
hosted branch references an endpoint the SDK itself never shipped a client for.

Verified directly against the backend with the same API key:

- `GET /api/cortex/memories` → **404** (Express-style "Cannot GET")
- `GET /api/cortex/recent?hours=…&limit=…` → **200** (capped at 100 items;
  `offset`/`page` query params are ignored — no server-side pagination)
- `GET /api/cortex/stats` → **200**

### Impact

Any hosted-mode user who calls `list_memories` gets a hard error. Agents that
browse memories (no search query) cannot.

### Suggested fix (one of)

1. Serve `GET /api/cortex/memories` on the hosted backend with
   `page`/`page_size`/`memory_type`/`min_importance`/`order` support, or
2. Point the MCP tool's hosted branch at the existing `/api/cortex/recent`
   (and add server-side pagination there), or
3. At minimum: make `/api/cortex/recent` honor `offset` so the client can
   emulate paging.

### Workaround we deployed locally

Patched the two dist bundles to fall back to `/api/cortex/recent?hours=26280&limit=100`
on 404, with client-side filter/sort/pagination over the returned window, and a
`note` field on the result telling the caller that browsing is limited to the
newest 100 memories while the route is missing. Happy to turn it into a PR if
approach (2) sounds right.

Environment: Windows, Node 25, `@clude/sdk@3.4.0`, hosted mode, server reports
`{ name: 'clude-memory', version: '3.4.0' }`, 611 stored memories.

---

# گزارش داخلی — رفع ابزارهای خراب ادیتور (۲۰۲۶-۰۹-۰۵)

## خلاصه‌ی سه‌گانه

| ابزار | تشخیص واقعی | اقدام | وضعیت |
|---|---|---|---|
| `list_memories` | SDK 3.4.0 به روت `_api/cortex/memories_` می‌زند که بک‌اند clude.io آن را پیاده نکرده (۴۰۴) — کلاینت خود SDK هم متد list ندارد | پچ محلی دو باندل dist با فال‌بک `_recent_` + فیلتر/مرتب‌سازی/صفحه‌بندی کلاینت + فیلد note | ✅ تأیید سرتاسری سبز |
| `recall_memories` | **خراب نبود** — با MCP مستقیم سالم جواب می‌دهد؛ «همیشه fail» گزارش‌شده محصول `{}` بود | نیازی به اقدام نبود | ✅ |
| `browser_console_messages` | سرور playwright با `@latest` هر بار resolve می‌شود و پشت proxy بسته هرگز بالا نمی‌آید (بازتولید شد: پین‌شده در ثانیه‌ها جواب داد، `latest` در ۶۰+ ثانیه هیچ). فرضیه‌ی `filename:""` رد شد — ابزار با `""` سالم کار می‌کند | پین `_@playwright/mcp@0.0.80_` در `~/.neural-inverse/mcp.json` (بکاپ: `mcp.json.ni-backup`) | ✅ handshake تأیید شد |

## باگ مشترک که همه را پنهان کرده بود

`Failed to call tool "X" on server "Y": {}` — در کد خود ما بود:
`mcpChannel._safeCallTool` روی Error ساده `JSON.stringify(err)` می‌زد که همیشه
`{}` است. رفع در سورس + پورت live-patch (کامیت `bf3e21ed`). از این بعد پیام
واقعی هر خطای ابزار در چت دیده می‌شود.

## کارهای باقی برای شما (مالک)

1. **اجرای Repatch NeuralInverse.bat (elevated)** — پچ جدید
   «mcp: surface real Error messages» الان روی نصب PENDING است
   (`30 OK, 1 PENDING`)؛ بعدش `python tools/live-patch.py --verify` باید
   ۳۱ OK بدهد.
2. **ری‌استارت ادیتور** تا هم پچ اصلی و هم mcp.json پین‌شده لود شود.
3. تأیید متن issue بالا برای فرستادن به آپ‌استریم clude (گیت همکاری).

## نکات

- پچ SDK داخل `node_modules` است — با آپدیت بعدی پکیج از می‌رود؛ متن issue
  راه‌حل بالادستی است. بکاپ‌ها: `*.ni-patch.orig`.
- محدودیت صادقانه‌ی فال‌بک: مرور لیست به ۱۰۰ خاطره‌ی جدیدتر محدود است تا
  وقتی بک‌اند روت صفحه‌بندی داشته باشد (در فیلد note به agent صداکننده
  اعلام می‌شود).

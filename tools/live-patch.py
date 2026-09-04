#!/usr/bin/env python3
"""Live-patch the installed NeuralInverse IDE with our source-level fixes.

Applies the same fixes we PR upstream, but directly to the minified
bundles of the installed app, so we can test without a full VS Code
build. Run from an elevated (admin) shell.

Usage:
    python tools/live-patch.py            # apply all patches
    python tools/live-patch.py --revert   # restore the original bundles

Safety: backs up each pristine file once to <file>.orig. A patch whose
pattern is missing is reported (may mean upstream already fixed it, or the
app updated and patterns changed) — nothing else is modified.
"""
import json
import shutil
import sys
import urllib.request
from pathlib import Path

APP = Path(r"C:\Program Files\NeuralInverse\resources\app")
BUNDLE = APP / "out/vs/workbench/workbench.desktop.main.js"
MAINJS = APP / "out/main.js"
PRODUCT_JSON = APP / "product.json"

UPDATE_API = ("https://tcnnnsytzd.execute-api.us-east-1.amazonaws.com"
              "/api/update/win32-x64/stable/0000000000000000000000000000000000000000")

# Each patch: (file, name, old_minified_snippet, replacement)
# Keep snippets exactly as they appear in the minified bundles.
PATCHES = [
    # ── fix/agent-resolution-by-id (PR #134 / issue #133) ──────────────────
    (BUNDLE,
     "agent-map-by-id (runWorkflow): slug(name) key -> id key",
     'new Map(this.agentStore.getAgents().map(g=>[g.name.toLowerCase().replace(/\\s+/g,"-"),g]',
     'new Map(this.agentStore.getAgents().map(g=>[g.id,g]'),
    (BUNDLE,
     "agent-map-by-id (runAgent fallback): raw name key -> id key",
     'new Map(this.agentStore.getAgents().map(p=>[p.name,p])',
     'new Map(this.agentStore.getAgents().map(p=>[p.id,p])'),
    # ── feat/agent-conversation-memory (task 1: agent forgets conversation) ──
    (BUNDLE,
     "agent-conversation-memory: runAgent loads/appends conversation",
     'try{await this._orchestrator.run(n,s,a,h,t,o,p=>this._onDidChangeRun.fire(p))}catch(p){s.status="failed",s.error=p.message,s.endedAt=Date.now()}return this._finalizeRun(s),s})}',
     'try{globalThis.__niAdhocConv=(globalThis.__niConv??(globalThis.__niConv=new Map)).get(e)||[],await this._orchestrator.run(n,s,a,h,t,o,p=>this._onDidChangeRun.fire(p))}catch(p){s.status="failed",s.error=p.message,s.endedAt=Date.now()}finally{delete globalThis.__niAdhocConv}'
     'if(s.status==="done"&&s.finalOutput){const w=globalThis.__niConv,y=w.get(e)||[];y.push({role:"user",content:t},{role:"assistant",content:s.finalOutput}),y.length>24&&y.splice(0,y.length-24),w.set(e,y)}'
     'return this._finalizeRun(s),s})}'),
    (BUNDLE,
     "agent-conversation-memory: orchestrator forwards conversation",
     '.execute(y,i,v,S,x,E,a)',
     '.execute(y,i,v,S,x,E,a,globalThis.__niAdhocConv||[])'),
    (BUNDLE,
     "agent-conversation-memory: executor seeds history",
     'for(d.push({role:"system",content:v}),d.push({role:"user",content:o}),',
     'for(d.push({role:"system",content:v}),d.push(...(arguments[7]||[])),d.push({role:"user",content:o}),'),
    # ── fix: no Void-layer tools in executor LLM calls (double tool catalog) ──
    (BUNDLE,
     "executor chatMode null: stop injecting Void/MCP tools into agent runs",
     'chatMode:"agent",onText',
     'chatMode:null,onText'),
    # ── fix(updater): endless update banner (server ignores commit) ─────────
    # Their update API returns the latest release for ANY commit hash, so the
    # client offers (and re-offers forever) the already-installed version.
    # Skip an update whose version equals the installed product.json version.
    # Pairs with the version stamping below.
    (MAINJS,
     "updater: skip update whose version matches installed version",
     'return!i||!i.url||!i.version||!i.productVersion?(this.setState(_e.Idle(s)),Promise.resolve(null)):s===1?(',
     'return!i||!i.url||!i.version||!i.productVersion||i.version===this.productService.version?(this.setState(_e.Idle(s)),Promise.resolve(null)):s===1?('),
]


def latest_release_version() -> str | None:
    try:
        with urllib.request.urlopen(UPDATE_API, timeout=15) as r:
            return json.loads(r.read().decode()).get("version")
    except Exception as e:
        print(f"WARN  update API unreachable: {e}")
        return None


def backup_once(f: Path) -> None:
    b = f.with_suffix(f.suffix + ".orig")
    if not b.exists():
        shutil.copy2(f, b)
        print(f"Backup saved: {b.name}")


def patch_product_json() -> None:
    # 1) Drop checksums: patched bundles fail VS Code's core-file integrity
    #    check ("installation appears to be corrupt" dialog).
    # 2) Stamp the marketing version from their update API onto `version`:
    #    their builds never bump it (stays at the VS Code base), which —
    #    together with the updater guard patch — is what stops the endless
    #    "X is available" banner after installing the latest build.
    if not PRODUCT_JSON.exists():
        return
    pdata = json.loads(PRODUCT_JSON.read_text(encoding="utf-8-sig"))
    changed = []
    if "checksums" in pdata:
        del pdata["checksums"]
        changed.append("checksums removed")
    latest = latest_release_version()
    if latest and pdata.get("version") != latest:
        pdata["version"] = latest
        changed.append(f"version stamped {latest}")
    if changed:
        backup_once(PRODUCT_JSON)
        PRODUCT_JSON.write_text(
            json.dumps(pdata, indent="\t", ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"OK    product.json: {'; '.join(changed)}")
    else:
        print("SKIP  product.json: nothing to do")


def main() -> int:
    revert = "--revert" in sys.argv
    if revert:
        for f in (BUNDLE, MAINJS, PRODUCT_JSON):
            b = f.with_suffix(f.suffix + ".orig")
            if b.exists():
                shutil.copy2(b, f)
                print(f"Reverted {f.name}")
        return 0

    files = {p[0] for p in PATCHES}
    for f in files:
        if not f.exists():
            print(f"ERROR: file not found: {f}")
            return 1
        backup_once(f)

    patch_product_json()

    for f, name, old, new in PATCHES:
        data = f.read_text(encoding="utf-8")
        count = data.count(old)
        if count == 0:
            already = data.count(new)
            print(f"SKIP  {name}: pattern not found"
                  + (" (already applied)" if already else ""))
            continue
        f.write_text(data.replace(old, new), encoding="utf-8", newline="")
        print(f"OK    {name}: {count} site(s) patched")

    print("Done. Restart NeuralInverse to load the patches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

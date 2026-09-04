#!/usr/bin/env python3
"""Live-patch the installed NeuralInverse IDE with our source-level fixes.

Applies the same fixes we PR upstream, but directly to the minified
workbench bundle of the installed app, so we can test without a full
VS Code build. Run from an elevated (admin) shell.

Usage:
    python tools/live-patch.py            # apply all patches
    python tools/live-patch.py --revert   # restore the original bundle

Safety: backs up the pristine bundle once to <bundle>.orig. A patch whose
pattern is missing is reported (may mean upstream already fixed it, or the
app updated and patterns changed) — nothing else is modified.
"""
import shutil
import sys
from pathlib import Path

BUNDLE = Path(r"C:\Program Files\NeuralInverse\resources\app\out\vs\workbench\workbench.desktop.main.js")
PRODUCT_JSON = Path(r"C:\Program Files\NeuralInverse\resources\app\product.json")

# Each patch: (name, old_minified_snippet, replacement)
# Keep snippets exactly as they appear in the minified bundle.
PATCHES = [
    (
        "agent-map-by-id (runWorkflow): slug(name) key -> id key",
        'new Map(this.agentStore.getAgents().map(g=>[g.name.toLowerCase().replace(/\\s+/g,"-"),g]',
        'new Map(this.agentStore.getAgents().map(g=>[g.id,g]',
    ),
    (
        "agent-map-by-id (runAgent fallback): raw name key -> id key",
        'new Map(this.agentStore.getAgents().map(p=>[p.name,p])',
        'new Map(this.agentStore.getAgents().map(p=>[p.id,p])',
    ),
    # ── feat/agent-conversation-memory (task 1: agent forgets conversation) ──
    # A) runAgent: load stored conversation, stash for the executor, append
    #    user+assistant turn after a successful run (cap 24 messages).
    (
        "agent-conversation-memory: runAgent loads/appends conversation",
        'try{await this._orchestrator.run(n,s,a,h,t,o,p=>this._onDidChangeRun.fire(p))}catch(p){s.status="failed",s.error=p.message,s.endedAt=Date.now()}return this._finalizeRun(s),s})}',
        'try{globalThis.__niAdhocConv=(globalThis.__niConv??(globalThis.__niConv=new Map)).get(e)||[],await this._orchestrator.run(n,s,a,h,t,o,p=>this._onDidChangeRun.fire(p))}catch(p){s.status="failed",s.error=p.message,s.endedAt=Date.now()}finally{delete globalThis.__niAdhocConv}'
        'if(s.status==="done"&&s.finalOutput){const w=globalThis.__niConv,y=w.get(e)||[];y.push({role:"user",content:t},{role:"assistant",content:s.finalOutput}),y.length>24&&y.splice(0,y.length-24),w.set(e,y)}'
        'return this._finalizeRun(s),s})}',
    ),
    # B) orchestrator: forward the stashed ad-hoc conversation to the executor.
    (
        "agent-conversation-memory: orchestrator forwards conversation",
        '.execute(y,i,v,S,x,E,a)',
        '.execute(y,i,v,S,x,E,a,globalThis.__niAdhocConv||[])',
    ),
    # C) executor: seed history with the prior conversation (8th arg).
    (
        "agent-conversation-memory: executor seeds history",
        'for(d.push({role:"system",content:v}),d.push({role:"user",content:o}),',
        'for(d.push({role:"system",content:v}),d.push(...(arguments[7]||[])),d.push({role:"user",content:o}),',
    ),
    # ── fix: no Void-layer tools in executor LLM calls (double tool catalog) ──
    (
        "executor chatMode null: stop injecting Void/MCP tools into agent runs",
        'chatMode:"agent",onText',
        'chatMode:null,onText',
    ),
]


def main() -> int:
    revert = "--revert" in sys.argv
    if not BUNDLE.exists():
        print(f"ERROR: bundle not found: {BUNDLE}")
        return 1
    backup = BUNDLE.with_suffix(BUNDLE.suffix + ".orig")

    if revert:
        if not backup.exists():
            print("ERROR: no .orig backup to restore")
            return 1
        shutil.copy2(backup, BUNDLE)
        pbackup = PRODUCT_JSON.with_suffix(".json.orig")
        if pbackup.exists():
            shutil.copy2(pbackup, PRODUCT_JSON)
            print("Reverted product.json (checksums restored).")
        print("Reverted to pristine bundle.")
        return 0

    if not backup.exists():
        shutil.copy2(BUNDLE, backup)
        print(f"Backup saved: {backup.name}")

    # Patched bundles fail VS Code's core-file checksum verification
    # ("installation appears to be corrupt" dialog). Dropping the checksums
    # map from product.json disables that comparison for patched files.
    if PRODUCT_JSON.exists():
        import json
        pbackup = PRODUCT_JSON.with_suffix(".json.orig")
        try:
            pdata = json.loads(PRODUCT_JSON.read_text(encoding="utf-8-sig"))
            if "checksums" in pdata:
                if not pbackup.exists():
                    shutil.copy2(PRODUCT_JSON, pbackup)
                    print(f"Backup saved: {pbackup.name}")
                del pdata["checksums"]
                PRODUCT_JSON.write_text(
                    json.dumps(pdata, indent="\t", ensure_ascii=False) + "\n",
                    encoding="utf-8")
                print("OK    product.json: checksums removed (integrity dialog off)")
            else:
                print("SKIP  product.json: no checksums (already fixed or n/a)")
        except Exception as e:
            print(f"WARN  product.json: {e}")

    data = BUNDLE.read_text(encoding="utf-8")
    changed = False
    for name, old, new in PATCHES:
        count = data.count(old)
        if count == 0:
            already = data.count(new)
            print(f"SKIP  {name}: pattern not found"
                  + (" (already applied)" if already else ""))
            continue
        data = data.replace(old, new)
        changed = True
        print(f"OK    {name}: {count} site(s) patched")

    if changed:
        BUNDLE.write_text(data, encoding="utf-8", newline="")
        print("Bundle written. Restart NeuralInverse to load the patch.")
    else:
        print("Nothing to do.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

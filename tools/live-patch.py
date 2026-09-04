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
        print("Reverted to pristine bundle.")
        return 0

    if not backup.exists():
        shutil.copy2(BUNDLE, backup)
        print(f"Backup saved: {backup.name}")

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

#!/usr/bin/env python3
"""Sandboxed acceptance tests for tools/live-patch.py (task Q4).

Every scenario runs against a THROWAWAY copy of the pristine install
(built from the real .orig baselines) — the installed app is never
touched, and no admin rights are needed.

Scenarios (the Q4 acceptance criteria):
  1. verify on a pristine copy        → the __niC module is MISSING, exit 1
  2. apply on pristine                → exit 0, manifest written, all applied
  3. verify after apply               → all OK — INCLUDING the three insertion
                                        patches whose `old` survives inside
                                        `new` (the false-alarm trap, Q4 §ج)
  4. idempotent re-apply              → `already` everywhere, exit 0
  5. corrupted pattern                → apply exits 1 with a summary;
                                        --allow-missing records it and exits 0
  6. simulated app update             → --revert refuses (exit 2) and points
                                        at --rebaseline; --rebaseline recovers
  7. --status reads the manifest      → app version + last apply present

Exit code: 0 iff every scenario passes; 1 otherwise. SKIPPED (exit 0, clearly
printed) when the real install or its .orig baselines are not present — e.g.
on CI machines — because the sandbox is built from them.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode the arrows and box
# characters this script prints — the run then dies mid-scenario with a
# UnicodeEncodeError that looks like a patch failure. Force UTF-8 on our own
# streams so the output is readable however the script is invoked.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools" / "live-patch.py"
REAL_APP = Path(r"C:\Program Files\NeuralInverse\resources\app")

# patch counts come from the module itself so the selftest stays valid as
# PATCHES/PREPENDS grow
import importlib.util
_spec = importlib.util.spec_from_file_location("lp", SCRIPT)
_lp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_lp)
N_PATCHES = len(_lp.PATCHES)
N_PREPENDS = len(_lp.PREPENDS)
N_TOTAL = N_PATCHES + N_PREPENDS  # verify counts prepends + patches

PRISTINE = {
    "out/vs/workbench/workbench.desktop.main.js": REAL_APP / "out/vs/workbench/workbench.desktop.main.js.orig",
    "out/main.js": REAL_APP / "out/main.js.orig",
    "product.json": REAL_APP / "product.json.orig",
    "node_modules/node-fetch/lib/index.js": REAL_APP / "node_modules/node-fetch/lib/index.js.orig",
}

failures = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {label}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(label)


def run(root: Path, *args: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["NI_OFFLINE"] = "1"
    env.update(extra_env or {})
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                          capture_output=True, text=True, env=env, timeout=300)


def make_sandbox(tmp: Path) -> Path:
    root = tmp / "app"
    # purge state from an earlier sandbox at the same path (manifest + .orig
    # baselines) so every scenario starts truly pristine
    if root.exists():
        for stale in root.rglob(".ni-livepatch.json"):
            stale.unlink()
        for stale in root.rglob("*.orig"):
            stale.unlink()
    for rel, orig in PRISTINE.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(orig, dest)
    return root


def main() -> int:
    missing = [str(p) for p in PRISTINE.values() if not p.exists()]
    if missing:
        print(f"SKIP  live-patch selftest — pristine baselines not present on this machine:")
        for m in missing:
            print(f"      {m}")
        return 0

    with tempfile.TemporaryDirectory(prefix="ni-livepatch-test-") as td:
        tmp = Path(td)
        root = make_sandbox(tmp)

        print("scenario 1: --verify on a pristine copy must report __niC MISSING and exit 1")
        r = run(root, "--verify")
        check("exit code is 1", r.returncode == 1, f"got {r.returncode}")
        check("__niC module reported MISSING", "MISSING conversation-compactor" in r.stdout, r.stdout[-400:])
        # on a pristine copy every patch is PENDING except the two-stage
        # "provider-format fix" (its old only exists after "chatMode null")
        check("unapplied patches are PENDING, not MISSING",
              "PENDING" in r.stdout and f"{N_PATCHES - 1} PENDING" in r.stdout, r.stdout[-200:])

        print("scenario 2: apply on pristine → exit 0 + manifest")
        r = run(root)
        check("exit code is 0", r.returncode == 0, r.stdout[-600:] + r.stderr[-300:])
        check("summary line printed", "summary :" in r.stdout)
        manifest = root / ".ni-livepatch.json"
        check("manifest written", manifest.exists())
        m = json.loads(manifest.read_text(encoding="utf-8-sig"))
        check(f"manifest has {N_PATCHES} patch records", len(m.get("patches", [])) == N_PATCHES)
        check("manifest hashes all four files", set(m.get("files", {}).keys()) == set(PRISTINE.keys()))
        check("manifest recorded the repo commit", m.get("repoCommit") not in (None, ""))

        # A patch that applies cleanly can still be BROKEN JavaScript — a single
        # syntax error kills the whole bundle and the app shows a black screen
        # (happened 2026-09-05 with a duplicated const declaration). Pattern
        # presence is NOT enough: the patched bundles must PARSE.
        for rel in ("out/vs/workbench/workbench.desktop.main.js", "out/main.js"):
            r_check = subprocess.run(["node", "--check", str(root / rel)], capture_output=True, text=True)
            check(f"patched {rel.split('/')[-1]} parses (node --check)", r_check.returncode == 0,
                  (r_check.stderr or "")[-300:])

        print("scenario 3: --verify after apply → all OK, insertion patches included")
        r = run(root, "--verify")
        check("exit code is 0", r.returncode == 0, r.stdout[-400:])
        check(f"{N_TOTAL} OK, nothing missing/pending", f"{N_TOTAL} OK, 0 PENDING, 0 MISSING" in r.stdout, r.stdout[-200:])
        for insertion in ("track finish_reason", "say why a run finished", "populate the field"):
            check(f"insertion patch '{insertion}…' is OK (not a false alarm)",
                  any(line.startswith("OK") and insertion in line for line in r.stdout.splitlines()))

        print("scenario 4: idempotent re-apply")
        r = run(root)
        check("exit code is 0", r.returncode == 0, r.stdout[-400:])
        check("everything already applied", f"0 applied, {N_PATCHES} already" in r.stdout, r.stdout[-200:])

        print("scenario 5: corrupted pattern → apply exits 1; --allow-missing acknowledges")
        root2 = make_sandbox(tmp)
        bundle = root2 / "out/vs/workbench/workbench.desktop.main.js"
        # break the ctx-fit patch so its pattern exists in NO form
        data = bundle.read_text(encoding="utf-8")
        needle = 'c=Math.max(a*1/2,c??4096)'
        assert needle in data, "corruption needle missing from pristine bundle"
        bundle.write_text(data.replace(needle, "/*corrupted-by-selftest*/"), encoding="utf-8", newline="")
        r = run(root2)
        check("exit code is 1", r.returncode == 1, r.stdout[-400:])
        check("missing patch named in output", "MISSING ctx-fit" in r.stdout)
        check("summary reports the miss", "1 missing" in r.stdout)
        r = run(root2, "--allow-missing", "ctx-fit: reserve 1/4 of window for output=selftest corruption")
        check("--allow-missing exits 0", r.returncode == 0, r.stdout[-400:])
        m2 = json.loads((root2 / ".ni-livepatch.json").read_text(encoding="utf-8-sig"))
        check("reason recorded in manifest", any(a["name"].startswith("ctx-fit") for a in m2.get("allowedMissing", [])))

        print("scenario 6: simulated app update → revert refuses, rebaseline recovers")
        root3 = make_sandbox(tmp)
        r = run(root3)
        assert r.returncode == 0, r.stdout
        # simulate an app update landing on top of our patches
        bundle3 = root3 / "out/vs/workbench/workbench.desktop.main.js"
        bundle3.write_text(bundle3.read_text(encoding="utf-8") + "\n// simulated upstream update", encoding="utf-8", newline="")
        r = run(root3, "--revert")
        check("--revert refuses (exit 2)", r.returncode == 2, f"got {r.returncode}")
        check("points at --rebaseline", "--rebaseline" in r.stdout, r.stdout[-300:])
        r = run(root3)
        check("--apply also refuses (exit 2)", r.returncode == 2, f"got {r.returncode}")
        r = run(root3, "--rebaseline")
        check("--rebaseline succeeds", r.returncode == 0, r.stdout[-300:])
        check("manifest removed by rebaseline", not (root3 / ".ni-livepatch.json").exists())
        r = run(root3, "--verify")
        check("verify still sees the patches present after rebaseline",
              r.returncode == 0 and f"{N_TOTAL} OK" in r.stdout, r.stdout[-300:])
        r = run(root3, "--revert")
        check("revert works again after rebaseline", r.returncode == 0, r.stdout[-300:])

        print("scenario 7: --status reads the manifest")
        root4 = make_sandbox(tmp)
        run(root4)
        r = run(root4, "--status")
        check("exit code is 0", r.returncode == 0)
        check("shows last apply from manifest", "last apply" in r.stdout and "repo" in r.stdout)
        check("per-file states listed", "matches last apply" in r.stdout, r.stdout[-300:])

    print("-" * 72)
    if failures:
        print(f"live-patch selftest: {len(failures)} FAILURE(S)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("live-patch selftest: all scenarios passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Jarvis Voice Test Harness — runner auto-evolutivo

Esegue scenari YAML in scenarios/, scrive JSON in runs/, accumula failure
in learnings/ → quando una failure ricorre 3x propaga cicatrice nel vault.

Uso:
  python3 harness.py                       # tutti gli scenari
  python3 harness.py autosend_timing       # singolo scenario
  python3 harness.py --evolve              # solo analizza failure → propose patch

Architettura ispirata al pattern Backward Pass del vault (cicatrice_backprop.py):
ogni failure è un gradient locale → 3x ricorrenza = propagazione globale.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[harness] pyyaml mancante. Esegui: pip3 install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent
SCENARIOS = ROOT / "scenarios"
RUNS = ROOT / "runs"
LEARNINGS = ROOT / "learnings"

RUNS.mkdir(exist_ok=True)
LEARNINGS.mkdir(exist_ok=True)

FAILURE_THRESHOLD = 3  # 3 ricorrenze → cicatrice
RECENT_RUNS = 10        # finestra di lookback


def load_scenarios(name_filter: str | None = None) -> list[dict]:
    out = []
    for f in sorted(SCENARIOS.glob("*.yaml")):
        if name_filter and name_filter not in f.stem:
            continue
        try:
            with f.open() as fh:
                data = yaml.safe_load(fh)
            data["_file"] = f.name
            data["_id"] = f.stem
            out.append(data)
        except Exception as e:
            print(f"[harness] skip {f.name}: {e}", file=sys.stderr)
    return out


def run_scenario(scn: dict) -> dict:
    sid = scn["_id"]
    setup = scn.get("setup", "")
    action = scn["action"]
    check = scn.get("check", "")
    teardown = scn.get("teardown", "")
    timeout = scn.get("timeout", 10)

    started = time.time()
    log = []

    def sh(label: str, cmd: str) -> tuple[int, str, str]:
        if not cmd.strip():
            return 0, "", ""
        try:
            r = subprocess.run(
                ["/bin/zsh", "-c", cmd],
                capture_output=True, text=True, timeout=timeout,
            )
            log.append({"step": label, "rc": r.returncode,
                        "out": (r.stdout or "")[-500:],
                        "err": (r.stderr or "")[-500:]})
            return r.returncode, r.stdout or "", r.stderr or ""
        except subprocess.TimeoutExpired:
            log.append({"step": label, "rc": -1, "err": f"timeout {timeout}s"})
            return -1, "", "timeout"

    sh("setup", setup)
    rc, out, err = sh("action", action)
    chk_rc, chk_out, _ = sh("check", check)
    sh("teardown", teardown)

    passed = (rc == 0) and (chk_rc == 0)
    elapsed = time.time() - started

    return {
        "scenario": sid,
        "passed": passed,
        "elapsed_s": round(elapsed, 3),
        "rc_action": rc,
        "rc_check": chk_rc,
        "check_output": chk_out.strip()[-200:],
        "log": log,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }


def write_run(results: list[dict]) -> Path:
    ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    path = RUNS / f"{ts}.json"
    summary = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results,
    }
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return path


def evolve() -> None:
    """Analizza ultimi RECENT_RUNS run, conta failure per scenario,
    propone cicatrice se >= FAILURE_THRESHOLD."""
    runs = sorted(RUNS.glob("*.json"))[-RECENT_RUNS:]
    if not runs:
        print("[evolve] no runs yet")
        return

    failures: dict[str, list[dict]] = {}
    for rf in runs:
        try:
            data = json.loads(rf.read_text())
            for r in data.get("results", []):
                if not r["passed"]:
                    failures.setdefault(r["scenario"], []).append(r)
        except Exception:
            pass

    print(f"[evolve] analyzed {len(runs)} runs")
    for sid, fails in failures.items():
        n = len(fails)
        marker = "🔴" if n >= FAILURE_THRESHOLD else "🟡"
        print(f"  {marker} {sid}: {n} failures (threshold {FAILURE_THRESHOLD})")
        if n >= FAILURE_THRESHOLD:
            propose_learning(sid, fails)


def propose_learning(sid: str, fails: list[dict]) -> None:
    """Genera draft cicatrice in learnings/. NON propaga al vault automaticamente
    (Mattia decide se promuovere). Pattern: drift sicuro, tu vedi prima di scrivere."""
    path = LEARNINGS / f"learning_{sid}_{datetime.now().strftime('%Y%m%d')}.md"
    if path.exists():
        return  # già proposto oggi
    last = fails[-1]
    body = f"""---
scenario: {sid}
failures: {len(fails)}
status: draft
created: {datetime.now().isoformat(timespec="seconds")}
type: jarvis-voice-learning
---

# Learning — {sid}

**Pattern**: {len(fails)} failure ricorrenti negli ultimi {RECENT_RUNS} run.

## Ultima failure
- Timestamp: {last['ts']}
- Elapsed: {last['elapsed_s']}s
- RC action: {last['rc_action']} | RC check: {last['rc_check']}
- Output check: `{last['check_output']}`

## Hypothesis (TODO Mattia/Polpo)
[ipotesi root cause da scrivere — questa è draft auto-generata]

## Patch proposta
[codice/config diff da applicare]

## Promote
Se confermato → copiare in vault come `feedback_jarvis_voice_{sid}.md` con frontmatter `type: feedback` e aggiungere riga in MEMORY.md per backprop.
"""
    path.write_text(body)
    print(f"  → cicatrice draft scritta: {path.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", nargs="?", help="filtra per nome scenario")
    ap.add_argument("--evolve", action="store_true", help="solo analisi cicatrici")
    args = ap.parse_args()

    if args.evolve:
        evolve()
        return

    scns = load_scenarios(args.scenario)
    if not scns:
        print("[harness] nessuno scenario trovato", file=sys.stderr)
        sys.exit(1)

    print(f"[harness] running {len(scns)} scenari")
    results = []
    for s in scns:
        print(f"  · {s['_id']} ", end="", flush=True)
        r = run_scenario(s)
        print("✅" if r["passed"] else "❌", f"({r['elapsed_s']}s)")
        results.append(r)

    path = write_run(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"[harness] {passed}/{len(results)} passed → {path.name}")

    # Auto-evolve dopo ogni run
    print()
    evolve()


if __name__ == "__main__":
    main()

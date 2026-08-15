#!/usr/bin/env python
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rows = json.loads(Path("data/_scan_candidates_2026-08-13.json").read_text(encoding="utf-8"))
print(f"TOTAL={len(rows)} value={sum(1 for r in rows if r['value'])} lock={sum(1 for r in rows if r['lock'])}")
print("---")
for r in rows:
    v = r.get("value")
    l = r.get("lock")
    h2h = r.get("h2h") or {}
    print(f"{r['date']} | {r['home']} — {r['away']} | {r['league']}")
    print(
        f"  λ={r['lambda_home']:.2f}/{r['lambda_away']:.2f} "
        f"H2H={h2h.get('homeWins')}-{h2h.get('draws')}-{h2h.get('awayWins')}"
    )
    if v:
        print(
            f"  VALUE {v['label']} p={v['p']:.0%} @{v['odds']} "
            f"edge={v['edge']:.1%} ({v['bk']})"
        )
    if l:
        print(
            f"  LOCK {l['label']} p={l['p']:.0%} @{l['odds']} "
            f"edge={l['edge']:.1%} ({l['bk']})"
        )

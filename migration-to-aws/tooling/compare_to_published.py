#!/usr/bin/env python3
"""Compare this build against the currently published power.

Answers three questions for a parity review:

* **regressions** — names the published power has that this build dropped (must be empty)
* **unchanged**   — byte-identical, so the plugin has not touched them
* **updated**     — content differs, i.e. real upstream drift this sync is picking up

Run against a checkout of kirodotdev/powers:

    python3 tooling/compare_to_published.py --published /path/to/powers/migration-to-aws
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--published", required=True, type=Path)
    ap.add_argument("--power", type=Path, default=Path(__file__).resolve().parent.parent)
    args = ap.parse_args()

    pub = args.published.resolve() / "steering"
    mine = args.power.resolve() / "steering"

    pub_files = {p.name: p for p in pub.iterdir() if p.is_file()}
    my_files = {p.name: p for p in mine.iterdir() if p.is_file()}

    regressions = sorted(set(pub_files) - set(my_files))
    added = sorted(set(my_files) - set(pub_files))
    shared = sorted(set(pub_files) & set(my_files))

    unchanged = [n for n in shared if digest(pub_files[n]) == digest(my_files[n])]
    updated = [n for n in shared if digest(pub_files[n]) != digest(my_files[n])]

    print(f"published: {len(pub_files)}    this build: {len(my_files)}")
    print(f"  carried over unchanged : {len(unchanged)}")
    print(f"  refreshed from plugin  : {len(updated)}")
    print(f"  newly added            : {len(added)}")
    print(f"  REGRESSIONS            : {len(regressions)}")

    if regressions:
        print("\n### REGRESSIONS ###")
        for n in regressions:
            print(f"  {n}")

    print("\n### REFRESHED (upstream drift picked up) ###")
    for n in updated:
        pl = len(pub_files[n].read_text(encoding="utf-8", errors="replace").splitlines())
        ml = len(my_files[n].read_text(encoding="utf-8", errors="replace").splitlines())
        delta = ml - pl
        sign = f"+{delta}" if delta > 0 else str(delta)
        print(f"  {n:44s} {pl:5d} -> {ml:5d} lines ({sign})")

    return 1 if regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Time and measure peak memory for `apm compile --dry-run` across builds and project sizes.

Expects generate_project.py to have produced the project directories
already (see README), and setup_envs.sh to have produced the two venvs.

Peak RSS is measured via a small wrapper subprocess that reports
resource.getrusage(RUSAGE_CHILDREN).ru_maxrss for just the apm process it
ran, so it isn't polluted by earlier runs (Linux only; ru_maxrss is in KiB).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_BINARIES = {
    "before": HERE / ".work/before-venv/bin/apm",
    "after": HERE / ".work/after-venv/bin/apm",
}
DEFAULT_PROJECTS = ["proj_small", "proj_1000", "proj_2000"]

WRAPPER_SRC = """
import json, resource, subprocess, sys, time
start = time.perf_counter()
subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
elapsed = time.perf_counter() - start
peak_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
print(json.dumps({"elapsed": elapsed, "peak_kb": peak_kb}))
"""


def run_once(binary: Path, cwd: Path) -> tuple[float, int]:
    result = subprocess.run(
        [sys.executable, "-c", WRAPPER_SRC, str(binary), "compile", "--dry-run", "--no-links", "--target", "claude"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        timeout=300,
    )
    data = json.loads(result.stdout)
    return data["elapsed"], data["peak_kb"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--projects", nargs="+", default=DEFAULT_PROJECTS)
    args = parser.parse_args()

    results: dict[tuple[str, str], list[tuple[float, int]]] = {}
    for proj in args.projects:
        proj_dir = HERE / proj
        if not proj_dir.is_dir():
            raise SystemExit(f"Missing {proj_dir}; run generate_project.py first.")
        for label, binary in DEFAULT_BINARIES.items():
            if not binary.exists():
                raise SystemExit(f"Missing {binary}; run setup_envs.sh first.")
            runs = [run_once(binary, proj_dir) for _ in range(args.repeats)]
            results[(proj, label)] = runs
            times = ["%.2f" % t for t, _ in runs]
            peaks = ["%.0f" % (m / 1024) for _, m in runs]
            print(f"{proj:>10} {label:>7}: time={times} MB={peaks}")

    print()
    header = f"{'project':>10} {'before (min)':>14} {'after (min)':>13} {'speedup':>9} {'before MB':>11} {'after MB':>10} {'mem ratio':>10}"
    print(header)
    for proj in args.projects:
        before_runs = results[(proj, "before")]
        after_runs = results[(proj, "after")]
        before_min = min(t for t, _ in before_runs)
        after_min = min(t for t, _ in after_runs)
        before_mem = min(m for _, m in before_runs) / 1024
        after_mem = min(m for _, m in after_runs) / 1024
        print(
            f"{proj:>10} {before_min:>13.2f}s {after_min:>12.2f}s {before_min / after_min:>8.1f}x "
            f"{before_mem:>10.0f} {after_mem:>9.0f} {before_mem / after_mem:>9.1f}x"
        )


if __name__ == "__main__":
    main()

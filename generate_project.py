#!/usr/bin/env python
"""Generate a synthetic apm project for placement-performance benchmarking.

Builds a monorepo-shaped tree: a set of top-level modules, each with a fixed
sub-tree of src/tests/config directories, until roughly --target-dirs
directories exist in total. Each leaf directory gets a few files across
several extensions. A handful of instructions with different `applyTo`
scopes (some project-wide, some module-scoped) are added so apm's placement
optimizer has to reconcile many overlapping, non-trivial matching-directory
sets -- the condition that stresses placement cost, as opposed to a single
project-wide `applyTo: "**"` instruction, which has its own fast path.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

EXTENSIONS = ["py", "js", "ts", "md", "json"]

INSTRUCTIONS = [
    ("python.instructions.md", "**/*.py", "Python style", "Use type hints on all functions."),
    ("javascript.instructions.md", "**/*.js", "JavaScript style", "Prefer const over let."),
    ("typescript.instructions.md", "**/*.ts", "TypeScript style", "Enable strict null checks."),
    ("markdown.instructions.md", "**/*.md", "Markdown style", "Wrap prose at 100 columns."),
    ("json.instructions.md", "**/*.json", "JSON style", "Keep keys alphabetically sorted."),
    ("module-python.instructions.md", "modules/*/src/**/*.py", "Module Python style", "Module-local Python style."),
    ("module-tests.instructions.md", "modules/*/tests/**/*.py", "Module test style", "Module-local test conventions."),
    ("shared-config.instructions.md", "modules/*/config/**", "Config ownership", "Config files are generated; do not hand-edit."),
]

SUBDIRS_PER_MODULE = ["src", "src/core", "src/utils", "tests", "config"]


def build_tree(root: Path, target_dirs: int, files_per_dir: int) -> int:
    modules_root = root / "modules"
    modules_root.mkdir(parents=True, exist_ok=True)

    dirs_per_module = 1 + len(SUBDIRS_PER_MODULE)  # module dir itself + subdirs
    num_modules = max(1, target_dirs // dirs_per_module)

    dir_count = 0
    for m in range(num_modules):
        module_dir = modules_root / f"module_{m:04d}"
        module_dir.mkdir(parents=True, exist_ok=True)
        dir_count += 1
        for sub in SUBDIRS_PER_MODULE:
            d = module_dir / sub
            d.mkdir(parents=True, exist_ok=True)
            dir_count += 1
            for i in range(files_per_dir):
                ext = EXTENSIONS[i % len(EXTENSIONS)]
                (d / f"file_{i}.{ext}").write_text(f"// generated file {i}\n", encoding="utf-8")
    return dir_count


def write_instructions(root: Path) -> None:
    instr_dir = root / ".apm" / "instructions"
    instr_dir.mkdir(parents=True, exist_ok=True)
    for filename, apply_to, description, body in INSTRUCTIONS:
        (instr_dir / filename).write_text(
            f'---\napplyTo: "{apply_to}"\ndescription: "{description}"\n---\n{body}\n',
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path, help="Output project directory (recreated if it exists)")
    parser.add_argument("--target-dirs", type=int, default=1000)
    parser.add_argument("--files-per-dir", type=int, default=3)
    args = parser.parse_args()

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)

    (args.out / "apm.yml").write_text("name: placement-bench\nversion: 0.1.0\n", encoding="utf-8")
    dir_count = build_tree(args.out, args.target_dirs, args.files_per_dir)
    write_instructions(args.out)
    print(f"Generated {dir_count} directories under {args.out}")


if __name__ == "__main__":
    main()

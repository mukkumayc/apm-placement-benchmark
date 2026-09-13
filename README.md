# apm placement benchmark

Performance comparison for [apm](https://github.com/microsoft/apm)'s `apm compile`,
before and after a placement optimizer fix, on synthetic monorepo-shaped
projects.

## Results

Minimum of several repeats. Memory is peak RSS of the `apm` process:

| project | directories | before | after | speedup | before MB | after MB |
|---|---:|---:|---:|---:|---:|---:|
| `proj_small` | ~6 | 0.28s | 0.29s | 1.0x | 67 | 67 |
| `proj_1000` | ~1000 | 3.18s | 0.60s | 5.3x | 78 | 75 |
| `proj_2000` | ~2000 | 9.64s | 0.92s | 10.5x | 89 | 85 |
| `proj_10000` | ~10000 | 189.01s | 3.53s | 53.5x | 179 | 157 |

Before = latest `main` (`f8df1b75`); after = `perf/placement-large-tree-scaling`.

Compile time grows superlinearly with directory count before the fix and
stays close to flat after. Peak RSS barely moves either way.

## Reproducing

```sh
python generate_project.py proj_small --target-dirs 1
python generate_project.py proj_1000 --target-dirs 1000
python generate_project.py proj_2000 --target-dirs 2000

./setup_envs.sh   # optionally: repo_url before_ref after_ref
python benchmark.py
```

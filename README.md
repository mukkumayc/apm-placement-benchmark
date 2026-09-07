# apm placement benchmark

Performance comparison for [apm](https://github.com/microsoft/apm)'s `apm compile`,
before and after a placement optimizer fix, on synthetic monorepo-shaped
projects.

## Results

Minimum of several repeats. Memory is peak RSS of the `apm` process:

| project | directories | before | after | speedup | before MB | after MB |
|---|---:|---:|---:|---:|---:|---:|
| `proj_small` | ~6 | 0.28s | 0.27s | 1.0x | 67 | 67 |
| `proj_1000` | ~1000 | 2.90s | 0.58s | 5.0x | 77 | 74 |
| `proj_2000` | ~2000 | 8.39s | 0.92s | 9.1x | 87 | 82 |
| `proj_10000` | ~10000 | 158.00s | 3.61s | 43.8x | 167 | 145 |

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

# Final method (November 2026)

One method with the same settings for every use case, DSO and TSO. It changes three things in the combined method of [`METHOD.md`](METHOD.md); Variance-Distance Spanning Tree, the physics residual, Liu's features and the decoding into a valid topology stay as they are.

| Step | Original combined method | Final method |
|---|---|---|
| Classifier | random forest, 100 trees | **XGBoost tuned with Optuna** (nested grouped CV, 30 trials, log loss), or **TabFM** zero-shot |
| Features | Liu's features + residual | + **neighbourhood features**: `rel` (z-score and percentile of distance, residual and correlation within the case) and `loc` (number of candidates at the two ends, value of the line against the alternative lines at the same ends; LV and Far West, where the end-points are known) |
| Physics refinement | greedy, only lines with probability 0.05–0.95, change kept if the residual drops by more than 1% | greedy over **all** lines, change kept if the residual drops by more than **0.1%** |
| Passes | one | **two**: the physics features are recomputed around the first-pass estimate and the classifier is trained again |

Liu's own random forest (`liu_only`) is unchanged.

The second pass recomputes, around the first-pass estimate instead of the register:
- use cases 1 and 4: the power-flow residual of every candidate line;
- use case 2: the power balance at the head of each feeder, with every customer on the feeder of the first pass;
- use case 3: the three-phase voltage residual, with every customer on the phase of the first pass.

## Results (register 80% correct, one month)

Main experiment of each use case: SimBench LV (72 cases) and MV with every MV/LV substation metered (64 cases); Far West ACTIVSg2000 with PMU angles at every bus, σ = 0.1° (93 and 62 configurations).

**Final method with TabFM**, laptop run (Intel i7, 16 threads, float32); original and final on the same cases. Per-case files: [`results/final_method_pc/`](results/final_method_pc).

| Use case | Metric | Register | Original (RF, 1 pass) | Final, TabFM |
|---|---|---|---|---|
| DSO 1 · LV topology | % lines in the correct state | 79.8 | 95.2 | **98.1** |
| DSO 2 · customer → feeder | % customers correct | 79.1 | 94.2 | **94.8** |
| DSO 3 · customer → phase | % customers correct | 79.1 | 98.9 | **99.0** |
| DSO 4 · MV open points | % open points found · false openings | 81.5 | 95.0 · 28 | **97.1 · 16** |
| TSO 1 · 20% of statuses wrong | % correct · out of service found · false "out" | 79.6 | 99.53 · 102/138 · 11 | **99.62 · 126/138** · 26 |
| TSO 4 · 1 of 5 outages on the wrong branch | % out of service found · false "out" | 80.0 | 89.0 (276/310) · 20 | **95.8 (297/310)** · 33 |

**Final method with XGBoost**, 2-core cloud run with its own Far West scenarios (so its TSO originals differ slightly). Per-case files: [`results/final_method/`](results/final_method).

| Use case | Original (RF, 1 pass) | Final, XGBoost | Final, TabFM (same run) |
|---|---|---|---|
| DSO 1 · LV topology | 95.1 | **98.1** | 98.1 |
| DSO 2 · customer → feeder | 94.2 | 94.1 | – |
| DSO 3 · customer → phase | 98.9 | 98.9 | – |
| DSO 4 · MV open points | 95.0 · 28 | **97.2 · 16** | – |
| TSO 1 | 99.5 · 98/138 · 14 | 99.3 · 117/138 · 45 | – |
| TSO 4 | 90.0 (279/310) · 14 | 93.2 (289/310) · 32 | **96.5 (299/310) · 30** |

- **DSO:** clear gains in use cases 1 and 4 with either classifier; in 2 and 3 the original was already at 94–99%, and TabFM adds a little (+0.6 and +0.1) where XGBoost ties.
- **TSO:** both find more out-of-service branches. TabFM does it with fewer extra false alarms (+15 and +13 against +31 and +18 for XGBoost), so on TSO 1 the share in the correct state also rises. In the meshed transmission grid the probability gate held false alarms back; in the radial DSO it blocked correct corrections. The settings stay the same everywhere.
- TSO 4 is reproduced across the two runs: +6.8 points on the laptop, +6.5 in the cloud.
- **Where the gain comes from (DSO 1):**
  - random forest, original settings: 95.14;
  - random forest with the new refinement settings: 97.58;
  - XGBoost instead of the random forest: 97.51;
  - with the neighbourhood features: 98.07.

  The refinement settings and the neighbourhood features matter, not the classifier. TabFM ties with XGBoost on DSO 1 (98.12 vs 98.07, paired 95% interval −0.19 to +0.35). It is clearly better on the TSO, where the training set is small (62–93 cases × 108 branches).
- Original method reproduced in this run: TSO 1 gives 99.46 · 98/138 · 14 against the shipped 99.5 · 97/138 · 12. The scenarios were generated again.

## Run it

```bash
pip install -r requirements.txt
python run_all.py --stage original --workers 4               # original method, the six experiments (inputs of the final one)
python run_all.py --stage final --clf xgb_tuned --workers 4  # final method with XGBoost
python run_all.py --stage final --clf tabfm --workers 4      # final method with TabFM
python final_table.py --clf xgb_tuned --clf tabfm --out results/final_method
```

`--stage final` runs `original` first if its outputs are missing, and prints the table at the end. Steps whose output exists are skipped, so an interrupted run can be restarted with the same command. The Far West data must be in `far_west/data/` (see [`README.md`](README.md)).

**TabFM**
- Install: `pip install git+https://github.com/google-research/tabfm.git` (tested at commit `fbb6655`).
- The first run downloads `google/tabfm-1.0.0-pytorch` from Hugging Face (about 6 GB).
- It runs on CPU in float32 by default, using every core (`TABFM_THREADS` to limit). It needs about 7 GB of RAM; 16 GB or more is comfortable.
- Less memory: `TABFM_DTYPE=bfloat16` (about half), or `TABFM_BF16` pointing to a folder holding a bfloat16 copy (`config.json`, `model.safetensors`), which loads in about 3.3 GB.
- `TABFM_NEST` sets the ensemble members (default 4). `TABFM_MAXN` sets the most training rows used as context (default 10000; larger sets are subsampled with stratification).
- Each fit and prediction prints its size and duration. In DSO use case 1 every fold is saved as a checkpoint, so a restart resumes from the last finished fold.
- The weights have a non-commercial licence.

**Time**, measured:

| Step | 2-core cloud machine | Laptop, Intel i7, 16 threads, `--workers 4` |
|---|---|---|
| Original method, all six (incl. the Far West scenarios, run once) | about 12 h | about 5–6 h |
| Final method, XGBoost, all six | about 7 h | not measured |
| Final method, TabFM, DSO 1 / 2 / 3 / 4 | – | about 2 h / 6.5 h / 4.5 h / 1 h |

A TabFM fold costs about 16 min for a 10,000-row context plus about 0.2 s per predicted row on the laptop; use cases 2 and 3 predict up to 12,700 rows per fold, so they are the slow part.

**Windows:** `run_all.py` links shared caches with symbolic links and falls back to copies where links are not allowed. Developer mode avoids the copies.

## Code

| File | Role |
|---|---|
| `simbench/clf_extra.py` | `xgb_tuned` (Optuna, nested grouped CV), `xgb_tp` (tuned for the open class), `tabfm` (zero-shot) |
| `simbench/tabfm_lowmem.py` | loads TabFM once per process (official loader or a bfloat16 copy) |
| `simbench/fe.py` | neighbourhood features `rel`, `loc` (`FE=rel,loc`) |
| `final_table.py` | original vs final table and per-case files |

Environment variables used by the final method: `CLF` / `VAR` (classifier), `FE`, `GLO`/`GHI` and `FWGLO`/`FWGHI` (probability gate; −1/2 = none), `MINGAIN` (minimum relative gain of the refinement), `PASS2` / `MVPASS2` (second pass), `SUFFIX`, `SUFFIX2`, `OUTTAG`, `OUTSFX` (output folders).

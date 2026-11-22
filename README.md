# DSO Service 7 — AI-based Grid Topology Identification

EnerTEF TEF DSO node · D2.2 §2.6.7

The repository has three parts.

| Folder | What it is |
|---|---|
| [`variance_distance_spanning_tree/`](variance_distance_spanning_tree/) | The original service: validates the documented topology of an LV network against smart meter voltages (variance distance + Kruskal), with its report and experiments. |
| [`combined_method/`](combined_method/) | All four use cases: the random forest of Dong Liu (TU Delft) combined with Variance-Distance Spanning Tree, the power-flow residual and a physics refinement, on SimBench (LV, MV) and on the ACTIVSg2000 Far West transmission area. Code to reproduce every result, the results and the summary ([`RESULTS.md`](combined_method/RESULTS.md)). The final method (XGBoost or TabFM, neighbourhood features, refinement without gate, second pass) is in [`FINAL_METHOD.md`](combined_method/FINAL_METHOD.md). |
| [`uc3_siamese_method/`](uc3_siamese_method/) | Use case 3 (phase identification): the siamese method of Dong Liu, our implementation from the paper, reported next to the combination. |

## Results of the final method (register 80% correct, one month)

The final method is the same for every use case, DSO and TSO: TabFM (or XGBoost) as the classifier, neighbourhood features, the physics refinement over all lines with a 0.1% minimum gain, and a second pass ([`FINAL_METHOD.md`](combined_method/FINAL_METHOD.md)). It is compared with the original combination: random forest, probability gate 0.05–0.95, 1% minimum gain, one pass. Both run on the same cases; Far West uses PMU angles at every bus (σ = 0.1°).

| Use case | Metric | Register | Original combination | Final method, TabFM |
|---|---|---|---|---|
| DSO 1 · LV topology | % lines in the correct state | 79.8 | 95.2 | **98.1** |
| DSO 2 · customer → feeder | % customers correct | 79.1 | 94.2 | **94.8** |
| DSO 3 · customer → phase | % customers correct | 79.1 | 98.9 | **99.0** |
| DSO 4 · MV open points | % open points found · false openings | 81.5 | 95.0 · 28 | **97.1 · 16** |
| TSO 1 · 20% of statuses wrong (93 configurations) | % correct · out of service found · false "out" | 79.6 | 99.53 · 102/138 · 11 | **99.62 · 126/138** · 26 |
| TSO 4 · 1 of 5 outages on the wrong branch (62 configurations) | % out of service found · false "out" | 80.0 | 89.0 (276/310) · 20 | **95.8 (297/310)** · 33 |

- Higher on the main metric in all six. Clear gains in the two topology problems of the DSO (LV +2.9, MV +2.1 with 12 fewer false openings); DSO 2 and 3 were already at 94–99%.
- TSO: 24 and 21 more out-of-service branches found, at the cost of more false alarms (+15 and +13).
- With XGBoost instead of TabFM the DSO results are the same within 0.7 points (98.1 / 94.1 / 98.9 / 97.2 · 16). On the TSO, XGBoost finds fewer branches for more false alarms (TSO 1: 99.3 · 117/138 · 45 against 99.5 · 98/138 · 14 for the original, on a separate run of the scenarios).
- TabFM run on a laptop (Intel i7, 16 threads); XGBoost on a 2-core cloud machine (about 7 h). Per-case files: [`combined_method/results/final_method_pc/`](combined_method/results/final_method_pc) (TabFM) and [`combined_method/results/final_method/`](combined_method/results/final_method) (XGBoost).

## Original combination: results at a glance (one month of data, no phase angle)

Share of the network in the right state for documentation 70 / 80 / 90% correct. The combination builds on the random forest of Dong Liu and adds the physics of the network.

| Use case · scenario | Documented | Variance-Distance Spanning Tree | Random forest (Liu) | Combination | Siamese (Liu) |
|---|---|---|---|---|---|
| 1 · LV | 69.8 / 79.8 / 90.2 | 92.6 / 94.8 / 97.6 | 76.2 / 80.2 / 86.9 | 93.6 / 95.1 / 97.6 | – |
| realistic register (spare cables, wrong lengths) | 69.8 / 79.8 / 90.2 | 81.6 / 83.5 / 85.6 | 63.3 / 69.5 / 79.3 | 85.4 / 89.7 / 94.7 | – |
| same + training only from the register (80%) | 79.8 | 83.5 | 62.8 | 89.1 | – |
| 1 · Far West (80% only) | 79.6 | 82.1 | 98.2 | 99.4 | – |
| fast mode + wrong lengths | 70.4 / 79.6 / 89.8 | 81.9 / 81.9 / 81.9 | 98.0 / 98.1 / 98.3 | 99.0 / 99.2 / 99.3 | – |
| 2 · LV | 69.8 / 79.1 / 90.5 | 69.3 / 71.9 / 74.4 | 50.8 / 53.7 / 55.2 | 89.5 / 94.2 / 96.1 | – |
| no metering at the feeder heads | 69.8 / 79.1 / 90.5 | 69.3 / 71.9 / 74.4 | 50.8 / 53.7 / 55.2 | 70.5 / 80.7 / 91.3 | – |
| 30% customers unlabelled, as in Liu | 69.8 (known) | 91.9 | 90.5 | 96.8 | – |
| 3 · LV | 69.8 / 79.1 / 90.5 | 82.3 / 89.2 / 92.9 | 82.8 / 85.0 / 88.3 | 98.3 / 98.9 / 99.5 | 98.5 at all levels (no register) |
| wrong cable lengths in the register | 69.8 / 79.1 / 90.5 | 82.3 / 89.2 / 92.9 | 82.8 / 85.0 / 88.3 | 98.3 / 98.7 / 99.5 | – |
| 4 · MV | 71.5 / 81.5 / 86.9 | 78.9 / 78.3 / 76.7 | 69.3 / 77.7 / 83.7 | 90.6 / 95.0 / 95.9 | – |
| meter at half of the MV/LV substations (80%) | 81.5 | 29.2 | 69.8 | 88.3 | – |
| 4 · Far West (80% only) | 80.0 | 74.5 | 71.9 | 85.8 | – |
| fast mode + wrong lengths | 80.0 | 74.2 | 68.4 | 82.6 | – |

Use case 4: share of truly open elements found. SimBench with personalized customer profiles ([`combined_method/PERSONALIZED_PROFILES.md`](combined_method/PERSONALIZED_PROFILES.md)).
Details, minimum requirements and limits: [`combined_method/RESULTS.md`](combined_method/RESULTS.md); method: [`combined_method/METHOD.md`](combined_method/METHOD.md).

All results are on simulated data (SimBench network models, ACTIVSg2000 synthetic grid); there is no field validation.

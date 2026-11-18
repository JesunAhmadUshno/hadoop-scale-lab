# Gap-closure re-execution summary (runs of 2026-11-18, registered as D18)

Source rows: results/rerun_2026-11-17_raw_runs.jsonl (warm-up plus three
timed runs per cell; no run void in any cell). Medians are over the three
timed runs. Output hashes matched the committed hashes in every run
(0.1 GiB c34381cf0ea8, full ffdc1bdaa2bc).

## 0.1 GiB anchor cell (Job ii)

| arm | fresh runs (s) | fresh median | committed median |
| --- | --- | --- | --- |
| baseline (local) | 50.163, 49.424, 49.788 | 49.788 | 49.871 |
| MapReduce (combined, rf 1) | 115.827, 115.031, 113.935 | 115.031 | 114.125 |

Fresh ratio R(0.1 GiB) = 115.031 / 49.788 = 2.311. Committed ratio 2.288.

## Full corpus anchor cell (1.85 GiB, Job ii)

| arm | fresh runs (s) | fresh median | committed median |
| --- | --- | --- | --- |
| baseline (local) | 996.680, 991.381, 1011.282 | 996.680 | 990.793 |
| MapReduce (combined, rf 1) | 949.841, 940.031, 945.739 | 945.739 | 954.534 |

Fresh ratio R(full) = 945.739 / 996.680 = 0.949. Committed ratio 0.963.

## Reading

Both anchor cells completed on the machine and reproduced: identical
output hashes, fresh medians within 1 percent of the committed medians on
three of four arms (MapReduce at 0.1 GiB is +0.8 percent), and the H1
pattern unchanged in direction and size: MapReduce is about 2.3x the
baseline at 0.1 GiB and slightly faster than the baseline at full corpus
(ratio below 1 on both the committed and the fresh numbers).

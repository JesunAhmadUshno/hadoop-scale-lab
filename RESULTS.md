# Results

## Verdicts (frozen rules, PREREGISTRATION.md)

- H1: **CONFIRMED**. R(full)=0.963, R(0.1 GiB)=2.288
- H2: **INCONCLUSIVE**. a needed cell is missing or void
- H3: **INCONCLUSIVE**. write penalty 29.5%, job penalty -0.1%
- H4: **REFUTED**. spark 1087.0s vs MR 954.5s

## Median wall times (seconds, 3 timed runs per cell)

| Job | Scale | Baseline | MapReduce | Ratio |
| --- | --- | --- | --- | --- |
| ii | 0.1GiB | 49.871 | 114.125 | 2.288 |
| ii | 1GiB | 541.092 | 572.420 | 1.058 |
| ii | full | 990.793 | 954.534 | 0.963 |
| bands | 0.1GiB | 17.042 | 86.834 | 5.095 |
| bands | 1GiB | 173.619 | 243.936 | 1.405 |
| bands | full | 320.605 | 345.136 | 1.077 |

## Raw run table

| Arm | Job | Scale | Layout | RF | Run | Warm-up | Wall s | Shuffle bytes | HDFS read | HDFS written | SHA-256 (short) | Void |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | ii | 0.1GiB | local | None | 0 | True | n/a | None | None | None | c34381cf0ea8 | False |
| baseline | ii | 0.1GiB | local | None | 1 | False | 49.844 | None | None | None | c34381cf0ea8 | False |
| baseline | ii | 0.1GiB | local | None | 2 | False | 50.175 | None | None | None | c34381cf0ea8 | False |
| baseline | ii | 0.1GiB | local | None | 3 | False | 49.871 | None | None | None | c34381cf0ea8 | False |
| mapreduce | ii | 0.1GiB | combined | 1 | 0 | True | n/a | 34924930 | 107428320 | 34639946 | c34381cf0ea8 | False |
| mapreduce | ii | 0.1GiB | combined | 1 | 1 | False | 113.924 | 34924930 | 107428320 | 34639946 | c34381cf0ea8 | False |
| mapreduce | ii | 0.1GiB | combined | 1 | 2 | False | 114.125 | 34924930 | 107428320 | 34639946 | c34381cf0ea8 | False |
| mapreduce | ii | 0.1GiB | combined | 1 | 3 | False | 114.333 | 34924930 | 107428320 | 34639946 | c34381cf0ea8 | False |
| baseline | ii | 1GiB | local | None | 0 | True | n/a | None | None | None | 2c99665ced2d | False |
| baseline | ii | 1GiB | local | None | 1 | False | 542.207 | None | None | None | 2c99665ced2d | False |
| baseline | ii | 1GiB | local | None | 2 | False | 534.839 | None | None | None | 2c99665ced2d | False |
| baseline | ii | 1GiB | local | None | 3 | False | 541.092 | None | None | None | 2c99665ced2d | False |
| mapreduce | ii | 1GiB | combined | 1 | 0 | True | n/a | 430718780 | 1073749302 | 423331743 | 2c99665ced2d | False |
| mapreduce | ii | 1GiB | combined | 1 | 1 | False | 572.420 | 430718780 | 1073749302 | 423331743 | 2c99665ced2d | False |
| mapreduce | ii | 1GiB | combined | 1 | 2 | False | 572.231 | 430718780 | 1073749302 | 423331743 | 2c99665ced2d | False |
| mapreduce | ii | 1GiB | combined | 1 | 3 | False | 632.935 | 430718780 | 1073749302 | 423331743 | 2c99665ced2d | False |
| baseline | ii | full | local | None | 0 | True | n/a | None | None | None | ffdc1bdaa2bc | False |
| baseline | ii | full | local | None | 1 | False | 981.455 | None | None | None | ffdc1bdaa2bc | False |
| baseline | ii | full | local | None | 2 | False | 998.646 | None | None | None | ffdc1bdaa2bc | False |
| baseline | ii | full | local | None | 3 | False | 990.793 | None | None | None | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 0 | True | n/a | 806355510 | 1984438900 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 1 | False | 945.828 | 806355510 | 1984438900 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 2 | False | 954.534 | 806355510 | 1984438900 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 3 | False | 964.136 | 806355510 | 1984438900 | 787857293 | ffdc1bdaa2bc | False |
| baseline | bands | 0.1GiB | local | None | 0 | True | n/a | None | None | None | c69010a15715 | False |
| baseline | bands | 0.1GiB | local | None | 1 | False | 17.362 | None | None | None | c69010a15715 | False |
| baseline | bands | 0.1GiB | local | None | 2 | False | 16.913 | None | None | None | c69010a15715 | False |
| baseline | bands | 0.1GiB | local | None | 3 | False | 17.042 | None | None | None | c69010a15715 | False |
| mapreduce | bands | 0.1GiB | combined | 1 | 0 | True | n/a | 301 | 107428320 | 266 | c69010a15715 | False |
| mapreduce | bands | 0.1GiB | combined | 1 | 1 | False | 86.834 | 301 | 107428320 | 266 | c69010a15715 | False |
| mapreduce | bands | 0.1GiB | combined | 1 | 2 | False | 87.030 | 301 | 107428320 | 266 | c69010a15715 | False |
| mapreduce | bands | 0.1GiB | combined | 1 | 3 | False | 85.932 | 301 | 107428320 | 266 | c69010a15715 | False |
| baseline | bands | 1GiB | local | None | 0 | True | n/a | None | None | None | 8083ad02376b | False |
| baseline | bands | 1GiB | local | None | 1 | False | 174.443 | None | None | None | 8083ad02376b | False |
| baseline | bands | 1GiB | local | None | 2 | False | 173.619 | None | None | None | 8083ad02376b | False |
| baseline | bands | 1GiB | local | None | 3 | False | 173.556 | None | None | None | 8083ad02376b | False |
| mapreduce | bands | 1GiB | combined | 1 | 0 | True | n/a | 1394 | 1073749302 | 283 | 8083ad02376b | False |
| mapreduce | bands | 1GiB | combined | 1 | 1 | False | 243.130 | 1394 | 1073749302 | 283 | 8083ad02376b | False |
| mapreduce | bands | 1GiB | combined | 1 | 2 | False | 243.936 | 1394 | 1073749302 | 283 | 8083ad02376b | False |
| mapreduce | bands | 1GiB | combined | 1 | 3 | False | 250.888 | 1394 | 1073749302 | 283 | 8083ad02376b | False |
| baseline | bands | full | local | None | 0 | True | n/a | None | None | None | 62ef9781b196 | False |
| baseline | bands | full | local | None | 1 | False | 326.754 | None | None | None | 62ef9781b196 | False |
| baseline | bands | full | local | None | 2 | False | 317.355 | None | None | None | 62ef9781b196 | False |
| baseline | bands | full | local | None | 3 | False | 320.605 | None | None | None | 62ef9781b196 | False |
| mapreduce | bands | full | combined | 1 | 0 | True | n/a | 2405 | 1984438900 | 291 | 62ef9781b196 | False |
| mapreduce | bands | full | combined | 1 | 1 | False | 345.136 | 2405 | 1984438900 | 291 | 62ef9781b196 | False |
| mapreduce | bands | full | combined | 1 | 2 | False | 343.025 | 2405 | 1984438900 | 291 | 62ef9781b196 | False |
| mapreduce | bands | full | combined | 1 | 3 | False | 346.130 | 2405 | 1984438900 | 291 | 62ef9781b196 | False |
| mapreduce | ii | full | combined | 1 | 0 | True | n/a | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 1 | False | 972.733 | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 2 | False | 976.830 | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 1 | 3 | False | 976.930 | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 3 | 0 | True | n/a | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 3 | 1 | False | 972.533 | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 3 | 2 | False | 975.439 | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| mapreduce | ii | full | combined | 3 | 3 | False | 980.000 | 806355510 | 1984438945 | 787857293 | ffdc1bdaa2bc | False |
| spark | ii | full | combined | 1 | 0 | True | n/a | None | None | None | ffdc1bdaa2bc | False |
| spark | ii | full | combined | 1 | 1 | False | 1085.642 | None | None | None | ffdc1bdaa2bc | False |
| spark | ii | full | combined | 1 | 2 | False | 1105.144 | None | None | None | ffdc1bdaa2bc | False |
| spark | ii | full | combined | 1 | 3 | False | 1086.950 | None | None | None | ffdc1bdaa2bc | False |

VOID CELL: job ii scale 1GiB layout small: operator stop before completion: warm-up run past 2.5 h with about 640 of 1055 maps complete (about 117 s slot time per 1 MiB map); cell not measured, H2 untested. See DECISIONS.md D10.

Ingest: scale full rf 1 warm-up True wall 58.708 s

Ingest: scale full rf 1 warm-up False wall 59.709 s

Ingest: scale full rf 3 warm-up True wall 76.525 s

Ingest: scale full rf 3 warm-up False wall 77.297 s

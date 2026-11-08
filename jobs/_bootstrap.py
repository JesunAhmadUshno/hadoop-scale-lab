"""Path bootstrap for the streaming scripts.

Hadoop Streaming ships src/common.py next to the job scripts (via
-files), so `import common` works in the task working directory. When
the scripts run locally (smoke tests, this repo's test suite) common
lives in ../src. This snippet makes both work."""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
for _cand in (_here, os.path.join(_here, "..", "src"), os.getcwd()):
    if os.path.exists(os.path.join(_cand, "common.py")):
        if _cand not in sys.path:
            sys.path.insert(0, _cand)
        break

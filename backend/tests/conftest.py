"""Point persistence at a throwaway directory before the app is imported.

store.py resolves its data directory at import time, so this has to run first —
pytest loads conftest before collecting test modules, which is exactly the hook
needed. Without it, running the suite would overwrite the real scenario file.
"""

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="payroll-tests-"))
os.environ["PAYROLL_DATA_DIR"] = str(_TMP)

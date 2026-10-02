"""pytest 全局夹具：确保仓库根在 sys.path（直接 import core/cli）"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

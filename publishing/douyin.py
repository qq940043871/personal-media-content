"""douyin 别名入口 — python -m publishing.douyin（实际实现见 publishing/douyin_publisher.py）"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from publishing.douyin_publisher import main

if __name__ == '__main__':
    main()

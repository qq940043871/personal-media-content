"""feishu 别名入口 — python -m publishing.feishu（实际实现见 publishing/feishu_publisher.py）"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from publishing.feishu_publisher import main

if __name__ == '__main__':
    main()

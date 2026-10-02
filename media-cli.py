#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
media-cli — AI 自媒体内容生产中台 统一命令行入口（薄壳）

命令实现见 cli/ 包：
    cli/app.py        解析器组装
    cli/commands/     各命令域（status/doctor/video/ai/publish/story/asset/task/storage/dashboard）

用法：
    python media-cli.py --help
    python media-cli.py doctor --live              # 环境自检 + 探活
    python media-cli.py status                     # 查看整体状态
"""

import sys
import os

# 确保 core / cli 包可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.app import main

if __name__ == '__main__':
    main()

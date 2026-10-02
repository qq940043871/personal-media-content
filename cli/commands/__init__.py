"""cli.commands — 各命令域模块；register_all 把全部子命令挂到主解析器"""

from . import status, doctor, video, ai, publish, story, asset, task, storage, dashboard

COMMAND_MODULES = (status, doctor, video, ai, publish, story, asset, task, storage, dashboard)


def register_all(subparsers):
    for module in COMMAND_MODULES:
        module.register(subparsers)

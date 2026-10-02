"""
cli — media-cli 的命令实现包

media-cli.py 只是薄入口；每个业务域一个模块（status/video/ai/publish/story/asset/task/storage/dashboard/doctor），
模块内提供 cmd_* 处理函数与 register(subparsers) 注册函数。新增命令：在对应模块加函数并登记。
"""

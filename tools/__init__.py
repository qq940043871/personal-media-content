"""
tools — 对外动作层（发布工具，skill 化预备）

与 core/（对内能力层：config/providers/转化/存储/统计）的分工见 ARCHITECTURE.md。
本包内所有工具遵循统一接口契约（详见 tools/README.md）：

1. 可独立运行：python -m tools.<tool> <action>，路径锚定仓库根，不依赖 CWD
2. 统一输出：--json 输出机器可读结果；退出码 0=成功 1=失败
3. 凭据只读根 .env，密钥不进参数不进日志
4. 数据契约 = assets/ 资产库（drafts → 发布成功 → published/ + meta.json）

已登记发布平台的注册表在 tools/publisher_base.py（_load_publisher / KNOWN_PLATFORMS）。
"""

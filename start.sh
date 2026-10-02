#!/usr/bin/env bash
# ============================================================
#  start.sh — 统一启动器（Git Bash 版；无参=菜单，带参=透传给 media-cli.py）
#
#    ./start.sh                 交互式菜单
#    ./start.sh status          直接执行 media-cli.py status
#    ./start.sh doctor --live   参数原样透传
#
#  解释器选择：本机 python 可能指向没装依赖的托管版（缺 python-dotenv），
#  故逐个候选探测「能 import dotenv」的那个再使用（依赖装在 anaconda）。
# ============================================================

set -u
cd "$(dirname "$0")" || exit 1

ROOT="$(pwd)"

pick_python() {
    for c in "$HOME/anaconda3/python.exe" "/c/ProgramData/anaconda3/python.exe" \
             "python" "python3" "py"; do
        if command -v "$c" >/dev/null 2>&1 && "$c" -c "import dotenv" >/dev/null 2>&1; then
            echo "$c"
            return 0
        fi
    done
    echo "python"   # 兜底：没找到带依赖的解释器，交给后续报错提示
}

PY="$(pick_python)"
if [ "$PY" = "python" ] && ! python -c "import dotenv" >/dev/null 2>&1; then
    echo "[!] 没找到装了依赖的 Python（需要 python-dotenv）"
    echo "    先跑菜单 [7] 安装依赖，或手工执行：pip install -r requirements.txt"
fi

# 带参数 → 直接透传
if [ $# -gt 0 ]; then
    "$PY" media-cli.py "$@"
    exit $?
fi

while true; do
    clear
    echo "============================================================"
    echo "  AI 自媒体内容生产中台 - 启动器"
    echo "============================================================"
    echo "  仓库   : $ROOT"
    echo "  解释器 : $PY"
    echo
    echo "  [1] 环境自检      doctor       接入/排障第一步"
    echo "  [2] 创作状态      status       小说/资产/稿件盘点"
    echo "  [3] 资产库骨架    asset init   幂等建齐 drafts/published"
    echo "  [4] 待发布清单    asset ls"
    echo "  [5] 发布资产      asset publish（输入资产路径）"
    echo "  [6] Web 数据看板  dashboard start（127.0.0.1:5000）"
    echo "  [7] 安装依赖      pip install -r requirements.txt"
    echo "  [8] 回归测试      pytest tests/"
    echo "  [9] 打开文档      README.md"
    echo "  [0] 退出"
    echo
    read -r -p "选择 [0-9]: " CHOICE
    case "$CHOICE" in
        1) "$PY" media-cli.py doctor ;;
        2) "$PY" media-cli.py status ;;
        3) "$PY" media-cli.py asset init ;;
        4) "$PY" media-cli.py asset ls ;;
        5) read -r -p "资产文件路径（如 assets/wechat/drafts/x.md）: " ASSET
           [ -n "${ASSET:-}" ] && "$PY" media-cli.py asset publish --file "$ASSET" ;;
        6) "$PY" media-cli.py dashboard start ;;
        7) "$PY" -m pip install -r requirements.txt
           read -r -p "顺带装测试依赖 pytest? [y/N] " DEV
           [ "${DEV:-}" = "y" ] && "$PY" -m pip install -r requirements-dev.txt ;;
        8) "$PY" -m pytest tests/ -q ;;
        9) explorer.exe "$(cygpath -w "$ROOT/README.md" 2>/dev/null || echo "$ROOT/README.md")" 2>/dev/null \
           || echo "  文档: $ROOT/README.md" ;;
        0) exit 0 ;;
        *) echo "  无效选项" ;;
    esac
    echo
    read -r -p "回车返回菜单..." _
done

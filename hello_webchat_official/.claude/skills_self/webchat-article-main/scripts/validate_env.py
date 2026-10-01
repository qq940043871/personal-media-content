"""
环境校验脚本 — 检查 config/.env 中 ARK_API_KEY 是否配置，微信凭证是否可选就绪。

Exit codes:
  0: 校验通过
  1: 校验失败（必需项缺失）
"""
import os
import sys
from pathlib import Path

# 定位项目根（向上查找 config/settings.py）
_script_path = Path(__file__).resolve()
for _parent in _script_path.parents:
    if (_parent / "config" / "settings.py").exists():
        PROJECT_DIR = _parent
        break
else:
    PROJECT_DIR = _script_path.parent.parent.parent.parent.parent  # fallback
CONFIG_DIR = PROJECT_DIR / "config"
ENV_FILE = CONFIG_DIR / ".env"
SETTINGS_FILE = CONFIG_DIR / "settings.py"


def _check_file(path: Path, label: str) -> bool:
    ok = path.exists()
    print(f"  {label}: {'✅ 存在' if ok else '❌ 缺失'} ({path})")
    return ok


def _check_env_key(lines: list[str], key: str, label: str) -> bool:
    prefix = f"{key}="
    for line in lines:
        line = line.strip()
        if line.startswith(prefix):
            val = line[len(prefix):].strip().strip('"').strip("'")
            if val and val != "your_ark_api_key_here":
                print(f"  {label}: ✅ 已配置")
                return True
            print(f"  {label}: ❌ 值为空或占位符")
            return False
    print(f"  {label}: ❌ 未找到 {key}")
    return False


def validate():
    print("\n=== webchat-article-main: 环境校验 ===\n")

    # 1) 检查 config/.env 和 config/settings.py 是否存在
    print("[1/3] 配置文件检查")
    env_ok = _check_file(ENV_FILE, "config/.env")
    settings_ok = _check_file(SETTINGS_FILE, "config/settings.py")
    if not env_ok or not settings_ok:
        print("\n❌ 配置文件缺失，请创建 config/.env（参考 config/.env.example）")
        sys.exit(1)

    # 2) 读取 .env
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 3) 检查 ARK_API_KEY
    print("\n[2/3] 密钥检查")
    ark_ok = _check_env_key(lines, "ARK_API_KEY", "ARK_API_KEY")
    if not ark_ok:
        print("\n❌ ARK_API_KEY 未配置，请编辑 config/.env 填入有效密钥")
        sys.exit(1)

    # 4) 检查微信配置（可选，仅提示）
    print("\n[3/3] 微信配置（可选）")
    wechat_appid_ok = _check_env_key(lines, "WECHAT_APPID", "WECHAT_APPID")
    wechat_secret_ok = _check_env_key(lines, "WECHAT_APPSECRET", "WECHAT_APPSECRET")
    if wechat_appid_ok and wechat_secret_ok:
        print("  → 微信凭证已就绪，可发布到公众号")
    else:
        print("  → 微信凭证未配置，发布功能不可用（写作和配图不受影响）")

    print("\n✅ 环境校验通过")
    sys.exit(0)


if __name__ == "__main__":
    validate()

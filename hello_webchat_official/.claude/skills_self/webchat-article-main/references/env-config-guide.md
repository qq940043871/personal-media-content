# 环境配置指南

## 配置来源

本项目使用 Pydantic Settings 管理配置，定义在 `config/settings.py`。

## 密钥配置 (`config/.env`)

```ini
# 必需：火山方舟 API 密钥（用于写稿和配图）
ARK_API_KEY=your_ark_api_key_here

# 可选：微信发布（不填则无法发布到公众号）
WECHAT_APPID=your_wechat_appid
WECHAT_APPSECRET=your_wechat_appsecret

# 可选：调试开关
DEBUG=false
LOG_LEVEL=INFO
```

## 模型配置 (`config/settings.py`)

| 键 | 默认值 | 说明 |
|-----|--------|------|
| ARK_BASE_URL | `https://ark.cn-beijing.volces.com/api/v3` | 火山方舟 API 地址 |
| LLM_MODEL | `doubao-seed-2-0-pro-260215` | 写稿模型 |
| IMAGE_MODEL | `doubao-seedream-5-0-260128` | 配图模型 |

## 配置优先级

1. 环境变量（最高）
2. `config/.env` 文件
3. `config/settings.py` 默认值

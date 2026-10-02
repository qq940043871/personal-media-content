"""
模型 Provider 层 — 全仓模型凭据唯一存放处

- registry.py: 从 .env 的 PROVIDER_* 段解析各能力（chat/asr/image）的凭据
- llm.py / asr.py: 各能力客户端（旧路径 core/llm_client.py、core/asr_client.py 保留为兼容 shim）

换模型只需改根 .env 的注册表段，业务线无需改动。
"""

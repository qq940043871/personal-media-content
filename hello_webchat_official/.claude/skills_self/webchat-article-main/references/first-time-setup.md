# 首次引导

## 配置步骤

### 1. 创建 `config/.env`

复制模板：

```bash
cp config/.env.example config/.env
```

编辑 `config/.env`，填写：

```ini
ARK_API_KEY=你的火山方舟API密钥
WECHAT_APPID=你的微信公众号AppID
WECHAT_APPSECRET=你的微信公众号AppSecret
```

### 2. 验证配置

```bash
python -c "from config import get_settings; s=get_settings(); print('OK' if s.ARK_API_KEY and s.ARK_API_KEY != 'your_ark_api_key_here' else 'MISSING')"
```

### 3. 检查依赖

```bash
pip install -r requirements.txt
```

## 快速开始

```bash
# 交互式模式
python main.py

# 命令行模式
python main.py "你的文章主题" -p
```

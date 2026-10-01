# hello_webchat_solo — 公众号智能写作助手（独立程序）

Python 程序：主题 → 大纲 → 正文 → 封面 → 微信草稿。架构细节见 [CLAUDE.md](CLAUDE.md)。

## 目录地图

```
hello_webchat_solo/
├── README.md
├── CLAUDE.md                  # 程序架构与命令（权威技术说明）
├── main.py                    # CLI 入口
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── .env / .env.example
│   ├── article-writing.yaml
│   └── presets/               # 封面/格式/结构等预设
├── src/                       # agent 与流水线实现
└── tests/
```

> `output/`（生成文章）与运行产生的 `docs/` 为运行时目录，不入库；首次运行自动生成。

## 常用命令

```bash
pip install -r requirements.txt
cp config/.env.example config/.env   # 填入 API Key

python main.py                              # 交互模式
python main.py "LangGraph 多智能体开发实战"
python main.py "Transformer 注意力机制" -o article.md
python main.py "RAG 系统架构设计" -p       # 发布到微信草稿
```

## 产出位置

- 流水线产物：`output/<时间戳>_<主题>/`（`outline.md`、`draft.md`、`article.html`、`review.md`、`log.txt` 等；运行时生成，不入库）

## 与官方技能线的区别

| | hello_webchat_solo | hello_webchat_official |
|--|--------------------|------------------------|
| 形态 | 可安装 Python 程序 | Claude 技能包 + drafts |
| 入口 | `python main.py` | SKILL 工作流 |
| 配置 | `config/` | `.aws-article/` + `.claude/` |

## 文档

- 程序架构：[CLAUDE.md](CLAUDE.md)

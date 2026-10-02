"""
配置加载与元数据管理

从 Settings（统一入口）获取文章写作约束，
为每篇文章生成 article.yaml 元数据文件。
"""
import datetime
from pathlib import Path
from core.wechat_agent.config.settings import get_settings


def load_article_config() -> dict:
    """
    获取文章写作约束配置

    统一委托给 Settings.get_article_config()，
    后者从 config/article-writing.yaml 加载（合并 .env 默认值）。
    """
    return get_settings().get_article_config()


def save_article_metadata(article_dir: Path, metadata: dict):
    """保存文章元数据到 article.yaml"""
    try:
        import yaml
        yaml_path = article_dir / "article.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)
        print(f"[SAVE] 文章元数据已保存到: {yaml_path}")
    except Exception as e:
        print(f"[WARN] 保存元数据失败: {e}")


def load_default_metadata(title: str, config: dict) -> dict:
    """构建默认的文章元数据"""
    return {
        "title": title,
        "author": config.get("default_author", "AI技术专栏"),
        "publish_completed": False,
        "image_source": "generated",
        "article_category": config.get("article_category", "AI技术"),
        "target_reader": config.get("target_reader", ""),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
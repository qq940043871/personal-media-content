"""Agent 模块 — 配置驱动的微信公众号文章生成智能体"""
from .agent import WeChatArticleAgent, build_article_agent
from .state import ArticleState
from .config import load_article_config


def create_agent():
    """创建文章生成 Agent（同步接口），自动加载 .aws-article/config.yaml 配置"""
    return WeChatArticleAgent()


def create_publisher():
    """创建发布器（当前 Agent 内置发布功能，返回 None）"""
    return None


def get_config():
    """获取当前配置"""
    return load_article_config()


__all__ = [
    "WeChatArticleAgent",
    "ArticleState",
    "build_article_agent",
    "load_article_config",
    "create_agent",
    "create_publisher",
    "get_config",
]
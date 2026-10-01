"""
文章生成状态定义
"""

from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ArticleState(TypedDict):
    """文章生成状态

    属性说明：
        title: 文章标题
        article_type: 文章类型
        target_length: 目标字数
        include_code: 是否包含代码
        include_images: 是否插入配图

        config: 全局配置
        target_reader: 目标读者
        tone: 调性
        writing_style: 写作风格
        forbidden_words: 禁用词列表

        article_dir: 文章保存目录路径

        outline: 文章大纲
        content_markdown: Markdown 内容
        content_html: HTML 内容
        cover_image: 封面图 base64
        article_images: 文章配图列表

        review_result: 审稿结果
        media_id: 微信草稿 ID
        status: 当前状态
        error: 错误信息

        messages: 消息历史（用于 Agent 对话）
    """
    # 输入
    title: str
    article_type: str
    target_length: int
    include_code: bool
    include_images: bool

    # 配置
    config: dict
    target_reader: str
    tone: str
    writing_style: str
    forbidden_words: list

    # 文件保存
    article_dir: str

    # 中间状态
    outline: str
    content_markdown: str
    content_html: str
    cover_image: str
    article_images: list

    # 审稿结果
    review_result: dict

    # 输出
    media_id: str
    status: str
    error: str

    # 消息历史
    messages: Annotated[Sequence[BaseMessage], add_messages]
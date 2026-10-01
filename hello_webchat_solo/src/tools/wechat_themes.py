"""
微信公众号文章版面主题系统

提供 5 套预定义视觉主题，覆盖科技、极简、商务、清新等风格。
每个主题定义颜色、字体、间距、代码块、表格、标题等全套样式。
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class CodeBlockTheme:
    """代码块主题"""
    background: str = "#1e1e1e"
    text_color: str = "#d4d4d4"
    border_color: str = "#333333"
    lang_bar_bg: str = "#1e1e1e"
    lang_bar_text: str = "#d4d4d4"
    lang_bar_border: str = "#333333"
    line_font_size: str = "13px"


@dataclass
class HeadingTheme:
    """标题主题"""
    h1_color: str = "#1a202c"
    h1_font_size: str = "22px"
    h1_border_bottom: str = "2px solid #e2e8f0"
    h2_color: str = "#1a202c"
    h2_font_size: str = "20px"
    h2_bg: str = "#f7fafc"
    h2_border_left: str = "5px solid #2b6cb0"
    h3_color: str = "#1a202c"
    h3_font_size: str = "17px"
    h3_border_left: str = "4px solid #4299e1"
    h4_color: str = "#2d3748"
    h4_font_size: str = "15px"
    h4_border_left: str = "3px solid #a0aec0"


@dataclass
class TableTheme:
    """表格主题"""
    border_color: str = "#1a202c"
    header_bg: str = "#000000"
    header_text: str = "#ffffff"
    stripe_bg: str = "#f7fafc"
    cell_border: str = "#e2e8f0"
    cell_text: str = "#2d3748"


@dataclass
class InlineTheme:
    """行内元素主题"""
    strong_color: str = "#1a202c"
    code_bg: str = "#edf2f7"
    code_text: str = "#c53030"
    link_color: str = "#2b6cb0"
    bullet_color: str = "#4299e1"
    list_number_color: str = "#2b6cb0"


@dataclass
class LayoutTheme:
    """完整版面主题"""
    name: str = "默认科技蓝"
    description: str = "适合技术教程、原理分析类文章"

    # 外层容器
    section_bg: str = ""
    section_padding: str = "20px 16px"
    section_font_size: str = "15px"
    section_text_color: str = "#2d3748"

    # 段落
    paragraph_margin: str = "10px 0 14px"
    paragraph_line_height: str = "2"
    paragraph_font_size: str = "15px"
    paragraph_color: str = "#2d3748"

    # 空行
    empty_line_height: str = "6px"

    # 列表
    list_margin: str = "8px 0 16px 0"
    list_item_margin: str = "6px 0"
    list_item_color: str = "#2d3748"
    list_item_font_size: str = "15px"

    # 子主题
    code_block: CodeBlockTheme = field(default_factory=CodeBlockTheme)
    heading: HeadingTheme = field(default_factory=HeadingTheme)
    table: TableTheme = field(default_factory=TableTheme)
    inline: InlineTheme = field(default_factory=InlineTheme)

    # 封面渐变（用于默认封面图的 PIL 渲染）
    cover_gradient_start: str = "24,144,255"   # R,G,B
    cover_gradient_end: str = "114,46,209"      # R,G,B
    cover_bg_default: str = "#1a1a2e"

    # 引用块
    blockquote_bg: str = "#f7fafc"
    blockquote_border_left: str = "3px solid #4299e1"
    blockquote_color: str = "#4a5568"
    blockquote_padding: str = "12px 16px"


# ==================== 预置主题 ====================

THEMES: Dict[str, LayoutTheme] = {
    "tech-blue": LayoutTheme(
        name="默认科技蓝",
        description="适合技术教程、原理分析类文章。深色代码块 + 蓝色系标题/链接，专业感强。",
        heading=HeadingTheme(
            h2_border_left="5px solid #2b6cb0",
            h3_border_left="4px solid #4299e1",
            h4_border_left="3px solid #a0aec0",
        ),
        inline=InlineTheme(
            link_color="#2b6cb0",
            code_bg="#edf2f7",
            code_text="#c53030",
            bullet_color="#4299e1",
            list_number_color="#2b6cb0",
        ),
    ),

    "minimal-mono": LayoutTheme(
        name="极简黑白",
        description="适合深度观点、行业分析类文章。去掉所有装饰色，靠字号和间距区分层级。",
        section_text_color="#1a1a1a",
        paragraph_color="#1a1a1a",
        heading=HeadingTheme(
            h1_color="#000000",
            h1_font_size="24px",
            h1_border_bottom="2px solid #cccccc",
            h2_color="#000000",
            h2_font_size="20px",
            h2_bg="#f5f5f5",
            h2_border_left="5px solid #333333",
            h3_color="#000000",
            h3_font_size="17px",
            h3_border_left="4px solid #666666",
            h4_color="#1a1a1a",
            h4_font_size="15px",
            h4_border_left="3px solid #999999",
        ),
        code_block=CodeBlockTheme(
            background="#2d2d2d",
            text_color="#cccccc",
            border_color="#444444",
            lang_bar_bg="#2d2d2d",
            lang_bar_text="#cccccc",
            lang_bar_border="#444444",
        ),
        table=TableTheme(
            border_color="#333333",
            header_bg="#222222",
            header_text="#ffffff",
            stripe_bg="#f5f5f5",
            cell_border="#cccccc",
            cell_text="#1a1a1a",
        ),
        inline=InlineTheme(
            strong_color="#000000",
            code_bg="#e8e8e8",
            code_text="#333333",
            link_color="#333333",
            bullet_color="#333333",
            list_number_color="#333333",
        ),
    ),

    "warm-orange": LayoutTheme(
        name="温暖橙",
        description="适合实战分享、经验总结类文章。暖色调标题和强调色，营造轻松的阅读氛围。",
        heading=HeadingTheme(
            h1_border_bottom="2px solid #fbd38d",
            h2_border_left="5px solid #ed8936",
            h2_bg="#fffaf0",
            h3_border_left="4px solid #f6ad55",
            h4_border_left="3px solid #fbd38d",
        ),
        table=TableTheme(
            header_bg="#ed8936",
            header_text="#ffffff",
            stripe_bg="#fffaf0",
            cell_border="#fbd38d",
        ),
        inline=InlineTheme(
            strong_color="#c05621",
            code_bg="#fffaf0",
            code_text="#c05621",
            link_color="#dd6b20",
            bullet_color="#ed8936",
            list_number_color="#dd6b20",
        ),
        blockquote_bg="#fffaf0",
        blockquote_border_left="3px solid #fbd38d",
        cover_gradient_start="237,137,54",
        cover_gradient_end="197,65,30",
    ),

    "business-navy": LayoutTheme(
        name="商务深蓝",
        description="适合架构设计、技术规范、行业报告类正式文章。深蓝主色调，稳重专业。",
        heading=HeadingTheme(
            h1_border_bottom="2px solid #2a4365",
            h2_bg="#1a365d",
            h2_color="#ffffff",
            h2_border_left="5px solid #00a3c4",
            h3_border_left="4px solid #2c5282",
            h4_border_left="3px solid #4a5568",
        ),
        table=TableTheme(
            header_bg="#1a365d",
            header_text="#ffffff",
            stripe_bg="#ebf4ff",
            cell_border="#bee3f8",
        ),
        inline=InlineTheme(
            strong_color="#1a365d",
            code_bg="#ebf8ff",
            code_text="#2c5282",
            link_color="#2b6cb0",
            bullet_color="#2c5282",
            list_number_color="#2b6cb0",
        ),
        cover_gradient_start="26,54,93",
        cover_gradient_end="44,82,130",
    ),

    "fresh-green": LayoutTheme(
        name="清新绿",
        description="适合新手教程、入门指南类文章。绿色系主线，清晰明快，降低阅读压力。",
        heading=HeadingTheme(
            h1_border_bottom="2px solid #c6f6d5",
            h2_border_left="5px solid #38a169",
            h2_bg="#f0fff4",
            h3_border_left="4px solid #68d391",
            h4_border_left="3px solid #9ae6b4",
        ),
        code_block=CodeBlockTheme(
            background="#1a202c",
            text_color="#a0ffb8",
            border_color="#2d3748",
            lang_bar_bg="#1a202c",
            lang_bar_text="#a0ffb8",
            lang_bar_border="#2d3748",
        ),
        table=TableTheme(
            header_bg="#276749",
            header_text="#ffffff",
            stripe_bg="#f0fff4",
            cell_border="#c6f6d5",
        ),
        inline=InlineTheme(
            strong_color="#22543d",
            code_bg="#f0fff4",
            code_text="#22543d",
            link_color="#38a169",
            bullet_color="#38a169",
            list_number_color="#276749",
        ),
        cover_gradient_start="56,161,105",
        cover_gradient_end="39,103,73",
    ),
}


def get_theme(theme_name: str) -> LayoutTheme:
    """
    根据主题名获取版面主题。

    Args:
        theme_name: 主题标识，可选值:
            - "tech-blue"    默认科技蓝（默认）
            - "minimal-mono" 极简黑白
            - "warm-orange"  温暖橙
            - "business-navy" 商务深蓝
            - "fresh-green"  清新绿

    Returns:
        LayoutTheme 实例
    """
    if theme_name not in THEMES:
        available = ", ".join(THEMES.keys())
        print(f"⚠️ 未知主题 '{theme_name}'，使用默认主题。可选: {available}")
        return THEMES["tech-blue"]
    return THEMES[theme_name]


def list_themes():
    """列出所有可用主题"""
    print("\n可用微信公众号文章版面主题:\n")
    print(f"{'主题标识':<20} {'名称':<12} {'适用场景'}")
    print("-" * 70)
    for key, theme in THEMES.items():
        print(f"  {key:<18} {theme.name:<12} {theme.description}")
    print()

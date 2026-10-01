"""
LangGraph Agent 节点函数

每个节点对应文章生成管线中的一个步骤：
  generate_outline → write_article → review_article → convert_html
  → generate_cover → generate_article_images → publish_draft
"""
import datetime
import re
import base64
import traceback
from pathlib import Path
from typing import Literal

import requests

from config.settings import settings
from src.tools.doubao_llm import DoubaoLLMClient
from src.tools.generate_image import get_image_generator
from src.tools.html_converter import markdown_to_wechat_html
from src.tools.wechat_api import (
    get_wechat_access_token,
    upload_image_to_wechat,
    upload_thumb_media,
    add_wechat_draft,
)
from src.tools.cover_generator import _build_default_cover_bytes
from src.agents.state import ArticleState
from src.agents.config import load_article_config, save_article_metadata, load_default_metadata
from src.agents.utils import (
    get_article_dir,
    save_text_to_file,
    save_image,
    log_llm_response,
)


# ==================== 节点：生成大纲 ====================

async def generate_outline_node(state: ArticleState) -> dict:
    """节点：调用 Doubao LLM 生成文章大纲"""
    title = state["title"]
    config = state.get("config", {})
    target_reader = state.get("target_reader", config.get("target_reader", ""))
    article_category = config.get("article_category", "AI技术")

    status = f"正在为《{title}》生成大纲..."
    print(status)

    # 创建文章目录
    article_dir = get_article_dir(title)
    print(f"[DIR] 文章目录已创建: {article_dir}")

    # 保存文章元数据
    save_article_metadata(article_dir, load_default_metadata(title, config))

    try:
        client = DoubaoLLMClient()
        outline = client.generate(
            prompt=f'请为文章《{title}》生成一个详细的大纲。',
            system_prompt=f"""你是一位资深的公众号内容编辑，擅长规划{article_category}领域的技术长文。

目标读者：{target_reader}

请按以下标准结构生成大纲（Markdown 格式）：

## 摘要
一句话（80-128 字）概括文章核心价值，用于微信摘要展示。

## 开头（2-3 段）
选择一种切入方式：
- 提问式：直击痛点
- 场景式：故事引入
- 数据式：用数字说话
- 金句式：观点鲜明
- 直给式：教程/清单型

要求：前 3 句必须抓住读者注意力，禁止用「在当今社会」「随着科技的发展」等套话。

## 正文章节（3-5 个）
每个章节包含：
- 小标题（简洁有力，不超过 15 字）
- 3-5 个内容要点（用短句概括）
- 配图标记（在要点后标注 [图:类型：画面描述]）
- 建议字数分配

配图类型参考：封面、信息图、氛围、流程图、对比

要求：
- 每个章节独立成块，核心观点放段首
- 长短段交替，避免节奏单调

## 结尾（1-2 段）
选择一种收尾方式：总结型 / 金句型 / 行动号召型 / 互动型

## 文末区块
留一个引导关注的位置（分隔线 + 关注引导语）。""",
            temperature=0.5,
            max_tokens=2000,
            stream=True,
        )

        log_llm_response(outline, "文章大纲", article_dir)
        save_text_to_file(outline, article_dir / "outline.md", "文章大纲")

        return {"outline": outline, "article_dir": str(article_dir), "status": "大纲生成完成"}
    except Exception as e:
        traceback.print_exc()
        print(f"[ERR] 生成大纲失败: {e}")
        return {"error": f"生成大纲失败: {str(e)}", "status": "大纲生成失败"}


# ==================== 节点：撰写文章 ====================

async def write_article_node(state: ArticleState) -> dict:
    """节点：调用 Doubao LLM 撰写文章正文"""
    title = state["title"]
    outline = state.get("outline", "")
    article_type = state.get("article_type", "技术教程")
    target_length = state.get("target_length", 3000)
    include_code = state.get("include_code", True)
    article_dir = Path(state.get("article_dir", ""))
    config = state.get("config", {})

    target_reader = state.get("target_reader", config.get("target_reader", ""))
    tone = state.get("tone", config.get("tone", ""))
    writing_style = state.get("writing_style", config.get("writing_style", ""))
    forbidden_words = state.get("forbidden_words", config.get("forbidden_words", []))

    print(f"[WRITE] 正在撰写《{title}》...")

    try:
        client = DoubaoLLMClient()
        forbidden_str = "、".join(forbidden_words) if forbidden_words else "在当今社会、随着科技的发展、值得一提的是"

        system_prompt = f"""你是一位资深的技术写作专家，专注于大模型和智能体技术领域。

## 读者画像
目标读者：{target_reader}
调性：{tone}
写作风格：{writing_style}

## 写作规范（必须严格遵守）

### 用词规范
- 使用「」而非 ""
- 英文单词与中文之间加空格，如「使用 LangGraph 构建」
- 不用「的的」「了了」等重复虚词
- 数字用阿拉伯数字，如「3 个」而非「三个」（除成语外）

### 句式偏好
- 多用短句，单句不超过 40 字
- 多用主动语态，少用「被」字句

### 段落规范
- 每段不超过 5 行（手机阅读友好）
- 核心观点放段首
- 用例子/数据支撑观点，不空谈

### 标题规范
- 小标题简洁有力，不超过 15 字
- 不用「浅谈」「论」「之我见」等学术体

### 禁止事项（AI 味自检）
- 禁止使用：{forbidden_str}
- 不用「不是 X，而是 Y」超过 2 次
- 不用夸张承诺
- 不用模板化故事
- 不用翻译腔
- 不要面面俱到却不表态——要有明确观点
- 不要把普通技巧包装成宏大概念

### 文章结构
- 以 # 标题开头
- 每个 ## 章节标题下，内容独立成块
- 在需要配图的位置插入配图标记：![类型名：画面描述](placeholder)
- 结尾要有总结或行动号召
- 文末加一行「---」分隔线后写引导关注文字

输出格式：Markdown"""

        prompt = f"""请撰写一篇关于「{title}」的技术文章。

文章类型：{article_type}
目标字数：{target_length} 字左右
{"需要包含可运行的代码示例，代码要有注释说明" if include_code else "不需要代码示例，侧重原理和实践分析"}

参考大纲：
{outline}

要求：
1. 严格遵守写作规范（短段落、短句、口语化、避免 AI 味）
2. 开头必须在前 3 句抓住读者，不要用套话
3. 每个小标题下的内容要有具体例子或数据支撑
4. 在合适位置插入配图标记（每节至少一张）
5. 结尾要有明确的总结观点或行动号召
6. 文末加一行「---」分隔线后写引导关注文字

请直接输出文章内容，不要有额外说明。"""

        content = client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=8000,
            stream=True,
        )

        if article_dir:
            log_llm_response(content, "文章正文", article_dir)
            save_text_to_file(content, article_dir / "draft.md", "文章初稿")

        print(f"\n[STAT] 文章字数: {len(content)} 字符\n")
        return {"content_markdown": content, "status": "文章撰写完成"}
    except Exception as e:
        return {"error": f"撰写文章失败: {str(e)}", "status": "文章撰写失败"}


# ==================== 节点：审稿 ====================

async def review_article_node(state: ArticleState) -> dict:
    """节点：审稿检查（内容审）—— 禁用词、段落长度、配图标记、标题规范"""
    title = state["title"]
    content_markdown = state.get("content_markdown", "")
    article_dir = Path(state.get("article_dir", ""))
    config = state.get("config", {})
    forbidden_words = state.get("forbidden_words", config.get("forbidden_words", []))

    print(f"[CHECK] 正在审稿《{title}》...")

    issues = []

    # 1. 禁用词
    for word in forbidden_words:
        if word in content_markdown:
            issues.append({"level": "warning", "type": "禁用词", "message": f"发现禁用词「{word}」，建议替换"})

    # 2. 段落长度
    paragraphs = content_markdown.split('\n\n')
    long_paragraphs = [i + 1 for i, p in enumerate(paragraphs) if len(p) > 300 and not p.startswith('```') and not p.startswith('|')]
    if long_paragraphs:
        issues.append({"level": "warning", "type": "段落过长", "message": f"第 {', '.join(map(str, long_paragraphs))} 段超过 300 字，建议拆分"})

    # 3. 配图标记
    image_markers = re.findall(r'!\[.+?\]\(placeholder\)', content_markdown)
    if not image_markers:
        issues.append({"level": "warning", "type": "缺少配图", "message": "未发现配图标记，建议在合适位置添加 ![类型：描述](placeholder)"})

    # 4. 结尾分隔线
    if '---' not in content_markdown[-500:]:
        issues.append({"level": "warning", "type": "缺少结尾", "message": "文末缺少分隔线和引导关注"})

    # 5. 标题长度
    if len(title) > 30:
        issues.append({"level": "warning", "type": "标题过长", "message": f"标题 {len(title)} 字，建议控制在 15 字以内"})

    # 判断等级
    block_issues = [i for i in issues if i["level"] == "block"]
    review_level = "block" if block_issues else ("warning" if issues else "pass")

    review_result = {
        "level": review_level,
        "issues": issues,
        "total_issues": len(issues),
        "image_count": len(image_markers),
    }

    if issues:
        print(f"\n[LIST] 审稿发现 {len(issues)} 个问题：")
        for issue in issues:
            icon = "[BLOCK]" if issue["level"] == "block" else "[WARN]"
            print(f"  {icon} [{issue['type']}] {issue['message']}")
    else:
        print(f"[OK] 审稿通过，未发现问题")

    # 保存审稿记录
    if article_dir:
        review_text = f"# 审稿记录\n\n审稿时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n审稿结果：{review_level}\n\n"
        if issues:
            review_text += "## 问题清单\n\n"
            for issue in issues:
                review_text += f"- [{issue['level']}] {issue['type']}: {issue['message']}\n"
        else:
            review_text += "## 无问题\n"
        save_text_to_file(review_text, article_dir / "review.md", "审稿记录")

    if review_level == "block":
        return {"error": f"审稿未通过：{block_issues[0]['message']}", "review_result": review_result, "status": "审稿未通过"}

    return {"review_result": review_result, "status": "审稿完成"}


# ==================== 节点：转换为 HTML ====================

async def convert_to_html_node(state: ArticleState) -> dict:
    """节点：Markdown → 微信公众号兼容 HTML"""
    content_markdown = state.get("content_markdown", "")
    article_dir = Path(state.get("article_dir", ""))

    if not content_markdown:
        return {"error": "没有可转换的内容", "status": "转换失败"}

    print("[CONVERT] 正在转换为 HTML 格式...")

    try:
        # 去掉正文中第一个 # 标题（避免与微信文章标题重复）
        content_markdown_clean = re.sub(r'^# .+\n\n?', '', content_markdown, count=1, flags=re.MULTILINE)
        content_html = markdown_to_wechat_html(content_markdown_clean)

        if article_dir:
            save_text_to_file(content_html, article_dir / "article.html", "文章 HTML")

        return {"content_html": content_html, "status": "HTML 转换完成"}
    except Exception as e:
        return {"error": f"HTML 转换失败: {str(e)}", "status": "转换失败"}


# ==================== 节点：生成封面 ====================

async def generate_cover_node(state: ArticleState) -> dict:
    """节点：生成封面图（默认蓝紫渐变样式）"""
    title = state["title"]
    article_dir = Path(state.get("article_dir", ""))

    print(f"[IMAGE] 正在为《{title}》生成封面图（默认样式）...")

    try:
        cover_bytes = _build_default_cover_bytes(title)

        if article_dir:
            with open(str(article_dir / "cover.jpg"), "wb") as f:
                f.write(cover_bytes)
            print(f"[SAVE] 封面图 已保存到: {article_dir / 'cover.jpg'} ({len(cover_bytes)} bytes)")

        print(f"[OK] 封面图生成完成")
        return {"cover_image": "", "status": "封面图生成完成（默认样式）"}
    except Exception as e:
        print(f"[WARN] 封面图生成异常: {e}")
        return {"cover_image": "", "status": f"封面图生成失败: {str(e)}"}


# ==================== 节点：生成配图 ====================

async def generate_article_images_node(state: ArticleState) -> dict:
    """节点：生成 1 张文章配图并上传到微信"""
    title = state["title"]
    content_markdown = state.get("content_markdown", "")
    include_images = state.get("include_images", False)
    article_dir = Path(state.get("article_dir", ""))

    if not include_images:
        return {"article_images": [], "status": "跳过配图生成"}

    print(f"[IMAGE] 正在为《{title}》生成文章配图...")

    try:
        access_token = get_wechat_access_token(settings.WECHAT_APPID, settings.WECHAT_APPSECRET)

        content_lines = content_markdown.split('\n')
        first_part = '\n'.join(content_lines[:len(content_lines) // 3])

        prompt = f"""为技术文章生成配图。
文章标题：{title}
内容主题：{first_part[:200]}

设计要求：
- 科技风格，蓝色调，专业感
- 适合微信公众号文章配图（16:9比例）
- 突出技术主题，有视觉吸引力
- 简洁大气，避免文字"""

        generator = get_image_generator()
        print(f"  [1/1] 生成配图...")
        result = generator.generate(prompt, size="2K")

        if not result["success"]:
            print(f"  [WARN] 配图生成失败: {result.get('error')}")
            return {"article_images": [], "status": "配图生成失败"}

        image_data = None
        if result.get("b64_json"):
            image_data = base64.b64decode(result["b64_json"])
        elif result.get("url"):
            try:
                resp = requests.get(result["url"], timeout=30)
                image_data = resp.content
            except Exception as e:
                print(f"  [WARN] 下载配图失败: {e}")
                return {"article_images": [], "status": "配图下载失败"}

        if image_data is None:
            return {"article_images": [], "status": "配图数据为空"}

        if article_dir:
            save_image(image_data, article_dir / "image_1.png", "配图")

        print(f"  [1/1] 上传配图到微信...")
        try:
            image_url = upload_image_to_wechat(access_token, image_data)
            print(f"  [OK] 配图上传成功")
        except Exception as e:
            print(f"  [WARN] 上传配图失败: {e}")
            return {"article_images": [], "status": "配图上传失败"}

        return {"article_images": [{"url": image_url, "position": 1}], "status": "配图生成完成"}

    except Exception as e:
        print(f"[WARN] 配图生成异常: {e}")
        return {"article_images": [], "status": f"配图生成失败: {str(e)}"}


# ==================== 辅助：插入配图到 HTML ====================

def insert_images_into_html(content_html: str, article_images: list) -> str:
    """在 HTML 中第一段后插入配图"""
    if not article_images:
        return content_html

    paragraphs = re.findall(r'<p[^>]*>.*?</p>', content_html, re.DOTALL)
    if not paragraphs:
        return content_html

    first_img = article_images[0]
    img_url = first_img.get("url", "")
    if not img_url:
        return content_html

    target_para = paragraphs[0]
    img_html = (
        f'<p style="margin:20px 0;text-align:center;">'
        f'<img src="{img_url}" style="max-width:100%;height:auto;display:block;margin:0 auto;" />'
        f'</p>'
    )
    return content_html.replace(target_para, target_para + img_html, 1)


# ==================== 节点：发布到微信草稿箱 ====================

async def publish_draft_node(state: ArticleState) -> dict:
    """节点：上传封面 → 插入配图 → 发布到微信草稿箱"""
    title = state["title"]
    content_html = state.get("content_html", "")
    cover_image = state.get("cover_image", "")
    article_images = state.get("article_images", [])

    if not content_html:
        return {"error": "没有可发布的内容", "status": "发布失败"}

    print(f"[PUBLISH] 正在发布《{title}》到微信草稿箱...")

    try:
        if not settings.WECHAT_APPID or not settings.WECHAT_APPSECRET:
            print("[WARN] 微信公众号未配置，跳过发布")
            print("[HINT] 请在 config/.env 中配置 WECHAT_APPID 和 WECHAT_APPSECRET")
            return {"status": "跳过发布（未配置微信）"}

        # Step 1: 获取 access_token
        print("  [1/3] 获取 access_token...")
        access_token = get_wechat_access_token(settings.WECHAT_APPID, settings.WECHAT_APPSECRET)
        print("  [OK] access_token 获取成功")

        # Step 2: 上传封面图
        print("  [2/3] 上传封面图...")
        thumb_media_id = upload_thumb_media(access_token, cover_image, title)
        print(f"  [OK] 封面图上传成功 (media_id: {thumb_media_id[:20]}...)")

        # Step 3: 插入配图
        if article_images:
            print(f"  [配图] 插入{len(article_images)}张配图到文章...")
            content_html = insert_images_into_html(content_html, article_images)
            print(f"  [OK] 配图插入完成")

        # Step 4: 创建草稿
        print("  [3/3] 创建微信草稿...")
        media_id = add_wechat_draft(access_token, title, content_html, thumb_media_id, author="AI技术专栏")
        print(f"  [OK] 草稿创建成功!")

        return {"media_id": media_id, "status": "发布到微信草稿箱成功"}

    except Exception as e:
        return {"error": f"发布失败: {str(e)}", "status": "发布失败"}


# ==================== 条件边 ====================

def should_continue(state: ArticleState) -> Literal["continue", "error"]:
    """检查是否有错误"""
    if state.get("error"):
        return "error"
    return "continue"
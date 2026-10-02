"""
图像生成工具
使用豆包SeeDream模型生成文章配图
"""
import json
import requests
import base64
from typing import Optional, Dict, Any
from langchain.tools import tool
from core.wechat_agent.config import get_settings


class ImageGenerator:
    """图像生成器"""

    def __init__(self):
        self.settings = get_settings()

        # 优先级：settings.IMAGE_* > settings.ARK_*
        self.api_key = self.settings.IMAGE_API_KEY or self.settings.ARK_API_KEY
        self.base_url = self.settings.IMAGE_BASE_URL or self.settings.ARK_BASE_URL
        self.model = self.settings.IMAGE_MODEL

    def generate(
        self,
        prompt: str,
        size: str = "2K",
        watermark: bool = False
    ) -> Dict[str, Any]:
        """
        生成图像

        Args:
            prompt: 图像描述提示词
            size: 图像尺寸 (1K/2K/4K)
            watermark: 是否添加水印

        Returns:
            包含图像URL或base64数据的字典
        """
        # API端点 - 如果 base_url 已经包含 /images/generations，则不再拼接
        if self.base_url.endswith("/images/generations"):
            url = self.base_url
        else:
            url = f"{self.base_url}/images/generations"

        print(f"[CHECK] 图像生成调试信息:")
        print(f"   URL: {url}")
        print(f"   模型: {self.model}")
        print(f"   尺寸: {size}")
        print(f"   水印: {watermark}")
        print(f"   提示词长度: {len(prompt)}")
        print(f"   提示词前100字符: {prompt[:100]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求数据 - 按照豆包API文档（移除不支持的output_format）
        data = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "watermark": watermark
        }

        print(f"[UPLOAD] 请求数据: {json.dumps(data, ensure_ascii=False)}")

        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            print(f"[RESP] 响应状态码: {response.status_code}")
            
            # 打印响应内容用于调试
            response_text = response.text
            print(f"[RESP] 响应内容: {response_text[:500]}...")
            
            # 检查HTTP错误
            if response.status_code >= 400:
                try:
                    error_json = response.json()
                    error_msg = error_json.get('error', {}).get('message', response_text)
                except:
                    error_msg = response_text
                
                return {
                    "success": False,
                    "error": f"API请求失败 ({response.status_code}): {error_msg}"
                }
            
            result = response.json()
            print(f"[RESP] 解析后的响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

            # 解析响应，获取图像数据
            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0]
                b64_data = image_data.get("b64_json")
                url_data = image_data.get("url")
                
                if b64_data:
                    print(f"[OK] 收到Base64图像数据，长度: {len(b64_data)}")
                elif url_data:
                    print(f"[OK] 收到图像URL: {url_data}")
                
                return {
                    "success": True,
                    "url": url_data,
                    "b64_json": b64_data,
                    "revised_prompt": image_data.get("revised_prompt", prompt)
                }
            else:
                return {
                    "success": False,
                    "error": f"API返回数据格式异常: {result}"
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"图像生成请求失败: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理响应失败: {str(e)}"
            }


# 全局图像生成器实例
_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """获取图像生成器（单例）"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator


@tool
def generate_cover_image(title: str, style: str = "modern") -> str:
    """
    生成文章封面图

    Args:
        title: 文章标题
        style: 风格 (modern/minimal/tech/artistic)

    Returns:
        生成的封面图URL或base64数据
    """
    style_prompts = {
        "modern": "现代简约风格，科技感，渐变背景，专业商务感",
        "minimal": "极简主义，大量留白，单色或双色设计，优雅简洁",
        "tech": "科技风格，电路板纹理，蓝色调，未来感，数字化元素",
        "artistic": "艺术插画风格，创意构图，色彩丰富，视觉冲击力"
    }

    style_desc = style_prompts.get(style, style_prompts["modern"])

    prompt = f"""为技术文章生成封面图。

文章标题：{title}

设计要求：
- {style_desc}
- 适合微信公众号封面（900x383比例）
- 突出技术主题
- 专业、现代、有视觉吸引力
- 可以包含抽象的技术元素（代码、神经网络、数据流等）
- 标题区域留白，便于后期添加文字"""

    try:
        generator = get_image_generator()
        result = generator.generate(prompt, size="2K")

        if result["success"]:
            if result.get("url"):
                return f"封面图生成成功！\nURL: {result['url']}\n\n提示词: {result.get('revised_prompt', prompt)}"
            elif result.get("b64_json"):
                return f"封面图生成成功！\nBase64数据长度: {len(result['b64_json'])}\n\n提示词: {result.get('revised_prompt', prompt)}"
        else:
            return f"封面图生成失败: {result.get('error', '未知错误')}"

    except Exception as e:
        return f"生成封面图失败: {str(e)}"


@tool
def generate_article_image(description: str, image_type: str = "diagram") -> str:
    """
    生成文章配图（架构图、流程图等）

    Args:
        description: 图像内容描述
        image_type: 图像类型 (diagram/flowchart/architecture/concept)

    Returns:
        生成的图像URL或base64数据
    """
    type_prompts = {
        "diagram": "技术示意图，清晰的标注，专业配色，适合技术文档",
        "flowchart": "流程图，步骤清晰，箭头连接，逻辑分明，蓝白色调",
        "architecture": "系统架构图，分层展示，组件关系明确，专业技术风格",
        "concept": "概念示意图，抽象表达，视觉化呈现，易于理解"
    }

    type_desc = type_prompts.get(image_type, type_prompts["diagram"])

    prompt = f"""为技术文章生成配图。

内容描述：{description}

图像要求：
- {type_desc}
- 适合技术文章插图
- 清晰、专业、易于理解
- 中文标注（如需要）
- 高分辨率，细节清晰"""

    try:
        generator = get_image_generator()
        result = generator.generate(prompt, size="2K")

        if result["success"]:
            if result.get("url"):
                return f"配图生成成功！\nURL: {result['url']}\n\n提示词: {result.get('revised_prompt', prompt)}"
            elif result.get("b64_json"):
                return f"配图生成成功！\nBase64数据长度: {len(result['b64_json'])}\n\n提示词: {result.get('revised_prompt', prompt)}"
        else:
            return f"配图生成失败: {result.get('error', '未知错误')}"

    except Exception as e:
        return f"生成配图失败: {str(e)}"


@tool
def generate_image_from_markdown(article_content: str) -> str:
    """
    分析文章内容，自动提取配图需求并生成图像

    Args:
        article_content: 文章内容（Markdown格式）

    Returns:
        生成的图像列表及插入位置建议
    """
    import re

    # 提取 [配图：描述] 标记
    pattern = r'\[配图[：:]([^\]]+)\]'
    matches = re.findall(pattern, article_content)

    if not matches:
        return "文章中未找到配图标记，无需生成配图。"

    results = []
    generator = get_image_generator()

    for i, desc in enumerate(matches, 1):
        prompt = f"""为技术文章生成配图。

内容描述：{desc.strip()}

图像要求：
- 技术示意图风格
- 清晰、专业、易于理解
- 适合微信公众号文章
- 高分辨率"""

        try:
            result = generator.generate(prompt, size="2K")
            if result["success"]:
                if result.get("url"):
                    results.append(f"配图 {i}: {desc.strip()}\nURL: {result['url']}\n")
                elif result.get("b64_json"):
                    results.append(f"配图 {i}: {desc.strip()}\nBase64数据已生成\n")
            else:
                results.append(f"配图 {i}: {desc.strip()}\n生成失败: {result.get('error')}\n")
        except Exception as e:
            results.append(f"配图 {i}: {desc.strip()}\n生成失败: {str(e)}\n")

    return "\n".join(results)

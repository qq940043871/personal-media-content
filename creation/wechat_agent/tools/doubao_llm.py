"""
豆包大模型工具
支持文本生成、大纲生成、内容优化等功能
支持流式输出、自动重试、降级
"""
import json
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, List, Iterator
from langchain.tools import tool
from creation.wechat_agent.config import get_settings


class DoubaoLLMClient:
    """豆包大模型客户端 - 支持流式输出、自动重试、降级"""

    MAX_RETRIES = 3
    RETRY_BACKOFF = 2
    TIMEOUT = (10, 300)
    STREAM_TIMEOUT = (10, 180)

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.ARK_API_KEY
        self.base_url = self.settings.ARK_BASE_URL
        self.model = self.settings.LLM_MODEL
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        return session

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False
    ) -> str:
        """
        调用豆包大模型生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成token数
            stream: 是否使用流式输出

        Returns:
            生成的文本内容
        """
        if not stream:
            return self._generate_sync(prompt, system_prompt, temperature, max_tokens)

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                return self._generate_stream(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                err_msg = str(e)
                is_premature = "prematurely" in err_msg.lower() or "connection" in err_msg.lower()
                if not is_premature or attempt == self.MAX_RETRIES:
                    raise
                wait = self.RETRY_BACKOFF ** attempt
                print(f"\n[WARN] 流式传输中断 (第{attempt}/{self.MAX_RETRIES}次)，{wait}s 后重试...")
                time.sleep(wait)

        print("[WARN] 流式多次失败，降级为同步模式...")
        return self._generate_sync(prompt, system_prompt, temperature, max_tokens)

    def _generate_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """同步生成（非流式）"""
        url = f"{self.base_url}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = self._session.post(url, json=data, timeout=self.TIMEOUT)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"豆包API连接失败（网络不通或服务不可达）: {e}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"豆包API超时（请求耗时过长）: {e}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"豆包API返回错误 HTTP {e.response.status_code}: {e.response.text[:200]}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"豆包API请求失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"解析API响应失败: {str(e)}")

    def _generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """流式生成，实时输出到控制台"""
        url = f"{self.base_url}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        try:
            response = self._session.post(url, json=data, stream=True, timeout=self.STREAM_TIMEOUT)
            response.raise_for_status()

            print("\n" + "="*60)
            print("[BOT] AI 正在生成内容...")
            print("="*60 + "\n")

            full_content = []
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get('choices', [])
                            if not choices:
                                continue
                            delta = choices[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                print(content, end='', flush=True)
                                full_content.append(content)
                        except json.JSONDecodeError:
                            continue

            print("\n\n" + "="*60)
            print("[OK] 生成完成")
            print("="*60 + "\n")

            result = ''.join(full_content)
            if not result.strip():
                raise Exception("流式返回内容为空，可能是响应被截断")
            return result

        except requests.exceptions.ConnectionError as e:
            raise Exception(f"豆包API连接中断（Response ended prematurely）: {e}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"豆包API流式超时: {e}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"豆包API返回错误 HTTP {e.response.status_code}: {e.response.text[:200]}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"豆包API请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"流式生成失败: {str(e)}")

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> Iterator[str]:
        """
        流式生成，返回迭代器，可逐字获取内容

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成token数

        Yields:
            逐字生成的内容
        """
        url = f"{self.base_url}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        try:
            response = self._session.post(url, json=data, stream=True, timeout=self.STREAM_TIMEOUT)
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get('choices', [])
                            if not choices:
                                continue
                            delta = choices[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.ConnectionError as e:
            raise Exception(f"豆包API连接中断（Response ended prematurely）: {e}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"豆包API流式超时: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"豆包API请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"流式生成失败: {str(e)}")


# 全局客户端实例
_llm_client: Optional[DoubaoLLMClient] = None


def get_llm_client() -> DoubaoLLMClient:
    """获取LLM客户端（单例）"""
    global _llm_client
    if _llm_client is None:
        _llm_client = DoubaoLLMClient()
    return _llm_client


@tool
def generate_article_outline(topic: str, word_count: int = 2000) -> str:
    """
    根据主题生成文章大纲（流式输出）

    Args:
        topic: 文章主题
        word_count: 预计字数（默认2000字）

    Returns:
        文章大纲（Markdown格式）
    """
    system_prompt = """你是一位资深的技术内容策划专家，专注于大模型和智能体技术领域。
你的任务是为技术文章生成详细、专业的大纲。

大纲要求：
1. 结构清晰，包含引言、核心章节、总结
2. 技术深度适中，既有原理讲解又有实践指导
3. 每个章节标注预计字数
4. 包含代码示例的位置标记
5. 使用Markdown格式输出

输出格式示例：
# 文章标题

## 引言（约200字）
- 背景介绍
- 问题引出

## 核心章节1：XXX（约500字）
- 要点1
- 要点2
- 代码示例位置

## 总结（约200字）
- 核心观点回顾
- 展望与建议"""

    prompt = f"""请为以下主题生成详细的文章大纲：

主题：{topic}
预计总字数：{word_count}字

请确保大纲：
1. 覆盖该技术的核心概念和原理
2. 包含实际应用场景
3. 有代码示例的位置规划
4. 适合微信公众号的技术文章风格"""

    try:
        client = get_llm_client()
        outline = client.generate(prompt, system_prompt, temperature=0.7, stream=True)
        return outline
    except Exception as e:
        return f"生成大纲失败: {str(e)}"


@tool
def generate_article(title: str, outline: str, word_count: int = 2000) -> str:
    """
    根据大纲生成完整文章（流式输出）

    Args:
        title: 文章标题
        outline: 文章大纲
        word_count: 目标字数

    Returns:
        完整的文章内容（Markdown格式）
    """
    system_prompt = """你是一位资深的技术写作专家，专注于大模型和智能体技术领域。
你的任务是根据大纲撰写高质量的技术文章。

写作要求：
1. 语言专业但易懂，适合技术开发者阅读
2. 原理讲解清晰，配合图示说明位置
3. 代码示例完整、可运行，包含详细注释
4. 使用Markdown格式，支持微信公众号排版
5. 适当使用emoji增加可读性
6. 包含架构图、流程图的描述（用于后续生成配图）

代码规范：
- 使用代码块包裹，标注语言类型
- 关键行添加注释
- 提供完整的可运行示例
- 解释核心逻辑"""

    prompt = f"""请根据以下大纲撰写完整的技术文章：

标题：{title}

大纲：
{outline}

目标字数：{word_count}字

要求：
1. 严格按照大纲结构撰写
2. 每个技术概念都要有清晰解释
3. 包含2-3个完整的代码示例
4. 标注需要配图的位置（格式：[配图：描述]）
5. 文章结尾要有总结和思考题
6. 适合微信公众号发布（HTML兼容的Markdown）"""

    try:
        client = get_llm_client()
        article = client.generate(prompt, system_prompt, temperature=0.7, max_tokens=6000, stream=True)
        return article
    except Exception as e:
        return f"生成文章失败: {str(e)}"


@tool
def optimize_title(titles: List[str]) -> str:
    """
    优化文章标题，选择或生成最佳标题（流式输出）

    Args:
        titles: 候选标题列表

    Returns:
        优化后的最佳标题及理由
    """
    system_prompt = """你是一位资深的新媒体运营专家，擅长撰写吸引技术读者的标题。

标题优化原则：
1. 突出技术价值和实用性
2. 使用数字、对比等技巧增加吸引力
3. 避免标题党，保持专业性
4. 适合微信公众号传播
5. 长度控制在20-30字之间"""

    titles_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])

    prompt = f"""请从以下候选标题中选择或优化出最佳标题：

候选标题：
{titles_text}

请输出：
1. 最佳标题
2. 选择理由（从吸引力、专业性、传播性角度分析）
3. 如果有改进空间，提供优化建议"""

    try:
        client = get_llm_client()
        result = client.generate(prompt, system_prompt, temperature=0.8, stream=True)
        return result
    except Exception as e:
        return f"优化标题失败: {str(e)}"


@tool
def polish_content(content: str) -> str:
    """
    润色文章内容，优化表达和格式（流式输出）

    Args:
        content: 原始文章内容

    Returns:
        润色后的文章内容
    """
    system_prompt = """你是一位资深的技术编辑，专注于优化技术文章的可读性和专业性。

润色重点：
1. 优化技术术语的准确性
2. 改进句子结构，提升流畅度
3. 统一代码格式和注释风格
4. 检查逻辑连贯性
5. 保持Markdown格式规范
6. 适合微信公众号阅读体验"""

    prompt = f"""请润色以下技术文章内容：

原始内容：
{content}

润色要求：
1. 保持原意不变
2. 提升专业性和可读性
3. 优化代码注释
4. 检查并修正格式问题
5. 输出完整的润色后文章"""

    try:
        client = get_llm_client()
        polished = client.generate(prompt, system_prompt, temperature=0.5, max_tokens=6000, stream=True)
        return polished
    except Exception as e:
        return f"润色内容失败: {str(e)}"

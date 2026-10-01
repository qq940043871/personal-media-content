"""
LLM 客户端 — 通用大模型调用封装

提供：
- 同步/流式调用
- 统一的消息格式
- 错误处理与重试

使用方式：
    from core.llm_client import LLMClient
    llm = LLMClient()
    result = llm.chat("你好")
    result = llm.chat_stream("写一首诗")  # 边生成边打印
"""

import os
import json
import requests
from .config import config


class LLMClient:
    """通用 LLM 客户端 — 基于 OpenAI 兼容格式"""

    def __init__(self, api_key=None, api_url=None, model=None,
                 temperature=None, max_tokens=None, system_prompt=None):
        self.api_key = api_key or config.LLM_API_KEY
        self.api_url = api_url or config.LLM_API_URL
        self.model = model or config.LLM_MODEL
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self.system_prompt = system_prompt or '你是一个专业的AI助手。'

    def chat(self, prompt, system_prompt=None):
        """
        同步调用 LLM，返回完整文本

        Args:
            prompt: 用户输入
            system_prompt: 可选，覆盖默认系统提示

        Returns:
            str: 模型回复文本
        """
        payload = self._build_payload(prompt, system_prompt, stream=False)
        return self._call_sync(payload)

    def chat_stream(self, prompt, system_prompt=None):
        """
        流式调用 LLM，边生成边打印，最后返回完整文本

        Args:
            prompt: 用户输入
            system_prompt: 可选，覆盖默认系统提示

        Returns:
            str: 模型完整回复文本
        """
        payload = self._build_payload(prompt, system_prompt, stream=True)
        return self._call_stream(payload)

    def chat_messages(self, messages, stream=False):
        """
        直接传入 messages 数组调用（支持多轮对话）

        Args:
            messages: [{"role": "user"/"system"/"assistant", "content": "..."}]
            stream: 是否流式

        Returns:
            str: 模型回复文本
        """
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'stream': stream
        }
        if stream:
            return self._call_stream(payload)
        else:
            return self._call_sync(payload)

    # ---- 内部方法 ----

    def _build_payload(self, prompt, system_prompt, stream):
        return {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt or self.system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'stream': stream
        }

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _call_sync(self, payload):
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"[LLM] 调用失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[LLM] 响应内容: {e.response.text[:500]}")
            raise

    def _call_stream(self, payload):
        full_content = ""
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
                stream=True,
                timeout=300
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_content += content
                                print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.RequestException as e:
            print(f"\n[LLM] 流式调用失败: {e}")
            raise

        print()
        return full_content

    # ---- 便捷方法 ----

    def summarize(self, text, max_length=300):
        """文本摘要"""
        prompt = f"请对以下文本进行精简总结，控制在{max_length}字以内：\n\n{text}"
        return self.chat(prompt)

    def extract_keywords(self, text, count=10):
        """提取关键词，返回列表"""
        prompt = f"请从以下文本中提取{count}个最关键的关键词：\n\n{text}\n\n请以逗号分隔输出关键词。"
        result = self.chat(prompt)
        return [k.strip() for k in result.strip().split(',') if k.strip()]

    def generate_outline(self, text):
        """生成结构化大纲"""
        prompt = f"请根据以下文本内容，生成一个结构化的大纲：\n\n{text}"
        return self.chat(prompt)

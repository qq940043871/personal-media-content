"""
LLM 处理器 — 兼容层：在 core.LLMClient 基础上添加文章生成专用逻辑

旧代码 `from modules.llm_processor import LLMProcessor` 仍然可用。
新代码建议直接使用 `from core.llm_client import LLMClient`。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import LLMClient
from config import config


class LLMProcessor:
    """文章生成专用 LLM 处理器 — 基于 core.LLMClient 封装"""

    def __init__(self):
        self._client = LLMClient(
            system_prompt='你是一位专业的教育内容创作助手，擅长将语音转写内容整理成结构化的教学文章。'
        )
        self.api_key = config.LLM_API_KEY
        self.api_url = config.LLM_API_URL
        self.model = config.LLM_MODEL
        self.temperature = config.LLM_TEMPERATURE
        self.max_tokens = config.LLM_MAX_TOKENS

    # ---- 基础方法（直接委托）----

    def generate_article(self, transcript, video_info=None):
        prompt = self._build_article_prompt(transcript, video_info)
        result = self._client.chat(prompt)
        return {'success': True, 'article': result}

    def generate_summary(self, transcript, max_length=300):
        result = self._client.summarize(transcript, max_length)
        return {'success': True, 'summary': result.strip()}

    def generate_outline(self, transcript):
        result = self._client.generate_outline(transcript)
        return {'success': True, 'outline': result.strip()}

    def generate_keywords(self, transcript, count=10):
        keywords = self._client.extract_keywords(transcript, count)
        return {'success': True, 'keywords': keywords}

    # ---- 流式方法 ----

    def _generate_outline_stream(self, transcript):
        prompt = f"请根据以下文本内容，生成一个结构化的课程大纲：\n\n{transcript}"
        result = self._client.chat_stream(prompt)
        return {'success': True, 'outline': result.strip()}

    def _generate_keywords_stream(self, transcript, count=10):
        prompt = f"请从以下文本中提取{count}个最关键的关键词：\n\n{transcript}\n\n请以逗号分隔输出关键词。"
        result = self._client.chat_stream(prompt)
        keywords = [k.strip() for k in result.strip().split(',') if k.strip()]
        return {'success': True, 'keywords': keywords}

    def _generate_summary_stream(self, transcript, max_length=300):
        prompt = f"请对以下文本进行精简总结，控制在{max_length}字以内：\n\n{transcript}"
        result = self._client.chat_stream(prompt)
        return {'success': True, 'summary': result.strip()}

    # ---- 完整文章生成（4步流水线）----

    @staticmethod
    def _extract_transcript(video_data):
        """兼容 transcript / text 两种键名（旧调用方与测试脚本多用 'text'）"""
        transcript = (video_data.get('transcript') or video_data.get('text') or '').strip()
        if not transcript:
            raise ValueError(
                "转写文本为空（video_data 缺少 'transcript'/'text' 键或内容为空白）。"
                "拒绝在空输入上生成文章——空输入会让模型自由发挥或拒绝，产生看似成功的垃圾结果。")
        return transcript

    def generate_full_article(self, video_data):
        transcript = self._extract_transcript(video_data)
        frames = video_data.get('frames', [])
        video_info = video_data.get('video_info', {})

        outline_result = self.generate_outline(transcript)
        keywords_result = self.generate_keywords(transcript)
        summary_result = self.generate_summary(transcript)

        detailed_prompt = self._build_detailed_article_prompt({
            'transcript': transcript,
            'outline': outline_result['outline'],
            'keywords': keywords_result['keywords'],
            'summary': summary_result['summary'],
            'frame_count': len(frames),
            'duration': video_info.get('duration', 0)
        })

        article_result = self._client.chat(detailed_prompt)

        return {
            'success': True,
            'article': article_result,
            'summary': summary_result['summary'],
            'outline': outline_result['outline'],
            'keywords': keywords_result['keywords']
        }

    def generate_full_article_stream(self, video_data, save_path=None):
        """流式生成完整文章（4步流水线，边生成边打印）"""
        transcript = self._extract_transcript(video_data)
        frames = video_data.get('frames', [])
        video_info = video_data.get('video_info', {})

        print("[1/4] 正在生成大纲...")
        outline_result = self._generate_outline_stream(transcript)
        print("\n[2/4] 正在提取关键词...")
        keywords_result = self._generate_keywords_stream(transcript)
        print("\n[3/4] 正在生成摘要...")
        summary_result = self._generate_summary_stream(transcript)

        detailed_prompt = self._build_detailed_article_prompt({
            'transcript': transcript,
            'outline': outline_result['outline'],
            'keywords': keywords_result['keywords'],
            'summary': summary_result['summary'],
            'frame_count': len(frames),
            'duration': video_info.get('duration', 0)
        })

        print("\n[4/4] 正在生成文章（流式输出）...\n")
        article_result = self._client.chat_stream(detailed_prompt)

        if save_path and article_result:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(article_result)
            print(f"文章已保存: {save_path}")

        print("\n========== 文章生成完成 ==========\n")

        return {
            'success': True,
            'article': article_result,
            'summary': summary_result['summary'],
            'outline': outline_result['outline'],
            'keywords': keywords_result['keywords']
        }

    def save_article_to_file(self, article_data, filename=None, output_dir=None, video_name=None):
        if not article_data or not article_data.get('success'):
            print(f"[save_article_to_file] 跳过: success={article_data.get('success') if article_data else 'None'}")
            return None

        article_content = article_data.get('article', '')
        if not article_content or not article_content.strip():
            print(f"[save_article_to_file] 文章内容为空，跳过保存")
            return None

        if output_dir is None:
            if video_name:
                output_dir = config.get_video_articles_dir(video_name)
            else:
                output_dir = config.OUTPUT_ARTICLES_DIR if hasattr(config, 'OUTPUT_ARTICLES_DIR') else './articles'

        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"article_{timestamp}.md"

        if not filename.endswith('.md'):
            filename += '.md'

        output_path = os.path.join(output_dir, filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article_content)

        print(f"文章已保存: {output_path}")
        return output_path

    def batch_generate_articles(self, transcripts):
        results = []

        for transcript_data in transcripts:
            video_name = transcript_data.get('video_name')
            print(f"\n正在生成文章: {video_name or transcript_data.get('audio_path', 'unknown')}")
            try:
                save_path = None
                if video_name:
                    from pathlib import Path
                    base_name = Path(video_name).name
                    save_path = os.path.join(config.get_video_articles_dir(video_name), f"{base_name}.md")

                result = self.generate_full_article_stream({
                    'transcript': transcript_data.get('text', ''),
                    'frames': transcript_data.get('frames', []),
                    'video_info': transcript_data.get('video_info', {})
                }, save_path=save_path)
                results.append({
                    'audio_path': transcript_data.get('audio_path'),
                    'video_name': video_name,
                    **result
                })
            except Exception as e:
                print(f"文章生成失败: {e}")
                results.append({
                    'audio_path': transcript_data.get('audio_path'),
                    'success': False,
                    'error': str(e)
                })

        return results

    # ---- 内部提示词构建 ----

    def _build_article_prompt(self, transcript, video_info):
        duration = video_info.get('duration', 0) if video_info else 0
        duration_str = f"视频时长约{round(duration / 60)}分钟。" if duration else ""

        return f"""你是一位专业的教育内容编辑。请根据以下语音转写文本，将其整理成一篇结构清晰、内容详实的教学文章。

{duration_str}

原始文本：
{transcript}

要求：
1. 文章结构清晰，包含标题、多个章节、小节
2. 内容详实，保留所有重要知识点
3. 使用Markdown格式
4. 语言正式、专业，但易于理解
5. 可以适当补充必要的解释和说明

请输出完整的文章内容："""

    def _build_detailed_article_prompt(self, data):
        return f"""你是一位专业的教育内容编辑。请根据以下信息，撰写一篇高质量的教学文章。

文章大纲：
{data['outline']}

关键词：{','.join(data['keywords'])}

核心摘要：{data['summary']}

详细内容：
{data['transcript']}

要求：
1. 严格按照大纲结构组织内容
2. 文章开头要有引人入胜的引言
3. 每个章节内容详实，逻辑清晰
4. 使用Markdown格式
5. 语言正式专业，适合教学场景
6. 可以适当添加示例和解释

请输出完整的教学文章："""

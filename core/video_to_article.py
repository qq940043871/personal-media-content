"""
视频→文章流水线 — 教学视频抽帧/转写/成文的一体化编排

定位：core 对内能力层（原 hello_feishu 教学视频流水线，2026-10 并入主工程；
包装层 video/asr/llm_processor 已消除，直接使用 providers 客户端）。

用法：
    python media-cli.py pipeline video-article                 # 批量处理 system/storage/videos_input
    python media-cli.py pipeline video-article --video x.mp4   # 单个视频
    python media-cli.py pipeline video-article --input-dir <目录>

示例（模块方式）：
    from core.video_to_article import VideoToArticlePipeline, VideoArticleGenerator
    VideoToArticlePipeline().run()
    gen = VideoArticleGenerator()
    result = gen.generate_full_article({'text': '转写文本', 'frames': []})

输出：
    system/storage/videos_output/<video>/{frames,audio,audio_txt,articles}；
    抽帧→音频→转写→成文 四步各自断点续跑（已有产物自动跳过）

依赖：
    FFmpeg（FFMPEG_PATH）；ASR/LLM 走根 .env 的 Provider 注册表
"""

import os
import sys
from pathlib import Path

from .config import config
from .video_toolkit import VideoToolkit
from .providers.asr import ASRClient
from .providers.llm import LLMClient


# ===== 视频关键帧配图（供飞书等图文发布使用）=====

def get_video_frames(video_name, frames_dir=None, max_frames=5):
    """获取视频关键帧列表（用于文章配图）"""
    if frames_dir is None:
        frames_dir = config.get_video_frames_dir(video_name)

    pattern = os.path.join(frames_dir, f"{video_name}_keyframe_*.jpg")
    import glob
    frames = sorted(glob.glob(pattern))

    if not frames:
        return []

    if len(frames) <= max_frames:
        return frames

    step = len(frames) // max_frames
    return [frames[i] for i in range(0, len(frames), step)][:max_frames]


def generate_article_images(video_name, frames_dir=None, max_frames=5):
    """生成文章配图数据结构（供 FeishuPublisher.insert_images_batch 使用）"""
    frames = get_video_frames(video_name, frames_dir, max_frames)

    images = []
    for i, frame_path in enumerate(frames):
        images.append({
            'path': frame_path,
            'caption': f"视频关键帧 {i + 1}",
            'selection': None
        })

    return images


def save_transcript(audio_path, transcript, video_name=None, output_dir=None):
    """转写结果落盘（audio_txt/<音频名>.txt）；video_name 给定时用其产物目录"""
    if not transcript or not transcript.get('success'):
        return None

    if output_dir is None:
        if video_name:
            output_dir = config.get_video_audio_txt_dir(video_name)
        else:
            output_dir = os.path.join(os.path.dirname(audio_path), 'audio_txt')
    os.makedirs(output_dir, exist_ok=True)

    audio_filename = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join(output_dir, f"{audio_filename}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(transcript.get('text', ''))

    print(f"转写结果已保存: {output_path}")
    return output_path


# ===== 文章生成（大纲→关键词→摘要→成文 四步）=====

class VideoArticleGenerator:
    """教学文章生成器 — 基于 LLMClient 的教育内容四步生成"""

    def __init__(self, client=None):
        self._client = client or LLMClient(
            system_prompt='你是一位专业的教育内容创作助手，擅长将语音转写内容整理成结构化的教学文章。'
        )

    # ---- 基础生成 ----

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

    # ---- 流式生成 ----

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

    # ---- 完整文章生成（四步流水线）----

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
        """流式生成完整文章（四步流水线，边生成边打印）"""
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
            os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
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
            print("[save_article_to_file] 文章内容为空，跳过保存")
            return None

        if output_dir is None:
            output_dir = (config.get_video_articles_dir(video_name) if video_name
                          else config.STORAGE_ARTICLES)
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
                    base_name = Path(video_name).name
                    save_path = os.path.join(config.get_video_articles_dir(video_name),
                                             f"{base_name}.md")

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

    # ---- 提示词 ----

    @staticmethod
    def _build_article_prompt(transcript, video_info):
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

    @staticmethod
    def _build_detailed_article_prompt(data):
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


# ===== 流水线编排（抽帧→音频→转写→成文，断点续跑）=====

class VideoToArticlePipeline:
    """教学视频→文章流水线编排"""

    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

    def __init__(self, generator=None):
        self.toolkit = VideoToolkit()
        self.asr = ASRClient()
        self.generator = generator or VideoArticleGenerator()

    # ---- 步骤状态 ----

    @staticmethod
    def get_video_files(input_dir):
        """递归获取所有视频文件，返回 (绝对路径, 相对路径) 列表"""
        video_files = []
        for root, _dirs, files in os.walk(input_dir):
            for f in files:
                if f.lower().endswith(VideoToArticlePipeline.VIDEO_EXTENSIONS):
                    abs_path = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_path, input_dir)
                    video_files.append((abs_path, rel_path))
        return video_files

    @staticmethod
    def get_existing_frames(video_name):
        """获取已存在的帧文件列表（帧前缀用 video_name 的末段）"""
        frames_dir = config.get_video_frames_dir(video_name)
        frame_prefix = Path(video_name).name
        frames = []
        if os.path.exists(frames_dir):
            frame_files = [f for f in os.listdir(frames_dir)
                           if f.startswith(frame_prefix) and f.endswith('.jpg')]
            frame_files.sort()
            frames = [os.path.join(frames_dir, f) for f in frame_files]
        return frames

    @staticmethod
    def check_step_status(video_name):
        """检查视频各处理步骤的完成状态（用于断点续跑）"""
        frames_dir = config.get_video_frames_dir(video_name)
        frame_prefix = Path(video_name).name
        frames_exist = (os.path.exists(frames_dir)
                        and len([f for f in os.listdir(frames_dir)
                                 if f.startswith(frame_prefix) and f.endswith('.jpg')]) > 0)

        base_name = Path(video_name).name
        audio_path = os.path.join(config.get_video_audio_dir(video_name), f"{base_name}.mp3")
        audio_exist = os.path.exists(audio_path)

        txt_path = os.path.join(config.get_video_audio_txt_dir(video_name), f"{base_name}.txt")
        txt_exist = os.path.exists(txt_path)

        article_path = os.path.join(config.get_video_articles_dir(video_name), f"{base_name}.md")
        article_exist = os.path.exists(article_path)

        return {
            'frames_done': frames_exist,
            'audio_done': audio_exist,
            'txt_done': txt_exist,
            'article_done': article_exist,
            'all_done': frames_exist and audio_exist and txt_exist and article_exist
        }

    # ---- 三阶段 ----

    def run(self, input_dir=None, video_path=None):
        """
        运行完整流水线（批量目录或单个视频）

        Returns:
            dict: {'videos': int, 'transcribed': int, 'articles': int, ...}
        """
        print('=== 教学视频分析与文章生成流水线 ===\n')
        config.ensure_base_directories()

        # 1/3 抽帧 + 抽音
        print('1/3 开始处理视频...')
        video_results = []
        if video_path:
            rel = os.path.basename(video_path)
            files_with_rel = [(video_path, rel)]
        else:
            input_dir = input_dir or config.STORAGE_VIDEO_INPUT
            files_with_rel = self.get_video_files(input_dir)

        skipped_frames = skipped_audio = 0
        for video_file, video_rel_path in files_with_rel:
            video_name = os.path.splitext(video_rel_path)[0]
            step_status = self.check_step_status(video_name)
            config.ensure_video_directories(video_name)

            if step_status['frames_done']:
                print(f"跳过已提取帧: {video_name}")
                frames_result = {'success': True, 'frames': self.get_existing_frames(video_name),
                                 'frame_count': len(self.get_existing_frames(video_name))}
                skipped_frames += 1
            else:
                print(f"提取帧: {video_name}")
                frames_result = self.toolkit.extract_key_frames(
                    video_file, config.get_video_frames_dir(video_name))

            base_name = Path(video_name).name
            audio_path = os.path.join(config.get_video_audio_dir(video_name), f"{base_name}.mp3")
            if step_status['audio_done']:
                print(f"跳过已提取音频: {video_name}")
                audio_result = {'success': True, 'audio_path': audio_path}
                skipped_audio += 1
            else:
                print(f"提取音频: {video_name}")
                audio_result = self.toolkit.extract_audio(
                    video_file, config.get_video_audio_dir(video_name))

            video_results.append({
                'video_path': video_file,
                'video_name': video_name,
                'video_info': self.toolkit.get_info(video_file),
                'frames': frames_result.get('frames', []),
                'frame_count': frames_result.get('frame_count', 0),
                'audio_path': audio_result.get('audio_path'),
                'success': frames_result.get('success') and audio_result.get('success')
            })

        success_videos = [r for r in video_results if r.get('success')]
        print(f"\n视频处理完成: {len(success_videos)}/{len(files_with_rel)} 个视频")
        if skipped_frames:
            print(f"跳过已提取帧: {skipped_frames} 个")
        if skipped_audio:
            print(f"跳过已提取音频: {skipped_audio} 个")

        # 2/3 转写
        print('2/3 开始语音转写...')
        need_transcribe = []
        success_asr = []
        for video_result in success_videos:
            video_name = video_result['video_name']
            base_name = Path(video_name).name
            txt_path = os.path.join(config.get_video_audio_txt_dir(video_name), f"{base_name}.txt")
            if os.path.exists(txt_path):
                print(f"跳过已转写: {video_name}")
                with open(txt_path, 'r', encoding='utf-8') as f:
                    success_asr.append({'audio_path': video_result['audio_path'],
                                        'text': f.read(), 'video_name': video_name,
                                        'success': True})
            else:
                need_transcribe.append(video_result['audio_path'])

        asr_results = self.asr.batch_transcribe(need_transcribe)
        audio_to_video = {v['audio_path']: v for v in success_videos}
        newly_transcribed = 0
        for audio_path, asr_result in zip(need_transcribe, asr_results):
            if asr_result.get('success'):
                video_name = audio_to_video.get(audio_path, {}).get(
                    'video_name', Path(audio_path).stem)
                save_transcript(audio_path, asr_result, video_name=video_name)
                success_asr.append({**asr_result, 'video_name': video_name})
                newly_transcribed += 1

        print(f"\n语音转写完成: {len(success_asr)}/{len(success_videos)} 个音频")
        print(f"新转写: {newly_transcribed} 个")

        # 3/3 成文
        print('3/3 开始生成文章...')
        article_inputs = []
        for asr_result in success_asr:
            video_result = next((v for v in success_videos
                                 if v['video_name'] == asr_result.get('video_name')), None)
            article_inputs.append({
                'audio_path': asr_result['audio_path'],
                'text': asr_result['text'],
                'frames': video_result.get('frames', []) if video_result else [],
                'video_info': video_result.get('video_info', {}) if video_result else {},
                'video_name': video_result.get('video_name') if video_result else None
            })

        need_generate = []
        skipped_articles = 0
        for input_data in article_inputs:
            video_name = input_data.get('video_name')
            base_name = Path(video_name).name
            article_path = os.path.join(config.get_video_articles_dir(video_name), f"{base_name}.md")
            if not os.path.exists(article_path):
                need_generate.append(input_data)
            else:
                print(f"跳过已生成: {video_name}")
                skipped_articles += 1

        article_results = self.generator.batch_generate_articles(need_generate)
        new_articles = len([r for r in article_results if r.get('success')])

        print(f"\n文章生成完成: {new_articles}/{len(article_inputs)} 篇文章")
        if skipped_articles:
            print(f"跳过已生成: {skipped_articles} 篇")

        print('\n=== 处理流程全部完成 ===')
        return {
            'videos': len(success_videos),
            'transcribed': newly_transcribed,
            'articles': new_articles,
            'skipped': {'frames': skipped_frames, 'audio': skipped_audio,
                        'articles': skipped_articles},
        }

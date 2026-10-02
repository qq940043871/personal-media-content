"""
小说章节 → 视频分镜脚本 转换器

功能：
- 从小说章节中提取高光场景
- 生成标准化的视频分镜脚本（含画面描述、镜头语言、配乐提示）
- 支持多种视频风格（科幻/都市/古风/玄幻/悬疑等）
- 输出分镜提示词，可直接用于 AI 视频生成

使用方式：
    from core.story_to_script import StoryToScript
    converter = StoryToScript()
    result = converter.chapter_to_script(chapter_text, style='玄幻')

    # 输出：分镜列表 + 完整脚本 + AI生成提示词
    print(result['shots'])
    print(result['full_script'])
    print(result['prompt_list'])
"""

import os
import re
from .llm_client import LLMClient


class StoryToScript:
    """小说章节 → 视频分镜脚本 转换器"""

    # 预置视频风格
    STYLES = {
        '玄幻': {
            'visual': '电影级画质，IMAX 3D效果，仙侠玄幻风格，仙气缭绕，光影梦幻',
            'color': '紫金/青蓝/月白 高对比，饱和度高，光晕效果',
            'camera': '大远景展现世界观，特写突出人物表情，慢动作表现功法释放',
            'music': '古风史诗配乐，古筝+笛子+管弦乐团，节奏随剧情起伏',
        },
        '科幻': {
            'visual': '电影级画质，IMAX70mm胶片感，赛博朋克/科幻风格，霓虹灯光',
            'color': '冷蓝+霓虹粉紫 高对比，金属质感，全息投影光效',
            'camera': '低角度仰拍显压迫，手持镜头增紧张，无人机视角展场景',
            'music': '电子合成器配乐，低沉贝斯+科技感音效，紧张节奏',
        },
        '都市': {
            'visual': '电影级画质，自然光感，写实都市风格，生活化场景',
            'color': '暖黄+冷蓝 日常色调，柔和光影，氛围感强',
            'camera': '中景对话为主，跟拍镜头代入感，空镜转场',
            'music': '钢琴+弦乐 抒情配乐，节奏舒缓，情感饱满',
        },
        '悬疑': {
            'visual': '电影级画质，低照度，悬疑暗黑风格，阴影厚重',
            'color': '低饱和，灰绿/暗红 色调对比，大量阴影隐藏信息',
            'camera': '倾斜镜头显不安，特写放大细节，慢推镜头增紧张',
            'music': '悬疑配乐，低频音效+心跳声，留白制造恐惧',
        },
        '古风': {
            'visual': '电影级画质，国风工笔风格，水墨晕染，古典美学',
            'color': '朱砂/月白/青黛 传统配色，柔和光影，意境悠远',
            'camera': '对称构图，远景展山水，近景拍细节，慢节奏',
            'music': '纯古风配乐，古琴+箫+琵琶，悠扬婉转',
        },
        '末日废土': {
            'visual': '电影级画质，60年代复古科幻风，末日废土场景，强光烈日',
            'color': '暖橙+冷蓝 高对比，画面质感强烈，破败美学',
            'camera': '低角度跟拍，远景展废墟，特写显细节',
            'music': '工业摇滚+电子混合，低沉有力，末日氛围',
        },
    }

    def __init__(self, llm_client=None, style='玄幻'):
        self.llm = llm_client or LLMClient(
            system_prompt='你是一位资深影视编剧和分镜师，擅长将小说内容转化为专业的视频分镜脚本。'
        )
        self.style = style

    def chapter_to_script(self, chapter_text, style=None, num_shots=8, title=''):
        """
        将小说章节转换为视频分镜脚本

        Args:
            chapter_text: 小说章节正文
            style: 视频风格（玄幻/科幻/都市/悬疑/古风/末日废土），默认用初始化时的风格
            num_shots: 分镜数量，默认8个
            title: 章节标题（可选，用于生成更准确的脚本）

        Returns:
            dict: {
                'success': bool,
                'title': str,
                'style': str,
                'shots': [{'shot_num': int, 'shot_type': str, 'description': str,
                           'characters': str, 'scene': str, 'camera': str,
                           'duration': str, 'prompt': str}],
                'full_script': str,
                'prompt_list': [str],
                'summary': str,
            }
        """
        style = style or self.style
        style_config = self.STYLES.get(style, self.STYLES['玄幻'])

        print(f"[Story→Script] 正在生成分镜脚本 (风格: {style}, 分镜数: {num_shots})...")

        # 第一步：提取章节高光场景
        print("[Story→Script] 步骤 1/3: 分析章节，提取高光场景...")
        highlights = self._extract_highlights(chapter_text, title, num_shots)

        # 第二步：生成详细分镜
        print("[Story→Script] 步骤 2/3: 生成详细分镜脚本...")
        shots = self._generate_shots(highlights, style_config, num_shots)

        # 第三步：生成AI视频提示词
        print("[Story→Script] 步骤 3/3: 生成AI视频生成提示词...")
        prompt_list = self._generate_prompts(shots, style_config)

        # 组装完整脚本
        full_script = self._format_full_script(title or '未命名章节', style, shots, style_config)

        print(f"[Story→Script] 生成完成！共 {len(shots)} 个分镜")

        return {
            'success': True,
            'title': title,
            'style': style,
            'shots': shots,
            'full_script': full_script,
            'prompt_list': prompt_list,
            'summary': highlights.get('summary', ''),
        }

    def batch_chapters_to_script(self, chapters, style=None, num_shots=8):
        """
        批量处理多个章节

        Args:
            chapters: [{'title': str, 'content': str}, ...]
            style: 视频风格
            num_shots: 每章分镜数

        Returns:
            list: 每个章节的结果
        """
        results = []
        for i, ch in enumerate(chapters, 1):
            print(f"\n[Story→Script] 处理第 {i}/{len(chapters)} 章: {ch.get('title', '')}")
            try:
                result = self.chapter_to_script(
                    ch['content'],
                    style=style,
                    num_shots=num_shots,
                    title=ch.get('title', '')
                )
                results.append(result)
            except Exception as e:
                print(f"[Story→Script] 失败: {e}")
                results.append({'success': False, 'title': ch.get('title', ''), 'error': str(e)})
        return results

    # ---- 内部方法 ----

    def _extract_highlights(self, text, title, num_shots):
        """提取章节高光场景"""
        # 截取前 N 字，避免 token 超限（保留开头和结尾）
        max_len = 8000
        if len(text) > max_len:
            # 保留前 60% 和后 40%
            split_point = int(max_len * 0.6)
            text = text[:split_point] + "\n...(中间省略)...\n" + text[-(max_len - split_point):]

        prompt = f"""你是一位资深影视编剧。请从以下小说章节中提取最适合视频化的 {num_shots} 个高光场景。

章节标题：{title}

章节内容：
{text}

要求：
1. 选择 {num_shots} 个最有视觉冲击力、最能推动剧情的关键场景
2. 每个场景包含：场景概述、出场人物、环境地点、情绪氛围
3. 按时间顺序排列
4. 场景之间要有逻辑关联，能串联成完整的叙事线

请按以下格式输出（严格按格式，不要添加额外文字）：

【摘要】
（一句话概括本章核心内容）

【场景1】
概述：...
人物：...
地点：...
情绪：...

【场景2】
...
"""

        result = self.llm.chat(prompt)
        return self._parse_highlights(result)

    def _parse_highlights(self, text):
        """解析高光场景输出"""
        result = {'summary': '', 'scenes': []}

        # 提取摘要
        summary_match = re.search(r'【摘要】\s*\n(.+?)(?=\n【场景|\Z)', text, re.DOTALL)
        if summary_match:
            result['summary'] = summary_match.group(1).strip()

        # 提取场景
        scene_pattern = re.compile(r'【场景\d+】\s*\n(.+?)(?=\n【场景|\Z)', re.DOTALL)
        for match in scene_pattern.finditer(text):
            scene_text = match.group(1).strip()
            scene = {}
            for line in scene_text.split('\n'):
                line = line.strip()
                if line.startswith('概述：'):
                    scene['description'] = line[3:].strip()
                elif line.startswith('人物：'):
                    scene['characters'] = line[3:].strip()
                elif line.startswith('地点：'):
                    scene['location'] = line[3:].strip()
                elif line.startswith('情绪：'):
                    scene['mood'] = line[3:].strip()
            if scene:
                result['scenes'].append(scene)

        return result

    def _generate_shots(self, highlights, style_config, num_shots):
        """生成详细分镜"""
        scenes_text = '\n'.join([
            f"场景{i+1}：{s.get('description', '')}\n"
            f"  人物：{s.get('characters', '')}\n"
            f"  地点：{s.get('location', '')}\n"
            f"  情绪：{s.get('mood', '')}"
            for i, s in enumerate(highlights.get('scenes', []))
        ])

        prompt = f"""你是一位专业的影视分镜师。请根据以下场景描述，生成 {num_shots} 个详细的视频分镜。

视频风格：{style_config['visual']}
色彩风格：{style_config['color']}
镜头语言：{style_config['camera']}

场景列表：
{scenes_text}

要求：
1. 分镜必须严格忠于上面的场景列表——人物、地点、事件、情绪都要与场景一致，禁止引入场景中不存在的设定或与剧情无关的通用模板画面
2. 共 {num_shots} 个分镜，每个分镜对应一个关键画面
3. 每个分镜包含：分镜序号、景别（远景/全景/中景/近景/特写）、画面描述、镜头运动、时长建议
4. 画面描述要具体、有画面感，适合作为AI视频生成的提示词
5. 分镜之间要有节奏感，有张有弛
6. 最后一个分镜要有结尾感（留白/悬念/情绪升华）

请严格按以下格式输出：

【分镜1】
景别：远景
画面描述：...
镜头运动：缓慢推进
时长：约5秒

【分镜2】
...
"""

        result = self.llm.chat(prompt)
        return self._parse_shots(result)

    def _parse_shots(self, text):
        """解析分镜输出"""
        shots = []
        shot_pattern = re.compile(r'【分镜(\d+)】\s*\n(.+?)(?=\n【分镜|\Z)', re.DOTALL)

        for match in shot_pattern.finditer(text):
            shot_num = int(match.group(1))
            shot_text = match.group(2).strip()
            shot = {'shot_num': shot_num}

            for line in shot_text.split('\n'):
                line = line.strip()
                if line.startswith('景别：'):
                    shot['shot_type'] = line[3:].strip()
                elif line.startswith('画面描述：'):
                    shot['description'] = line[5:].strip()
                elif line.startswith('镜头运动：'):
                    shot['camera_movement'] = line[5:].strip()
                elif line.startswith('时长：'):
                    shot['duration'] = line[3:].strip()

            if 'description' in shot:
                shots.append(shot)

        return shots

    def _generate_prompts(self, shots, style_config):
        """为每个分镜生成AI视频提示词"""
        prompt_list = []
        for shot in shots:
            prompt = (
                f"{style_config['visual']}，{style_config['color']}。"
                f"{shot.get('shot_type', '')}，{shot.get('description', '').rstrip('。')}。"
                f"镜头：{shot.get('camera_movement', '固定镜头')}。"
                f"电影级画质，高细节， cinematic composition。"
            )
            prompt_list.append(prompt.strip())
            shot['prompt'] = prompt.strip()
        return prompt_list

    def _format_full_script(self, title, style, shots, style_config):
        """格式化完整脚本（Markdown 格式）"""
        lines = []
        lines.append(f"# 《{title}》视频分镜脚本")
        lines.append('')
        lines.append(f"**风格**：{style}")
        lines.append(f"**分镜数**：{len(shots)}")
        lines.append('')
        lines.append('---')
        lines.append('')

        for shot in shots:
            lines.append(f"## 分镜 {shot.get('shot_num', '?')}")
            lines.append('')
            lines.append(f"- **景别**：{shot.get('shot_type', '-')}")
            lines.append(f"- **时长**：{shot.get('duration', '-')}")
            lines.append(f"- **镜头运动**：{shot.get('camera_movement', '-')}")
            lines.append('')
            lines.append(f"**画面描述**：")
            lines.append(shot.get('description', ''))
            lines.append('')
            if shot.get('prompt'):
                lines.append(f"**AI生成提示词**：")
                lines.append(f"> {shot['prompt']}")
                lines.append('')

        lines.append('---')
        lines.append('')
        lines.append(f"**视觉风格**：{style_config['visual']}")
        lines.append(f"**色彩风格**：{style_config['color']}")
        lines.append(f"**配乐风格**：{style_config['music']}")

        return '\n'.join(lines)

    # ---- 便捷方法 ----

    @classmethod
    def get_available_styles(cls):
        """获取所有可用风格"""
        return list(cls.STYLES.keys())

    def quick_extract(self, text, num_scenes=3):
        """
        快速提取高光场景（不生成分镜，只提取场景）
        用于快速预览哪些章节适合做视频
        """
        highlights = self._extract_highlights(text, '', num_scenes)
        return {
            'success': True,
            'summary': highlights.get('summary', ''),
            'scenes': highlights.get('scenes', []),
        }

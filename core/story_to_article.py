"""
小说章节 → 公众号/飞书文章 转换器

功能：
- 小说章节 → 深度解读文章（适合公众号推文）
- 小说章节 → 剧情梗概/速读（适合引流）
- 小说章节 → 人物分析/世界观科普
- 多章节合集 → 专题文章
- 输出 Markdown，可直接发布到飞书/公众号

使用方式：
    from core.story_to_article import StoryToArticle
    converter = StoryToArticle()

    # 生成深度解读文章
    result = converter.chapter_to_deep_article(chapter_text, title='第1章 xxx')

    # 生成剧情速读
    result = converter.chapter_to_summary(chapter_text, style='速读')

    # 多章合集
    result = converter.chapters_to_feature([ch1, ch2, ch3], feature_title='第一卷复盘')
"""

import os
import re
from .llm_client import LLMClient


class StoryToArticle:
    """小说章节 → 文章 转换器"""

    # 文章类型模板
    ARTICLE_TYPES = {
        'deep_analysis': {
            'name': '深度解读',
            'description': '深度解读章节内容，分析人物心理、剧情伏笔、世界观设定',
            'audience': '核心读者 / 粉丝',
        },
        'summary': {
            'name': '剧情速读',
            'description': '快速回顾章节剧情，适合没时间看原文的读者',
            'audience': '普通读者 / 追更党',
        },
        'character': {
            'name': '人物分析',
            'description': '聚焦人物成长、性格变化、关系演变',
            'audience': '角色粉 / CP粉',
        },
        'worldview': {
            'name': '世界观科普',
            'description': '从章节内容扩展，科普世界观设定、修炼体系等',
            'audience': '设定党 / 考据党',
        },
        'feature': {
            'name': '专题合集',
            'description': '多章节合集，形成专题文章',
            'audience': '新读者 / 入坑指南',
        },
    }

    def __init__(self, llm_client=None):
        self.llm = llm_client or LLMClient(
            system_prompt='你是一位资深内容编辑和文学评论家，擅长将小说内容转化为优质的公众号文章。'
        )

    # ===== 单章转换 =====

    def chapter_to_deep_article(self, chapter_text, title='', chapter_num='',
                                series_name='', author=''):
        """
        生成深度解读文章

        Returns:
            dict: {'success': bool, 'title': str, 'content': str, 'summary': str, 'tags': list}
        """
        print(f"[Story→Article] 生成深度解读文章: {title}")

        content = self._call_llm_article(
            chapter_text=chapter_text,
            title=title,
            article_type='deep_analysis',
            chapter_num=chapter_num,
            series_name=series_name,
        )

        return self._wrap_result(content, title, 'deep_analysis')

    def chapter_to_summary(self, chapter_text, title='', chapter_num='', series_name=''):
        """生成剧情速读文章"""
        print(f"[Story→Article] 生成剧情速读: {title}")

        content = self._call_llm_article(
            chapter_text=chapter_text,
            title=title,
            article_type='summary',
            chapter_num=chapter_num,
            series_name=series_name,
        )

        return self._wrap_result(content, title, 'summary')

    def chapter_to_character_analysis(self, chapter_text, character_name,
                                       title='', chapter_num='', series_name=''):
        """生成人物分析文章"""
        print(f"[Story→Article] 生成人物分析: {character_name}")

        content = self._call_llm_article(
            chapter_text=chapter_text,
            title=title,
            article_type='character',
            chapter_num=chapter_num,
            series_name=series_name,
            extra_context=f"重点分析人物：{character_name}",
        )

        return self._wrap_result(content, title or f'{character_name}人物分析', 'character')

    def chapter_to_worldview_article(self, chapter_text, focus_topic='',
                                      title='', chapter_num='', series_name=''):
        """生成世界观科普文章"""
        print(f"[Story→Article] 生成世界观科普: {focus_topic}")

        content = self._call_llm_article(
            chapter_text=chapter_text,
            title=title,
            article_type='worldview',
            chapter_num=chapter_num,
            series_name=series_name,
            extra_context=f"重点科普主题：{focus_topic}" if focus_topic else '',
        )

        return self._wrap_result(content, title or '世界观科普', 'worldview')

    # ===== 多章合集 =====

    def chapters_to_feature(self, chapters, feature_title, article_type='feature'):
        """
        多章节合集 → 专题文章

        Args:
            chapters: [{'title': str, 'content': str, 'chapter_num': str}, ...]
            feature_title: 专题标题
            article_type: 文章类型

        Returns:
            dict: {'success': bool, 'title': str, 'content': str, 'chapters_count': int}
        """
        print(f"[Story→Article] 生成专题合集: {feature_title} ({len(chapters)}章)")

        # 拼接章节内容（每章截取关键部分）
        combined_text = self._combine_chapters(chapters)

        prompt = f"""你是一位资深内容编辑。请根据以下多个小说章节，撰写一篇专题合集文章。

专题标题：{feature_title}
包含章节数：{len(chapters)}章

章节内容汇总：
{combined_text}

要求：
1. 文章要有一个吸引人的大标题
2. 开头有导语，介绍这个专题的看点
3. 主体按时间线/主题分章节，每个章节有小标题
4. 结尾有总结和展望
5. 总字数 2000-3000 字
6. 使用 Markdown 格式
7. 语言生动有趣，适合公众号阅读

请输出完整的专题文章："""

        result = self.llm.chat(prompt)

        # 提取标题（第一行通常是标题）
        article_title = feature_title
        lines = result.strip().split('\n')
        for line in lines[:5]:
            if line.startswith('# '):
                article_title = line[2:].strip()
                break

        return {
            'success': True,
            'title': article_title,
            'content': result,
            'chapters_count': len(chapters),
            'article_type': article_type,
        }

    # ===== 批量处理 =====

    def batch_convert(self, chapters, article_type='deep_analysis', **kwargs):
        """批量转换章节"""
        results = []
        for i, ch in enumerate(chapters, 1):
            print(f"\n[Story→Article] 处理第 {i}/{len(chapters)} 章: {ch.get('title', '')}")
            try:
                if article_type == 'deep_analysis':
                    result = self.chapter_to_deep_article(
                        ch['content'],
                        title=ch.get('title', ''),
                        chapter_num=ch.get('chapter_num', ''),
                        **kwargs
                    )
                elif article_type == 'summary':
                    result = self.chapter_to_summary(
                        ch['content'],
                        title=ch.get('title', ''),
                        chapter_num=ch.get('chapter_num', ''),
                        **kwargs
                    )
                else:
                    result = self.chapter_to_deep_article(
                        ch['content'],
                        title=ch.get('title', ''),
                        **kwargs
                    )
                results.append(result)
            except Exception as e:
                print(f"[Story→Article] 失败: {e}")
                results.append({
                    'success': False,
                    'title': ch.get('title', ''),
                    'error': str(e)
                })
        return results

    # ---- 内部方法 ----

    def _call_llm_article(self, chapter_text, title, article_type,
                           chapter_num='', series_name='', extra_context=''):
        """调用 LLM 生成文章"""
        type_config = self.ARTICLE_TYPES.get(article_type, self.ARTICLE_TYPES['deep_analysis'])

        # 截断过长的章节内容
        max_len = 10000
        if len(chapter_text) > max_len:
            chapter_text = chapter_text[:max_len] + '\n...(章节后半部分省略)...'

        header_info = []
        if series_name:
            header_info.append(f"作品：{series_name}")
        if chapter_num:
            header_info.append(f"章节：{chapter_num}")
        if title:
            header_info.append(f"标题：{title}")
        header_str = '\n'.join(header_info)

        prompt = f"""你是一位资深的公众号内容编辑。请根据以下小说章节内容，撰写一篇【{type_config['name']}】类型的文章。

{header_str}

文章类型说明：{type_config['description']}
目标读者：{type_config['audience']}
{extra_context}

章节原文：
{chapter_text}

文章要求：
1. 标题要吸引人，符合公众号风格（可以带emoji增加吸引力）
2. 开头要有钩子，吸引读者继续阅读
3. 结构清晰，使用小标题分段
4. 内容要有料，不是简单复述，要有分析和解读
5. 结尾要有互动引导（提问、留言引导等）
6. 总字数 1500-2500 字
7. 使用 Markdown 格式
8. 语言风格：轻松但有深度，像和朋友聊天一样自然

请输出完整的文章内容（直接输出 Markdown，不要加任何前缀说明）："""

        return self.llm.chat(prompt)

    def _combine_chapters(self, chapters):
        """合并多个章节内容（每章截取关键部分）"""
        parts = []
        for ch in chapters:
            title = ch.get('title', ch.get('chapter_num', '未知章节'))
            content = ch.get('content', '')
            # 每章截取前 2000 字 + 后 1000 字
            if len(content) > 3000:
                content = content[:2000] + "\n...(中间省略)...\n" + content[-1000:]
            parts.append(f"## {title}\n\n{content}")
        return '\n\n---\n\n'.join(parts)

    def _wrap_result(self, content, title, article_type):
        """包装结果"""
        # 提取标题
        article_title = title
        lines = content.strip().split('\n')
        for line in lines[:5]:
            if line.startswith('# '):
                article_title = line[2:].strip()
                break

        # 生成摘要（取前150字）
        plain_text = re.sub(r'[#*_`>\-]', '', content).strip()
        summary = plain_text[:150] + '...' if len(plain_text) > 150 else plain_text

        return {
            'success': True,
            'title': article_title,
            'content': content,
            'summary': summary,
            'article_type': article_type,
            'word_count': len(content),
        }

    # ---- 便捷方法 ----

    @classmethod
    def get_article_types(cls):
        """获取所有文章类型"""
        return {k: v['name'] for k, v in cls.ARTICLE_TYPES.items()}

    def save_article(self, result, output_path):
        """保存文章到文件"""
        if not result.get('success'):
            return False
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result['content'])
        return True

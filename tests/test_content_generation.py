"""内容生成质量修复的回归测试（不触网）"""

import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _sample_highlights_output():
    return """【摘要】
孟川渡劫成功，决心捞出战死英雄。

【场景1】
概述：孟川缓缓睁开双眼，与柳七月重逢相拥。
人物：孟川、柳七月
地点：沧元界·书房
情绪：劫后余生的释然与温情

【场景2】
概述：孟川念出英雄之名，柳七月眼眶泛红。
人物：孟川、柳七月
地点：沧元界·书房
情绪：沉痛追忆、坚定决意
"""


def test_parse_highlights_keeps_first_char():
    """回归：字段前缀是 3 字符（含全角冒号），解析不得吃掉首个内容字"""
    from core.story_to_script import StoryToScript

    conv = StoryToScript.__new__(StoryToScript)  # 不触发 LLM 客户端构造
    parsed = conv._parse_highlights(_sample_highlights_output())

    assert len(parsed['scenes']) == 2
    s1 = parsed['scenes'][0]
    assert s1['description'].startswith('孟川'), f"首字被吃: {s1['description'][:10]}"
    assert '孟川' in s1['characters'], f"人名被吃: {s1['characters']}"
    assert s1['location'].startswith('沧元界'), f"地名被吃: {s1['location']}"
    assert s1['mood'].startswith('劫后余生'), f"情绪被吃: {s1['mood']}"
    assert parsed['summary'].startswith('孟川渡劫成功')


def test_parse_shots_extracts_fields():
    from core.story_to_script import StoryToScript

    conv = StoryToScript.__new__(StoryToScript)
    text = """【分镜1】
景别：大远景
画面描述：云海翻涌的仙山全景。
镜头运动：缓慢横移
时长：约6秒
"""
    shots = conv._parse_shots(text)
    assert len(shots) == 1
    assert shots[0]['shot_type'] == '大远景'
    assert shots[0]['duration'] == '约6秒'
    assert shots[0]['description'].endswith('全景。')


def test_build_prompt_concat_no_double_period():
    """提示词拼接不应出现『。。』"""
    from core.story_to_script import StoryToScript

    conv = StoryToScript.__new__(StoryToScript)
    style = {'visual': '电影级玄幻风格', 'color': '紫金色', 'camera': '电影感运镜'}
    shots = [{'shot_num': 1, 'shot_type': '远景',
              'description': '云海之上的仙山。', 'camera_movement': '横移'}]
    prompts = conv._generate_prompts(shots, style)
    assert '。。' not in prompts[0]


def _get_generator_cls():
    from core.video_to_article import VideoArticleGenerator
    return VideoArticleGenerator


def test_empty_transcript_rejected():
    """空转写必须短路报错，而不是让模型自由发挥（幻觉假阳性根源）"""
    VideoArticleGenerator = _get_generator_cls()
    import pytest
    lp = VideoArticleGenerator()
    for bad in ({'transcript': ''}, {'text': '   '}, {}):
        with pytest.raises(ValueError):
            lp.generate_full_article(bad)


def test_transcript_key_compat():
    """transcript 与 text 两种键名都必须被接受"""
    VideoArticleGenerator = _get_generator_cls()
    lp = VideoArticleGenerator()
    assert lp._extract_transcript({'transcript': 'abc'}) == 'abc'
    assert lp._extract_transcript({'text': 'abc'}) == 'abc'
    assert lp._extract_transcript({'text': '  abc  '}) == 'abc'


def test_solo_review_flags_fabricated_benchmarks():
    """wechat_agent 审稿节点应识别第一手实测/压测数据断言（子进程隔离运行智能体依赖）"""
    import subprocess
    import textwrap

    solo_dir = os.path.join(ROOT)
    code = textwrap.dedent(f"""
        import asyncio, sys
        sys.path.insert(0, r'{solo_dir}')
        from core.wechat_agent.agents.nodes import review_article_node

        draft = ("## 真实压测数据揭秘\\n\\n"
                 "Qdrant 单机 QPS 达到 1200，P99 延迟 40ms。这是我们实测的结果。\\n")
        state = {{"title": "测试", "content_markdown": draft,
                  "article_dir": "", "config": {{}}, "forbidden_words": []}}
        result = asyncio.run(review_article_node(state))
        issues = result.get('review_result', {{}}).get('issues', [])
        assert '事实性风险' in [i['type'] for i in issues], result

        clean = "# 纯剧情文章\\n\\n这是一段没有任何实测数据断言的正文，聊聊人物和情感。"
        state2 = {{"title": "测试", "content_markdown": clean,
                   "article_dir": "", "config": {{}}, "forbidden_words": []}}
        result2 = asyncio.run(review_article_node(state2))
        issues2 = result2.get('review_result', {{}}).get('issues', [])
        assert '事实性风险' not in [i['type'] for i in issues2], result2
        print("SOLO_REVIEW_OK")
    """)
    r = subprocess.run([sys.executable, '-c', code], capture_output=True,
                       encoding='utf-8', errors='replace', cwd=solo_dir, timeout=120)
    assert r.returncode == 0, f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}"
    assert 'SOLO_REVIEW_OK' in r.stdout

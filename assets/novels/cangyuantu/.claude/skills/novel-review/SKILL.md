---
name: "novel-review"
description: "Reviews chapter content for plot coherence, quality, word count requirements, and determines if revisions are needed. Invoke after writing or editing chapters."
---

# 编剧审稿

This skill helps you review and evaluate chapter content from a professional editor's perspective, checking for plot coherence, quality standards, word count requirements, and providing recommendations for revisions.

## Usage

Invoke this skill after writing or editing chapters to get a comprehensive review of:
- Plot coherence and logical flow
- Content quality and adherence to genre conventions
- Word count compliance
- Overall readability and reader engagement
- Need for revisions

## Process

1. **Ask for Chapter Content**:
   - Ask which chapter file to review.
   - Provide context about the chapter's position in the story.

2. **Comprehensive Review**:
   - Use the following prompt template to review the chapter.

### Prompt Template (Chapter Review)

```
【任务】专业编剧审稿：审核正文内容的质量与连贯性

【待审核章节】
{粘贴chapters/8-续写-第X章.txt的内容}

【上下文信息】
【书籍选题】
{1-选题.txt的内容}
【书籍设定】
{2-核心设定.txt的内容}
【章节大纲】
{该章对应的分章大纲}
【上文衔接】
{上一章最后一段内容}

【审核维度】

### 1. 剧情连贯性 (30分)
- [ ] 开篇是否自然承接上一章结尾？
- [ ] 剧情发展是否符合章节大纲设定？
- [ ] 关键情节节点是否完整呈现？
- [ ] 结尾钩子是否按照要求设置？
- [ ] 是否存在逻辑漏洞或前后矛盾？

### 2. 内容质量 (30分)
- [ ] 风格是否与全书设定一致？
- [ ] 语言是否符合网文阅读习惯？（短句、短段落）
- [ ] 人物对话是否符合身份和性格？
- [ ] 场景描写是否适当（不过度、不缺失）？
- [ ] 是否包含至少1个小爽点？

### 3. 字数要求 (20分)
- [ ] 正文字数是否在1800-2000字范围内？（±100字可接受）
- [ ] 字数不足时是否有足够的细节？
- [ ] 字数超标时是否有冗余内容？

### 4. 节奏与可读性 (20分)
- [ ] 章节节奏是否紧凑，无拖沓？
- [ ] 段落划分是否适合手机阅读（≤3行）？
- [ ] 是否有足够的悬念和钩子？
- [ ] 读者看完是否有继续阅读的欲望？

【评分标准】
- 优秀：90-100分 → 无需修改，可直接发布
- 良好：80-89分 → 轻微修改建议，不影响整体
- 合格：70-79分 → 需要局部调整，确保质量
- 不合格：<70分 → 建议重写或大幅修改

【审核报告】

## 综合评分：[得分]分
## 质量等级：[优秀/良好/合格/不合格]

## 详细评价：
1. 剧情连贯性：[得分/30分] - [具体评价]
2. 内容质量：[得分/30分] - [具体评价]
3. 字数要求：[得分/20分] - [具体评价]
4. 节奏与可读性：[得分/20分] - [具体评价]

## 改稿建议：
[列出需要修改的具体问题和建议]

## 是否需要改稿：[是/否]
- 如需要：请使用 /novel-editor 技能进行修改
- 如不需要：可继续创作下一章

【输出格式】
直接输出完整的审核报告
```

3. **Output**:
   - Generate a comprehensive review report with scores and recommendations.

## Integration with Workflow

This skill is best used after the novel-writer or novel-editor skills. It should be placed as Step 8.5 in the core workflow:

1. Step 8: Write Chapter (novel-writer)
2. Step 8.5: Review Chapter (novel-review)
3. Step 9: Edit Chapter (novel-editor) - if needed

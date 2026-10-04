---
name: "novel-reader-review"
description: "Reader-focused review of plot units (5 chapters): assesses story coherence, attractiveness, and identifies bugs. Invoke after writing a complete plot unit to get a挑剔 reader's perspective."
---

# 挑剔的读者审稿

This skill provides a critical reader's perspective on a complete plot unit (5 chapters). It focuses on evaluating story coherence, reader engagement, and identifying plot bugs from the perspective of a discerning audience.

## Usage

Invoke this skill after writing a complete plot unit (5 chapters) to get:
- A reader's perspective on story coherence
- Assessment of reader engagement and attractiveness
- Identification of plot bugs or inconsistencies
- Overall evaluation of whether the plot unit works as intended

## Process

1. **Ask for Plot Unit Content**:
   - Ask for the plot unit number and corresponding chapter files.
   - Gather context about the plot unit's purpose and position in the story.

2. **Critical Reader Review**:
   - Use the following prompt template to review the plot unit.

### Prompt Template (Plot Unit Review)

```
【任务】挑剔的读者审稿：一次性审核5章剧情单元的质量

【待审核剧情单元】
【剧情单元信息】
第{X}卷-单元{Y}：第{起始章}-{结束章}章
单元主题：{剧情单元主题}

【待审核内容】
{粘贴该单元所有5章的正文内容}

【上下文信息】
【书籍选题】
{1-选题.txt的内容}
【书籍设定】
{2-核心设定.txt的内容}
【分卷大纲】
{3-分卷大纲.txt的内容}
【单元大纲】
{该单元对应的剧情单元设定}

【审核维度】

### 1. 故事连贯性 (25分)
- [ ] 剧情单元的5章是否构成一个完整的小故事？
- [ ] 各章之间的衔接是否自然流畅？
- [ ] 剧情发展是否符合单元主题和大纲设定？
- [ ] 是否存在前后矛盾或逻辑漏洞？
- [ ] 结尾是否成功引出下一个单元的钩子？

### 2. 吸引力与可读性 (25分)
- [ ] 剧情是否有足够的吸引力，让读者想一口气看完？
- [ ] 是否包含至少1个"5章小高潮"？
- [ ] 节奏控制是否合理（有张有弛）？
- [ ] 是否有足够的悬念和钩子设置？
- [ ] 是否存在拖沓或冗余内容？

### 3. 爽点密度 (25分)
- [ ] 是否包含足够的爽点（≥3个）？
- [ ] 爽点类型是否多样化？（装逼打脸、实力暴涨、身份反转等）
- [ ] 爽点节奏是否合理（开篇、发展、高潮分布）？
- [ ] 爽点是否符合目标读者群体的喜好？
- [ ] 是否有"黄金3章"的爽点布局？

### 4. 剧情 bug 检测 (25分)
- [ ] 是否存在设定矛盾（如能力上限冲突）？
- [ ] 是否存在人物性格崩坏？
- [ ] 是否存在情节漏洞（如物品消失、能力突然失效）？
- [ ] 是否存在时间线错误？
- [ ] 是否存在因果关系不成立的情节？

【评分标准】
- 优秀：90-100分 → 完美！这个单元可以作为全书的标杆
- 良好：80-89分 → 很棒！但有一些小问题需要调整
- 合格：70-79分 → 还可以，但需要改进核心问题
- 不合格：<70分 → 这个单元有严重问题，建议重写

### 常见读者吐槽点 (经验库)
- "开头就弃了" → 开篇钩子不够强
- "剧情太假了" → 逻辑漏洞或设定冲突
- "主角太蠢了" → 人设崩坏
- "这章水字数" → 内容拖沓、重复
- "没看懂在说什么" → 设定不清晰或逻辑混乱

【审核报告】

## 剧情单元审核报告
【单元信息】第{X}卷-单元{Y}：第{起始章}-{结束章}章
【质量等级】[优秀/良好/合格/不合格]
【综合评分】[得分]分

### 分项评价

#### 1. 故事连贯性：[得分/25分]
[详细评价]
- 优点：
- 问题：

#### 2. 吸引力与可读性：[得分/25分]
[详细评价]
- 优点：
- 问题：

#### 3. 爽点密度：[得分/25分]
[详细评价]
- 爽点清单：
  1. [爽点类型]：[具体内容]
  2. [爽点类型]：[具体内容]
- 分布情况：

#### 4. 剧情 Bug 检测：[得分/25分]
[详细评价]
- 发现的 Bug：
  1. [Bug类型]：[具体描述]
  2. [Bug类型]：[具体描述]

### 核心建议

#### 必须修改的问题：
1. [问题] → [修改建议]
2. [问题] → [修改建议]

#### 可以优化的地方：
1. [优化点] → [优化建议]

### 读者接受度预测

#### 最可能吐槽的地方：
1. [预测吐槽点] → [应对策略]

#### 最可能受欢迎的地方：
1. [亮点] → [如何强化]

### 是否需要改稿：[是/否]
- 如需要：建议重点修改第[X]章、第[Y]章的[具体问题]
- 如不需要：可继续创作下一个剧情单元

【输出格式】
直接输出完整的审核报告
```

3. **Output**:
   - Generate a comprehensive plot unit review report with detailed scores and recommendations.

## Integration with Workflow

This skill is used after writing a complete plot unit (5 chapters). It should be invoked after novel-writer or novel-review skills:

1. Write a complete plot unit (5 chapters) using novel-writer
2. Review the plot unit using novel-reader-review
3. Edit individual chapters if needed using novel-editor

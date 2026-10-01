---
name: "novel-editor"
description: "Edits, modifies, and expands existing content. Invoke when revising outlines or chapters, or needing to add details."
---

# Novel Editor & Expander

This skill helps you refine, correct, and expand your novel's content.

## Usage

Invoke this skill when you have existing content (outline or chapter) that needs improvement, or when you want to expand a short idea into a fuller scene.

## Process

1. **Ask for Content and Goal**:
   - Ask which file/content to edit.
   - Ask for the specific goal: "Modify/Fix" or "Expand".

2. **Modify/Fix**:
   - Use the following template for corrections.

### Prompt Template (Modification)

```
【任务】修改第{X}章的{大纲/正文}

【修改需求】
- 原版问题：{指出逻辑漏洞/节奏问题/人设崩坏}
- 修改方向：将【{旧情节}】改为【{新情节}】

【执行要求】
1. 用符合时间线的新情节替换
2. 确保第{X}章逻辑通顺，且能平滑过渡到第{X+1}章
3. 逻辑自检：
   - 是否与前文设定冲突？（如主角能力限制）
   - 是否影响后续剧情？
   - 是否需要同步修改后续章节？

【输出要求】
- 如无冲突，直接输出修改后的完整内容
- 如有冲突，先列出冲突点，等待确认后再修改

【可选：批量修改】
如需修改多个章节，请列出：
- 第{A}章：{修改点}
- 第{B}章：{修改点}
（我会逐章处理）
```

3. **Expand**:
   - Use the following logic for expansion (e.g., turning a summary into a scene).
   - Focus on adding sensory details, dialogue, and internal monologue while keeping the core plot point.

### Prompt Template (Expansion)

```
【任务】扩写/润色以下段落

【原文段落】
{粘贴需要扩写的段落}

【扩写要求】
1. **增加细节**：
   - 环境描写：{光影/声音/气味}
   - 动作描写：{微表情/肢体语言}
   - 心理描写：{潜台词/内心博弈}
2. **强化冲突**：
   - 拉长关键动作的慢镜头
   - 增加旁观者的反应
3. **字数目标**：
   - 将原文字数扩充至{X}倍（或具体字数）

【保持不变】
- 核心剧情走向不变
- 人物性格标签不变
```

4. **Output**:
   - Overwrite the original file or save as a new version.

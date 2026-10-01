---
name: "novel-writer"
description: "Writes novel content chapter by chapter. Invoke when writing the actual story content."
---

# Novel Writer

This skill helps you write the actual content of your novel, chapter by chapter.

## Usage

Invoke this skill when you have a chapter outline and are ready to write.

## Process

1. **Ask for Chapter Outline**:
   - Ask for the specific chapter outline to write.

2. **Generate Content**:
   - Use the following prompt template to write the chapter.

### Prompt Template

```
【任务】根据章节大纲创作正文，正文字数控制在1800-2000字左右

【选定选题】
步骤1选择的书名和简介{1-选题.txt}
【书籍设定】
步骤2生成的{2-核心设定.txt}

【章节大纲】
{粘贴步骤5的该章大纲}

【核心要求】（必须严格遵守）
1. **上下文衔接**：
   - 上一章结尾：{粘贴上一章最后一段}
   - 本章开篇需自然承接

2. **网文格式**：
   - 多用短句、短段落（一段≤3行）
   - 适合手机竖屏滑动阅读
   - 避免大段环境描写/心理活动

3. **风格调性**：
   - {搞笑风：多用梗/吐槽/反差}
   - {热血风：短句+动词+情绪渲染}
   - {甜宠风：细节+互动+心跳感}
   - 参考上一章的语言风格保持一致

4. **字数控制**：
   - 1800-2000字（±100字可接受）
   - 不足则补充细节，超出则删减废话

5. **剧情截断**【重要】：
   - 严格按照大纲写到"结尾钩子"处立刻停下
   - 不要提前写下一章内容
   - 不要写总结性结尾（如"他决定……"然后结束）
   - 钩子要卡在：
     - 系统提示一半
     - 门被推开但没说是谁
     - 关键话说一半被打断
     - 危险临近但没发生

【对话要求】
- 人物说话要符合身份（配角有口癖/主角有性格）
- 避免"说教式"长篇大论
- 多用"——"表示停顿，增加节奏感

【爽点检查】
- 本章是否有至少1个小高潮？
- 主角是否展现了能力/智商/魅力？
- 读者看完会不会想点下一章？

【输出格式】
先输出第x章 章节标题
然后是正文内容
```

3. **Output**:
   - Save the content to a file named `chapters/8-续写-第{X}章.txt`.

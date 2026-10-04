---
name: "novel-topic"
description: "Generates novel topics based on trends and requirements. Invoke when starting a new novel project or brainstorming ideas."
---

# Novel Topic Generator

This skill helps you generate novel topics based on current trends and specific requirements.

## Usage

Invoke this skill when you want to start a new novel project or need inspiration for a story idea.

## Process

1. **Ask for User Input**:
   - Ask for any specific genre or theme preferences (e.g., "Urban System", "Fantasy Rebirth").
   - Ask for any specific "golden finger" or cheat ideas if any.

2. **Generate Topics**:
   - Use the following prompt template to generate 3 topic options.

### Prompt Template

```
【任务】番茄小说爆款选题生成

【参考案例】
书名：《{参考书名}》
简介：{参考简介}

【要求】
1. 结合当前番茄小说热点（{指定类型/不限}），创作3个极具爆款潜质的选题
2. 书名要求：
   - 正好15个字符（含标点）
   - 吸睛+包含核心梗/反差感
   - 押韵朗朗上口
3. 每个选题包含：
   - 书名
   - 简介（150字以内，黄金三句开头）
   - 核心卖点（一句话说清金手指）
   - 目标受众（男频/女频/全年龄）

【输出格式】
选题A：
书名：
简介：
核心卖点：
目标受众：

（选题B、C同理）
```

3. **Output**:
   - Save the selected topic to a file named `1-选题.txt` in the project folder.

---
name: "novel-cover"
description: "Generates AI prompts for novel covers. Invoke when needing a cover image or visual concept."
---

# Novel Cover Creator

This skill helps you generate AI prompts (Jimeng/Stable Diffusion) for your novel's cover.

## Usage

Invoke this skill when you have a title and a general idea of the visual style.

## Process

1. **Ask for Novel Details**:
   - Ask for the title, genre, protagonist features, and core scene.

2. **Generate Prompt**:
   - Use the following template to generate the AI art prompt.

### Prompt Template

```
【任务】番茄小说封面AI提示词

【基础信息】
书名：{书名}
类型：{都市/玄幻/科幻/末世}
主角特征：{年龄/性别/气质}
核心场景：{标志性场景/装备/能力}

【封面要求】
- 比例：3:4（竖版）
- 风格：{写实/二次元/国风/赛博朋克}
- 色调：{冷色/暖色/对比色}
- 必须元素：
  - 书名文字（位置：上/下/中）
  - 作者名：文海旷工/著

【AI提示词（Midjourney/Jimeng）】

**正面提示词**：
{画面主体描述}，{角色外貌+动作+表情}，{背景环境+氛围}，{光影效果}，{艺术风格}，ultra detailed, 4k, dramatic lighting, cinematic composition

**负面提示词**：
nsfw, low quality, blurry, watermark, text, cropped, deformed

【文字层设计】
- 书名字体：{潇洒手写/电影海报/毛笔书法}
- 颜色：{与背景对比的颜色}
- 特效：{描边/发光/阴影}

【参考风格】（可选）
类似《{参考作品}》的封面风格

---

【分卷封面】（如需要）
第1卷：{卷名}
画面描述：...
（重复上述格式，每卷一个）
```

3. **Output**:
   - Save the prompt to a file named `7-封面提示词.txt`.

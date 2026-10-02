---
name: "novel-outline"
description: "Creates volume outlines, plot units, and chapter outlines. Invoke when planning the structure of the novel."
---

# Novel Outline Creator

This skill helps you plan the structure of your novel, from volume-level outlines to detailed chapter breakdowns.

## Usage

Invoke this skill when you have a topic and settings, and want to plan the story.

## Process

1. **Volume Outline**:
   - Ask for the topic and settings.
   - Generate a 5-volume, 300-chapter outline.

### Prompt Template (Volume Outline)

```
【任务】基于选题及核心设定设计分卷大纲

【选定选题】
从步骤1选择的书名和简介{1-选题.txt}
【书籍设定】
从步骤2生成的{2-核心设定.txt}

【结构要求】
- 全书300章，分5卷，每卷60章
- 总体风格：{节奏明快/幽默搞笑/热血燃/甜宠虐}/爽点密集

【每卷必填项】
第X卷：[卷名，体现核心事件/地图]
- 核心目标：主角要达成什么？（具体量化，如：实力达到XX级/攻略XX人/击败XX势力）
- 主要地图：场景设定（现代都市/异世大陆/虚拟游戏/星际空间）
- 核心反派：本卷BOSS是谁？性格特点？
- 剧情走向：
  - 开篇（1-10章）：切入点+小高潮
  - 发展（11-40章）：矛盾升级+连续打脸/爽点
  - 高潮（41-60章）：最大冲突爆发+引出下卷钩子

【特别要求】
1. 每卷结尾必须留钩子（新地图/新敌人/新秘密）
2. 力量/财富/影响力需阶梯式提升，避免崩盘
3. 第1卷前3章必须出现金手指，前10章必须有初次打脸
```

2. **Output**:
   - Save the volume outline to a file named `4-分卷大纲.txt`.

3. **Plot Units**:
   - Break down each volume into 12 plot units (5 chapters each).

### Prompt Template (Plot Units)

```
【任务】细化第{X}卷剧情单元

【选定选题】
步骤1选择的书名和简介{1-选题.txt}
【书籍设定】
步骤2生成的{2-核心设定.txt}
【分卷大纲】
步骤3生成的{3-分卷大纲.txt}

【基础信息】
第{X}卷名：{卷名}
本卷目标：{从分卷大纲复制}


【要求】
将本卷60章细分为12个"5章剧情单元"，每个单元包含：

【节奏控制】
- **黄金3章法则**：
  - 第1章：钩子+世界观
  - 第2章：金手指出现
  - 第3章：第一次小爽点（打脸/实力展示）
- **5章一小高潮**：每5章必须有1次反转/打脸
- **20章一大高潮**：击败阶段性BOSS

【爽点类型库】
- 装逼打脸：反派嘲讽→主角亮实力→众人震惊
- 实力暴涨：升级/觉醒/获得神器
- 美女倒贴：冷艳女神主动示好
- 财富爆发：一夜暴富/拍卖逆袭
- 身份反转：废柴其实是隐藏大佬

【钩子技巧】
- **对话钩子**："我有一个秘密……"（章末）
- **悬念钩子**："门外站着的，竟然是……"
- **危机钩子**："系统提示：【警告！检测到SSS级威胁】"
- **反转钩子**："然而他不知道，那个女孩，正是……"

【单元模板】
单元{Y}：第{起始章}-{结束章}章
- 主题：{一句话概括这5章讲什么小故事}
- 起（第1-2章）：冲突发生，主角入局
  - 具体事件：
- 承（第3章）：局势紧张，对手嚣张
  - 反派行为：
  - 主角反应：
- 转/合（第4-5章）：主角出手，反转打脸
  - 反转点：
  - 爽点：
  - 收获：{经验/装备/声望/新技能}
  - 引出悬念：

【特殊单元标记】
- 单元1-2：开篇钩子，建立世界观
- 单元6：中期小高潮
- 单元12：本卷终极BOSS战+下卷钩子
```

4. **Output**:
   - Save plot units to a file named `5-第X卷-剧情单元.txt`.

5. **Chapter Outline**:
   - Create detailed outlines for each chapter (5 chapters at a time).

### Prompt Template (Chapter Outline)

```
【任务】创作第{X}-{X+4}章详细大纲

【选定选题】
步骤1选择的书名和简介{1-选题.txt}
【书籍设定】
步骤2生成的{2-核心设定.txt}
【分卷大纲】
步骤3生成的{3-分卷大纲.txt}
【剧情单元】
步骤4生成的{4-第X卷-剧情单元.txt}

【上文衔接】
{复制上一章的结尾钩子}

【风格要求】
- 类型：{搞笑/热血/甜宠/悬疑}
- 节奏：紧凑，每章至少1个小爽点
- 目标读者：番茄小说{男频/女频}用户

【每章模板】
第{X}章：【起一个带梗的标题，10字内】
- 核心目标：{本章要达成什么？}
- 主要场景：{地点}
- 登场人物：{角色A、角色B}
- 关键情节（3-4个节点）：
  1. [开篇]：承接上文，快速入戏
     - 具体：
  2. [发展]：制造冲突/笑料
     - 具体：{反派嘲讽/主角装傻/意外事件}
  3. [高潮]：行动/反转
     - 具体：{主角出手/真相揭露/系统提示}
  4. [收尾]：{可选，情绪平复}
- 本章爽点：{打脸/装逼/实力暴涨/美女倒贴}
- 结尾钩子：{悬念/卡点，让读者想点下一章}

【逻辑检查】
- 本章是否与前文设定冲突？
- 主角行为是否符合人设？
- 爽点密度是否足够？（建议每章至少1个）

【输出要求】
只输出大纲，不要写正文！
```

6. **Output**:
   - Save chapter outlines to a file named `6-第X-Y章-分章大纲.txt`.

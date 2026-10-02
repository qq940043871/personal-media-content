---
name: "novel-settings"
description: "Creates core settings, character profiles, and tags/intros. Invoke when defining the world, characters, or platform metadata."
---

# Novel Settings Creator

This skill helps you define the world, characters, and system settings for your novel.

## Usage

Invoke this skill when you have a topic and need to flesh out the details.

## Process

1. **Ask for User Input**:
   - Ask for the selected topic (Title, Genre, Core Selling Point).
   - Ask for any specific setting preferences (e.g., "Cultivation levels", "System rules").

2. **Generate Settings**:
   - Use the following prompt template to generate the core settings.

### Prompt Template (Core Settings)

```
【任务】完善小说核心设定

【基础信息】
书名：{书名}
类型：{都市/玄幻/科幻/末世/游戏/其他}

【设定板块】

## 1. 世界观与等级体系
- 世界背景：{时代/地点/社会结构}
- 力量/等级划分：
  - 等级1：{名称} - 特征/能力范围
  - 等级2：...
  - （至少5级，最高级不超过10级）
- 货币/资源：{修炼资源/游戏币/积分等}

## 2. 金手指/系统机制【核心】
- 系统名称：
- 触发条件：{穿越/意外/遗传/选中等}
- 核心功能：
  1. 功能A：{具体描述+限制条件}
  2. 功能B：...
  （每个功能要有代价/冷却/成长性）
- 升级路线：
  - LV1 → LV2：需要{条件}，解锁{新功能}
  - ...

## 3. 角色档案
### 1. 角色塑造
- **主角**：给1-2个明显缺点（如社恐/路痴/吃货），增加可爱感
- **配角**：用"标签+反差"（如高冷女将军其实怕虫子）
- **反派**：分层设计（小喽啰→中层BOSS→幕后黑手），别一次性暴露

### 主角
- 姓名：
- 年龄/职业：
- 性格标签：{腹黑/贱萌/杀伐果断/佛系装逼}
- 口头禅：（可选）
- 标志性动作：（如：推眼镜=有人要倒霉）
- 成长轨迹：{从XX废柴 → XX大佬}

### 核心配角（3-5人）
- 姓名：
- 关系：{青梅竹马/保镖/师父/竞争对手}
- 性格标签：
- 作用：{工具人/暗恋对象/搞笑担当}

### 主要反派（分卷设定）
- 第1卷反派：{姓名} - 缺陷：{傲慢/贪婪/愚蠢}
- 第2卷反派：...

## 4.行文风格
明确一种行文风格
从下面的风格中选择
### 1. 轻快“小白文”风格
**适用选题：** 都市逆袭、系统流、穿书爽文、神医兵王
### 2. 荒诞“发疯文学”风格
**适用选题：** 反内耗、社畜觉醒、无厘头修仙、沙雕甜宠
### 3. 集体主义末世文风格
**适用选题：** 末世求生、科幻灾难、国家力量、群像生存
### 4. 代入感“摄像头女主”风格
**适用选题：** 第一人称宫斗、旁观者视角穿书、偷听心声类
### 5. 掌控感“反转权柄”风格
**适用选题：** 女强男弱、反向攻略、心机女主、修罗场
### 6. 去言情“女性升级流”风格
**适用选题：** 无限流女主、游戏降临、末日女强人、事业脑女主
### 7. 实验性“类型融合”风格
**适用选题：** 规则怪谈+无限流、科幻+修仙、刑侦+穿书
### 8. 现实性“日常修仙”风格
**适用选题：** 修仙种田、慢生活修真、现代人修仙、师徒日常

【创作提示】
1. 金手指规则要简单粗暴，读者一看就懂
2. 等级差距要明显，方便打脸反转
3. 配角别太完美，留缺陷方便制造冲突


```

3. **Output**:
   - Save the settings to a file named `2-核心设定.txt`.

4. **Generate Tags & Intro** (Optional):
   - You can also generate tags and an intro for the novel using the following template.

### Prompt Template (Tags & Intro)

```
【任务】为小说创作标签和简介

【基础信息】
书名：{书名}
类型：{从核心设定提取}
核心卖点：{金手指+主角特质}

【输出要求】

## 1. 作品标签（5-8个）
推荐符合番茄平台热度的标签，如：
- 题材类：{都市异能/系统流/重生/穿越/修仙/科幻}
- 风格类：{搞笑/爽文/无敌流/群像/单女主}
- 特色类：{迪化/腹黑/美食/娱乐/医术}

## 2. 作品简介（500字以内）
### 格式：
**【黄金三句】**（前3句必须抓眼球）
- 第1句：点出主角身份+意外
- 第2句：亮出金手指
- 第3句：展示核心冲突/爽点

**【正文】**（3-5句）
- 简述世界观
- 主角的骚操作/无敌姿态
- 主要对手/障碍

**【结尾】**（1句）
- 留白或喊话，引导点击
  例："这个世界，从今天开始改姓{主角姓}！"

### 风格：
{轻松诙谐/热血燃/霸气侧漏}，让人看了就想笑/想知道后续
```

5. **Output**:
   - Save tags and intro to a file named `3-标签简介.txt`.

#!/bin/bash

# 知识空间ID
SPACE_ID="7642921767484312506"

# 卷的父节点token
VOLUME_TOKENS=(
  "M3hFwrfoIiroWtkqpr0c0S41njf"  # 第一卷
  "FW9Pw1K4YivL12kLQw3cyNFcnhT"  # 第二卷
  "UESrwG0UzilgyjkBgBxcOptQnud"  # 第三卷
  "MQhcwMn1NiIDZdkaQD3cn3Jfnmb"  # 第四卷
  "G1G9wPLpPiafObkkwWtcMDgEnsf"  # 第五卷
)

# 卷的章节范围
VOLUME_RANGES=(
  "1-60"    # 第一卷
  "61-120"  # 第二卷
  "121-180" # 第三卷
  "181-240" # 第四卷
  "241-300" # 第五卷
)

# 章节标题映射（从大纲文件中提取）
declare -A CHAPTER_TITLES

# 第一卷章节标题
CHAPTER_TITLES[1]="第1章 八劫境召唤"
CHAPTER_TITLES[2]="第2章 时空长河捞人"
CHAPTER_TITLES[3]="第3章 青火山拜见师尊"
CHAPTER_TITLES[4]="第4章 异宇宙渗透"
CHAPTER_TITLES[5]="第5章 八劫境联盟会议"
CHAPTER_TITLES[6]="第6章 时空裂缝频现"
CHAPTER_TITLES[7]="第7章 再战黑袍"
CHAPTER_TITLES[8]="第8章 伤势恢复"
CHAPTER_TITLES[9]="第9章 悟出新招"
CHAPTER_TITLES[10]="第10章 三战黑袍"
CHAPTER_TITLES[11]="第11章 异宇宙震怒"
CHAPTER_TITLES[12]="第12章 联盟紧急会议"
CHAPTER_TITLES[13]="第13章 进入异宇宙"
CHAPTER_TITLES[14]="第14章 异宇宙秘密"
CHAPTER_TITLES[15]="第15章 陷入危机"
CHAPTER_TITLES[16]="第16章 异宇宙入侵"
CHAPTER_TITLES[17]="第17章 激烈战斗"
CHAPTER_TITLES[18]="第18章 混沌之刀显威"
CHAPTER_TITLES[19]="第19章 战后疗伤"
CHAPTER_TITLES[20]="第20章 准备反攻"
CHAPTER_TITLES[21]="第21章 异宇宙根基"
CHAPTER_TITLES[22]="第22章 异宇宙大战"
CHAPTER_TITLES[23]="第23章 异宇宙崩溃"
CHAPTER_TITLES[24]="第24章 返回家乡"
CHAPTER_TITLES[25]="第25章 追击残余"
CHAPTER_TITLES[26]="第26章 新的威胁"
CHAPTER_TITLES[27]="第27章 无尽时空"
CHAPTER_TITLES[28]="第28章 探索无尽时空"
CHAPTER_TITLES[29]="第29章 更强大的敌人"
CHAPTER_TITLES[30]="第30章 提升实力"
CHAPTER_TITLES[31]="第31章 悟出新招"
CHAPTER_TITLES[32]="第32章 再战强敌"
CHAPTER_TITLES[33]="第33章 击败强敌"
CHAPTER_TITLES[34]="第34章 追击敌人"
CHAPTER_TITLES[35]="第35章 斩杀强敌"
CHAPTER_TITLES[36]="第36章 新的威胁"
CHAPTER_TITLES[37]="第37章 异宇宙残余"
CHAPTER_TITLES[38]="第38章 追击残余"
CHAPTER_TITLES[39]="第39章 时空风暴"
CHAPTER_TITLES[40]="第40章 时空裂缝"
CHAPTER_TITLES[41]="第41章 时空危机"
CHAPTER_TITLES[42]="第42章 时空守护"
CHAPTER_TITLES[43]="第43章 时空平衡"
CHAPTER_TITLES[44]="第44章 时空秩序"
CHAPTER_TITLES[45]="第45章 时空法则"
CHAPTER_TITLES[46]="第46章 时空掌控"
CHAPTER_TITLES[47]="第47章 时空奥秘"
CHAPTER_TITLES[48]="第48章 时空之力"
CHAPTER_TITLES[49]="第49章 时空极限"
CHAPTER_TITLES[50]="第50章 时空终极"
CHAPTER_TITLES[51]="第51章 时空归一"
CHAPTER_TITLES[52]="第52章 时空永恒"
CHAPTER_TITLES[53]="第53章 时空无尽"
CHAPTER_TITLES[54]="第54章 时空循环"
CHAPTER_TITLES[55]="第55章 时空起点"
CHAPTER_TITLES[56]="第56章 时空终点"
CHAPTER_TITLES[57]="第57章 时空轮回"
CHAPTER_TITLES[58]="第58章 时空超越"
CHAPTER_TITLES[59]="第59章 时空合一"
CHAPTER_TITLES[60]="第60章 时空大道"

# 输出目录
OUTPUT_DIR="D:/ai_coder/p000_000_cangyuantu"

# 上传函数
upload_chapter() {
  local chapter=$1
  local volume_index=$2
  local parent_token=${VOLUME_TOKENS[$volume_index]}
  local title=${CHAPTER_TITLES[$chapter]:-"第${chapter}章"}
  local file_path="${OUTPUT_DIR}/8-续写-第${chapter}章.txt"
  
  if [ ! -f "$file_path" ]; then
    echo "文件不存在: $file_path"
    return 1
  fi
  
  # 读取文件内容
  local content=$(cat "$file_path")
  
  # 创建节点
  echo "上传第${chapter}章: $title"
  lark-cli wiki +node-create \
    --space-id "$SPACE_ID" \
    --parent-node-token "$parent_token" \
    --title "$title" \
    --type docx \
    --as user \
    --format json \
    --dry-run 2>&1 | head -5
  
  return 0
}

# 主循环
echo "开始批量上传章节..."
for volume_index in 0 1 2 3 4; do
  IFS='-' read -r start end <<< "${VOLUME_RANGES[$volume_index]}"
  echo "=== 第$(($volume_index + 1))卷: 第${start}-${end}章 ==="
  
  for chapter in $(seq $start $end); do
    upload_chapter $chapter $volume_index
  done
done

echo "上传完成"

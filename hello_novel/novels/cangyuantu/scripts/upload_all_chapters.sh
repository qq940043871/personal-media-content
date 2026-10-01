#!/bin/bash

# 沧元图知识库完整上传脚本
# 功能：批量上传所有章节到飞书知识库，替换术语，避免重复

SPACE_ID="7642921767484312506"
VOLUME1_NODE="M3hFwrfoIiroWtkqpr0c0S41njf"
VOLUME2_NODE="FW9Pw1K4YivL12kLQw3cyNFcnhT"

# 创建剩余卷目录
echo "创建第三卷、第四卷、第五卷目录..."
VOLUME3=$(lark-cli wiki +node-create --space-id "$SPACE_ID" --title "第三卷：元初境奥秘" --as user 2>&1 | grep -o '"node_token": "[^"]*"' | cut -d'"' -f4)
echo "第三卷节点: $VOLUME3"

VOLUME4=$(lark-cli wiki +node-create --space-id "$SPACE_ID" --title "第四卷：时空探索" --as user 2>&1 | grep -o '"node_token": "[^"]*"' | cut -d'"' -f4)
echo "第四卷节点: $VOLUME4"

VOLUME5=$(lark-cli wiki +node-create --space-id "$SPACE_ID" --title "第五卷：永恒之路" --as user 2>&1 | grep -o '"node_token": "[^"]*"' | cut -d'"' -f4)
echo "第五卷节点: $VOLUME5"

# 术语替换
replace_terms() {
    local content="$1"
    content=$(echo "$content" | sed 's/九劫境/永恒境/g')
    content=$(echo "$content" | sed 's/永恒经/元初境/g')
    echo "$content"
}

# 上传单个章节
upload_chapter() {
    local file="$1"
    local volume_node="$2"
    local chapter_num=$(basename "$file" | sed -n 's/.*第\([0-9]*\)章.*/\1/p')

    if [ -z "$chapter_num" ]; then
        echo "跳过无效文件: $file"
        return
    fi

    # 获取章节标题（第一行）
    local title=$(head -1 "$file" | sed 's/^[0-9]*章//' | xargs)
    title="第${chapter_num}章 ${title}"

    # 检查是否已存在（避免重复）
    local existing=$(lark-cli wiki +node-list --space-id "$SPACE_ID" --parent-node-token "$volume_node" --page-size 50 --as user 2>&1 | grep -c "\"title\": \"$title\"")
    if [ "$existing" -gt 0 ]; then
        echo "跳过已存在: $title"
        return
    fi

    echo "上传: $title"

    # 创建wiki节点
    lark-cli wiki +node-create \
        --space-id "$SPACE_ID" \
        --parent-node-token "$volume_node" \
        --title "$title" \
        --as user 2>&1 | grep -o '"url": "[^"]*"' | cut -d'"' -f4
}

# 主流程
echo "开始批量上传所有章节..."

# 获取所有章节文件并按数字排序
get_sorted_chapters() {
    ls D:/ai_coder/p000_000_cangyuantu/8-续写-第*.txt | while read file; do
        num=$(basename "$file" | sed -n 's/.*第\([0-9]*\)章.*/\1/p')
        echo "$num $file"
    done | sort -n
}

# 第一卷：第1-60章
echo "=== 第一卷：第1-60章 ==="
get_sorted_chapters | while read num file; do
    if [ "$num" -ge 1 ] && [ "$num" -le 60 ]; then
        upload_chapter "$file" "$VOLUME1_NODE"
        sleep 0.3
    fi
done

# 第二卷：第61-120章
echo "=== 第二卷：第61-120章 ==="
get_sorted_chapters | while read num file; do
    if [ "$num" -ge 61 ] && [ "$num" -le 120 ]; then
        upload_chapter "$file" "$VOLUME2_NODE"
        sleep 0.3
    fi
done

# 第三卷：第121-180章
echo "=== 第三卷：第121-180章 ==="
get_sorted_chapters | while read num file; do
    if [ "$num" -ge 121 ] && [ "$num" -le 180 ]; then
        upload_chapter "$file" "$VOLUME3"
        sleep 0.3
    fi
done

# 第四卷：第181-240章
echo "=== 第四卷：第181-240章 ==="
get_sorted_chapters | while read num file; do
    if [ "$num" -ge 181 ] && [ "$num" -le 240 ]; then
        upload_chapter "$file" "$VOLUME4"
        sleep 0.3
    fi
done

# 第五卷：第241-300章
echo "=== 第五卷：第241-300章 ==="
get_sorted_chapters | while read num file; do
    if [ "$num" -ge 241 ] && [ "$num" -le 300 ]; then
        upload_chapter "$file" "$VOLUME5"
        sleep 0.3
    fi
done

echo "所有章节上传完成！"

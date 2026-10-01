#!/bin/bash

# 沧元图知识库上传脚本
# 功能：批量上传章节到飞书知识库，替换术语

SPACE_ID="7642921767484312506"
VOLUME1_NODE="M3hFwrfoIiroWtkqpr0c0S41njf"
VOLUME2_NODE="FW9Pw1K4YivL12kLQw3cyNFcnhT"

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
    # 正确提取章节号：从"第X章"中提取数字
    local chapter_num=$(basename "$file" | sed -n 's/.*第\([0-9]*\)章.*/\1/p')

    if [ -z "$chapter_num" ]; then
        echo "跳过无效文件: $file"
        return
    fi

    echo "处理第${chapter_num}章..."

    # 读取文件内容
    local content=$(cat "$file")

    # 替换术语
    local modified_content=$(replace_terms "$content")

    # 获取章节标题（第一行）
    local title=$(head -1 "$file" | sed 's/^[0-9]*章//' | xargs)
    title="第${chapter_num}章 ${title}"

    # 创建wiki节点（使用docx类型，内容通过后续API更新）
    lark-cli wiki +node-create \
        --space-id "$SPACE_ID" \
        --parent-node-token "$volume_node" \
        --title "$title" \
        --as user 2>&1

    echo "已上传: $title"
}

# 主流程
echo "开始批量上传章节到知识库..."

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
        sleep 0.5  # 避免API限流
    fi
done

# 第二卷：第61-120章
echo "=== 第二卷：第61-120章 ==="
get_sorted_chapters | while read num file; do
    if [ "$num" -ge 61 ] && [ "$num" -le 120 ]; then
        upload_chapter "$file" "$VOLUME2_NODE"
        sleep 0.5
    fi
done

echo "上传完成！"

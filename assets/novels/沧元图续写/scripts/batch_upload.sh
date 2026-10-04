#!/bin/bash

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
declare -a VOL_START=(1 61 121 181 241)
declare -a VOL_END=(60 120 180 240 300)

OUTPUT_DIR="D:/ai_coder/p000_000_cangyuantu"
SUCCESS_COUNT=0
FAIL_COUNT=0

for vol in 0 1 2 3 4; do
  start=${VOL_START[$vol]}
  end=${VOL_END[$vol]}
  parent=${VOLUME_TOKENS[$vol]}
  vol_name=$((vol+1))
  
  echo "=== 第${vol_name}卷: 第${start}-${end}章 ==="
  
  for ch in $(seq $start $end); do
    file="${OUTPUT_DIR}/8-续写-第${ch}章.txt"
    
    if [ ! -f "$file" ]; then
      echo "[SKIP] 文件不存在: 第${ch}章"
      FAIL_COUNT=$((FAIL_COUNT+1))
      continue
    fi
    
    content=$(cat "$file")
    title="第${ch}章"
    
    # 创建节点
    result=$(lark-cli wiki +node-create \
      --space-id "$SPACE_ID" \
      --parent-node-token "$parent" \
      --title "$title" \
      --as user 2>&1)
    
    obj_token=$(echo "$result" | grep -o '"obj_token":"[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -z "$obj_token" ]; then
      echo "[FAIL] 第${ch}章 创建节点失败"
      FAIL_COUNT=$((FAIL_COUNT+1))
      continue
    fi
    
    # 更新内容
    update_result=$(lark-cli docs +update \
      --doc "$obj_token" \
      --markdown "$content" \
      --as user 2>&1)
    
    if echo "$update_result" | grep -q '"ok":true'; then
      echo "[OK] 第${ch}章"
      SUCCESS_COUNT=$((SUCCESS_COUNT+1))
    else
      echo "[FAIL] 第${ch}章 内容更新失败"
      FAIL_COUNT=$((FAIL_COUNT+1))
    fi
    
    sleep 0.3
  done
done

echo ""
echo "=== 完成 ==="
echo "成功: ${SUCCESS_COUNT} 章"
echo "失败: ${FAIL_COUNT} 章"

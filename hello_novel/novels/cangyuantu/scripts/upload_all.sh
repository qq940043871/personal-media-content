#!/bin/bash

SPACE_ID="7642921767484312506"
VOLUME_TOKENS=("M3hFwrfoIiroWtkqpr0c0S41njf" "FW9Pw1K4YivL12kLQw3cyNFcnhT" "UESrwG0UzilgyjkBgBxcOptQnud" "MQhcwMn1NiIDZdkaQD3cn3Jfnmb" "G1G9wPLpPiafObkkwWtcMDgEnsf")
VOL_START=(1 61 121 181 241)
VOL_END=(60 120 180 240 300)
DIR="D:/ai_coder/p000_000_cangyuantu"
OK=0
FAIL=0

# 从大纲文件提取标题
get_title() {
  local ch=$1
  local start=$(( (ch-1)/5*5 + 1 ))
  local end=$(( start + 4 ))
  local outline_file="${DIR}/6-续写-第${start}-${end}章-分章大纲.txt"
  
  if [ -f "$outline_file" ]; then
    local title=$(grep "^第${ch}章" "$outline_file" | head -1 | sed 's/：/:/g' | sed 's/第\([0-9]*\)章[: ]*//')
    if [ -n "$title" ]; then
      echo "第${ch}章 ${title}"
      return
    fi
  fi
  echo "第${ch}章"
}

for vol in 0 1 2 3 4; do
  start=${VOL_START[$vol]}
  end=${VOL_END[$vol]}
  parent=${VOLUME_TOKENS[$vol]}
  
  echo "=== 第$((vol+1))卷 ==="
  
  for ch in $(seq $start $end); do
    file="${DIR}/8-续写-第${ch}章.txt"
    [ ! -f "$file" ] && { FAIL=$((FAIL+1)); continue; }
    
    title=$(get_title $ch)
    content=$(cat "$file")
    
    # 创建节点
    result=$(lark-cli wiki +node-create --space-id "$SPACE_ID" --parent-node-token "$parent" --title "$title" --as user 2>&1)
    obj_token=$(echo "$result" | grep "obj_token" | sed 's/.*"obj_token": "\([^"]*\)".*/\1/')
    
    [ -z "$obj_token" ] && { echo "[FAIL] $title"; FAIL=$((FAIL+1)); continue; }
    
    # 更新内容
    update=$(lark-cli docs +update --doc "$obj_token" --markdown "$content" --mode overwrite --as user 2>&1)
    
    if echo "$update" | grep -q '"ok":true'; then
      echo "[OK] $title"
      OK=$((OK+1))
    else
      echo "[FAIL] $title"
      FAIL=$((FAIL+1))
    fi
    sleep 0.2
  done
done

echo ""
echo "=== 完成 ==="
echo "成功: $OK 章"
echo "失败: $FAIL 章"

#!/bin/bash

SPACE_ID="7643367191756147660"
VOL_PARENTS=("OW0dwcWgUi9o6Uk10akcm1RGn4b" "MnoJw8tatiBNYGkrOSyc5STbnPc" "RUZEwmPJgiVhURkrUsIcxoqLnZg" "A9iWwz3KOisviKkmpCQchILOnPh" "T4miwtWhGibnCHkMwN0cwKU2nCd")
DIR="D:/ai_coder/p000_000_cangyuantu"
OK=0
FAIL=0

get_title() {
  local ch=$1
  local s=$(( (ch-1)/5*5 + 1 ))
  local e=$(( s + 4 ))
  local f="${DIR}/6-续写-第${s}-${e}章-分章大纲.txt"
  if [ -f "$f" ]; then
    local t=$(grep "^第${ch}章" "$f" | head -1 | sed 's/：/ /g; s/第[0-9]*章[： ]*//')
    [ -n "$t" ] && { echo "第${ch}章 $t"; return; }
  fi
  echo "第${ch}章"
}

for vol in 0 1 2 3 4; do
  s=$(( vol*60 + 1 ))
  e=$(( s + 59 ))
  p=${VOL_PARENTS[$vol]}
  echo "=== 第$((vol+1))卷 ==="
  
  for ch in $(seq $s $e); do
    f="${DIR}/8-续写-第${ch}章.txt"
    [ ! -f "$f" ] && { FAIL=$((FAIL+1)); continue; }
    
    title=$(get_title $ch)
    content=$(cat "$f")
    
    r=$(lark-cli wiki +node-create --space-id "$SPACE_ID" --parent-node-token "$p" --title "$title" --as user 2>&1)
    ot=$(echo "$r" | grep "obj_token" | sed 's/.*"obj_token": "\([^"]*\)".*/\1/')
    
    [ -z "$ot" ] && { echo "[FAIL] $title"; FAIL=$((FAIL+1)); continue; }
    
    u=$(lark-cli docs +update --doc "$ot" --markdown "$content" --mode overwrite --as user 2>&1)
    
    if echo "$u" | grep -q '"ok":true'; then
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
echo "成功: $OK | 失败: $FAIL"

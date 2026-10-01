# -*- coding: utf-8 -*-
# 校验 blocks.jsonl 每块 b64 是否能干净解码为 UTF-8
import json, base64, sys

PATH = r"D:\ai_person\p000_0000_it\blog\_seed\blocks.jsonl"

bad = []
total = 0
with open(PATH, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        total += 1
        try:
            raw = base64.b64decode(o["b64"], validate=True)
            raw.decode("utf-8")
        except Exception as e:
            bad.append((o["post"], o["seq"], type(e).__name__, str(e)[:100]))

print("total blocks:", total)
print("bad:", bad if bad else "NONE - all valid")

# -*- coding: utf-8 -*-
import re
from pathlib import Path
CH = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
CJK = re.compile(r"[\u4e00-\u9fff]")
done = [281,293,177,219,300,202,289,295,286,297,143,285,123,296]
print("=== manual rewrites ===")
for i in done:
    t = (CH/f"chapter-{i:03d}.md").read_text(encoding='utf-8')
    lines=[]
    for ln in t.splitlines():
        if re.match(r"^#\s*第\d+章", ln): continue
        if "本章关键点" in ln: break
        lines.append(ln)
    body='\n'.join(lines)
    cjk=len(CJK.findall(body))
    body2=re.sub(r"\n---\s*$","",body,flags=re.M)
    dash=len(re.findall(r"——", body2))
    foot="Y" if "**本章关键点" in t else "N"
    flag=""
    if cjk<5000: flag+=" SHORT"
    if dash>8: flag+=" DASH"
    if foot=="N": flag+=" NOFOOT"
    print(f"  {i:3d} cjk={cjk:5d} dash={dash:2d} foot={foot}{flag}")

print("\n=== 121-300 residual short/dash/foot ===")
short=[]; hi=[]; nofoot=[]; missing=[]
for i in range(121,301):
    p=CH/f"chapter-{i:03d}.md"
    if not p.exists():
        missing.append(i); continue
    t=p.read_text(encoding='utf-8')
    lines=[]
    for ln in t.splitlines():
        if re.match(r"^#\s*第\d+章", ln): continue
        if "本章关键点" in ln: break
        lines.append(ln)
    body='\n'.join(lines)
    cjk=len(CJK.findall(body))
    body2=re.sub(r"\n---\s*$","",body,flags=re.M)
    dash=len(re.findall(r"——", body2))
    foot="**本章关键点" in t
    if 0<=cjk<5000: short.append((i,cjk,dash,foot))
    if dash>8: hi.append((i,cjk,dash,foot))
    if not foot: nofoot.append(i)
print(f"short={len(short)} dash>8={len(hi)} nofoot={len(nofoot)} missing={missing}")
print("\nALL SHORT:")
for i,c,d,f in short:
    print(f"  {i:3d} {c:5d} dash={d} foot={f}")
print("\nDASH>8:")
for i,c,d,f in hi:
    print(f"  {i:3d} cjk={c} dash={d} foot={f}")
print("\nNOFOOT:", nofoot)

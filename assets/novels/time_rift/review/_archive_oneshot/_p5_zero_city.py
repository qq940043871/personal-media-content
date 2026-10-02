# -*- coding: utf-8 -*-
import re
from pathlib import Path
dirp = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
keys = ["时光倒流","19层","周晚晴","47区","观察窗","配电箱","电梯","监察","手写表","林晓实验室","打烊"]
zero=[]
for n in range(481,601):
    text=(dirp/f"chapter-{n:03d}.md").read_text(encoding="utf-8")
    body=re.sub(r"^#[^\n]*\n","",text,count=1)
    body=re.sub(r"(?s)\n---\n\*\*本章关键点：\*\*.*$","",body)
    body=re.sub(r"\n---\n（全书完）.*$","",body,flags=re.S)
    hits=sum(body.count(k) for k in keys)
    if hits==0:
        zero.append(n)
print("zero_city", zero)
for n in zero:
    t=(dirp/f"chapter-{n:03d}.md").read_text(encoding="utf-8")
    print("---", n, "tail ---")
    print(t[-400:])

import re, os, sys
base = r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters'
nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [433,429,469,437,479,462,419,464,465,431]
for n in nums:
    p = os.path.join(base, f'chapter-{n:03d}.md')
    t = open(p, encoding='utf-8').read()
    if '本章关键点' in t:
        body = t[:t.rfind('**本章关键点')]
        footer = True
    else:
        body = t
        footer = False
    body = re.sub(r'\n-{3,}\s*$', '', body)
    cn = sum(1 for c in body if '\u4e00' <= c <= '\u9fff')
    dash = body.count('——')
    nab = len(re.findall(r'不是[^。！？\n]{1,25}而是', body))
    blue_raw = len(re.findall(r'纯蓝|蓝色数据流', body))
    title = t.splitlines()[0][:40]
    ok = 'OK' if cn >= 5000 and dash <= 8 and footer else 'NEED'
    print(f'{n}: {ok} cn={cn} dash={dash} nab={nab} blue_raw={blue_raw} footer={footer} | {title}')

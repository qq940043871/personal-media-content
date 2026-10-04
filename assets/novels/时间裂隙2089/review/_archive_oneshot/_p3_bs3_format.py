import re, os
base = r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters'
nums = [433,429,469,437,479,462,419,464,465,431]
for n in nums:
    p = os.path.join(base, f'chapter-{n:03d}.md')
    t = open(p, encoding='utf-8').read()
    title = t.splitlines()[0]
    has_footer = '**本章关键点：**' in t
    # meta chapter refs in character speech
    meta = re.findall(r'第[一二三四五六七八九十百零\d]+章', t)
    # pure blue current without fusion nearby
    issues = []
    if not title.startswith(f'# 第{n}章'):
        issues.append('bad title')
    if not has_footer:
        issues.append('no footer')
    if meta:
        issues.append(f'meta={meta}')
    # 赵远航
    if '赵远航' in t:
        issues.append('赵远航')
    if '旧时光' in t:
        issues.append('旧时光')
    # mechanical arm on ARIA
    if re.search(r'ARIA[^。\n]{0,20}机械左臂|机械左臂[^。\n]{0,20}ARIA', t):
        issues.append('ARIA+机械臂?')
    print(f'{n}: {title[:30]} issues={issues or ["OK"]}')

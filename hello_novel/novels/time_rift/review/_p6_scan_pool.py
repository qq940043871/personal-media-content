from pathlib import Path
import re
ch_dir = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')
pool = [537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
for n in pool:
    p = ch_dir / f'chapter-{n:03d}.md'
    text = p.read_text(encoding='utf-8-sig')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else '?'
    body_lines = []
    for l in lines:
        if l.startswith('---') or l.startswith('**本章关键点'):
            break
        body_lines.append(l)
    body = ' '.join(body_lines[1:])
    first = body[:200]
    last = body[-200:] if len(body)>200 else body
    flags = []
    if '时光倒流' in body: flags.append('shop')
    if '19层' in body or '十九层' in body: flags.append('19')
    if '47区' in body or '47层' in body: flags.append('47')
    if '林晓' in body: flags.append('lin')
    if '陈明远' in body or '陈维远' in body: flags.append('chen')
    if '店长' in body: flags.append('keeper')
    if '周晚晴' in body: flags.append('zhou')
    print(f'CH{n} {title}')
    print(f'  START: {first[:160]}')
    print(f'  END:   {last[-160:]}')
    print(f'  flags: {",".join(flags)}')
    print()

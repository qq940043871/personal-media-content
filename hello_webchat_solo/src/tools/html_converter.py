"""
Markdown → 微信公众号兼容 HTML 转换器

微信公众号编辑器的 CSS 限制：
- 不支持 <style> 标签、class 选择器
- 不支持 linear-gradient、border-radius（会被过滤）
- <ol> 标签会被过滤，list-style 不生效
- 所有样式必须内联，且只能用纯色

内置主题：default(经典蓝) / grace(优雅紫) / modern(暖橙) / simple(极简黑)
"""
import re


def markdown_to_wechat_html(md_content: str, theme: str = "default") -> str:
    """
    将 Markdown 转换为微信公众号兼容的 HTML。
    所有样式内联嵌入，兼容微信编辑器过滤规则。

    Args:
        md_content: Markdown 原文
        theme: 主题名 —— default / grace / modern / simple

    Returns:
        内联样式的 HTML 字符串，外层包裹 <section>
    """
    # ---- 主题样式表 ----
    themes = {
        "default": {
            "primary": "#1A6DB5", "bg_accent": "#EBF5FF",
            "h1": "text-align:center;font-size:22px;font-weight:bold;color:{primary};border-bottom:2px solid {primary};padding-bottom:10px;margin-bottom:24px;line-height:1.6;",
            "h2": "font-size:17px;font-weight:bold;color:#fff;background:{primary};padding:5px 14px 4px;display:inline-block;margin:2em 0 0;line-height:1.6;",
            "h3": "font-size:16px;font-weight:bold;color:{primary};padding-left:10px;border-left:3px solid {primary};margin:1.5em 0 0.8em;line-height:1.6;",
            "h4": "font-size:15px;font-weight:bold;color:#444;margin:1.2em 0 0.6em;line-height:1.6;",
            "p": "font-size:15px;line-height:1.8;color:#3a3a3a;margin:10px 0;letter-spacing:0.5px;text-align:justify;",
            "strong": "color:{primary};font-weight:bold;",
            "code_inline": "color:{primary};background:{bg_accent};padding:2px 6px;font-size:90%;font-family:Consolas,Monaco,'Courier New',monospace;",
            "a": "color:{primary};text-decoration:none;border-bottom:1px solid {primary};",
            "blockquote": "border-left:4px solid {primary};background:#f7fbff;padding:14px 16px;margin:1.2em 0;color:#555;",
            "li": "margin-bottom:6px;line-height:1.75;color:#3a3a3a;font-size:15px;",
            "img": "max-width:100%;display:block;margin:0 auto;",
            "pre_bg": "#0F2A44", "pre_color": "#93C5FD",
            "table_header_bg": "#1A6DB5", "table_header_color": "#ffffff",
            "table_border": "#d0e3f0", "table_alt_bg": "#f0f7ff",
        },
        "grace": {
            "primary": "#664D9D", "bg_accent": "#F6EEFF",
            "h1": "text-align:center;font-size:22px;font-weight:bold;color:#595959;margin-bottom:24px;line-height:1.6;",
            "h2": "font-size:18px;font-weight:bold;color:#595959;padding-left:10px;border-left:5px solid #DEC6FB;margin:2em 0 1em;line-height:1.6;",
            "h3": "font-size:16px;font-weight:bold;color:#595959;text-align:center;border-bottom:2px solid #DEC6FB;display:inline-block;padding-bottom:4px;margin:1.5em 0 0.8em;line-height:1.6;",
            "h4": "font-size:15px;font-weight:bold;color:#595959;margin:1.2em 0 0.6em;line-height:1.6;",
            "p": "font-size:14px;line-height:1.75;color:#595959;margin:10px 0;letter-spacing:2px;text-align:justify;",
            "strong": "color:#595959;font-weight:bold;",
            "code_inline": "color:{primary};background:{bg_accent};padding:2px 8px;font-size:90%;font-family:Consolas,Monaco,'Courier New',monospace;",
            "a": "color:{primary};font-weight:normal;border-bottom:1px solid {primary};",
            "blockquote": "border:1px solid #DEC6FB;background:{bg_accent};padding:15px 20px;margin:1.2em 0;color:#595959;border-left-width:1px;",
            "li": "margin-bottom:6px;line-height:1.75;color:#595959;font-size:14px;",
            "img": "max-width:100%;display:block;margin:20px auto;",
            "pre_bg": "#F9F5FF", "pre_color": "#5B3A8C",
            "table_header_bg": "#664D9D", "table_header_color": "#ffffff",
            "table_border": "#E9D5FF", "table_alt_bg": "#faf5ff",
        },
        "modern": {
            "primary": "#EF7060", "bg_accent": "#fff9f9",
            "h1": "font-size:22px;font-weight:bold;color:{primary};text-align:center;border-bottom:2px solid {primary};padding-bottom:10px;margin-bottom:24px;line-height:1.6;",
            "h2": "font-size:17px;font-weight:bold;color:#fff;background:{primary};padding:4px 12px 2px;display:inline-block;margin:2em 0 0;line-height:1.6;",
            "h3": "font-size:16px;font-weight:bold;color:{primary};margin:1.5em 0 0.8em;line-height:1.6;",
            "h4": "font-size:15px;font-weight:bold;color:#c0392b;margin:1.2em 0 0.6em;line-height:1.6;",
            "p": "font-size:15px;line-height:1.8;color:#3e3e3e;margin:10px 0;text-align:justify;",
            "strong": "color:{primary};font-weight:bold;",
            "code_inline": "color:#e96900;background:#f3f3f3;padding:2px 6px;font-size:90%;font-family:Consolas,Monaco,'Courier New',monospace;",
            "a": "color:{primary};text-decoration:none;border-bottom:1px solid {primary};",
            "blockquote": "border-left:4px solid {primary};background:{bg_accent};padding:12px 16px;margin:1.2em 0;color:#555;",
            "li": "margin-bottom:6px;line-height:1.75;color:#3e3e3e;font-size:15px;",
            "img": "max-width:100%;display:block;margin:15px auto;",
            "pre_bg": "#1C1917", "pre_color": "#FDBA74",
            "table_header_bg": "#EF7060", "table_header_color": "#ffffff",
            "table_border": "#f5d5d0", "table_alt_bg": "#fff5f4",
        },
        "simple": {
            "primary": "#18181B", "bg_accent": "#FAFAFA",
            "h1": "text-align:center;font-size:24px;font-weight:300;color:#18181B;letter-spacing:4px;margin-bottom:32px;line-height:1.6;",
            "h2": "font-size:18px;font-weight:400;color:#18181B;letter-spacing:2px;margin:2.5em 0 1em;line-height:1.6;",
            "h3": "font-size:16px;font-weight:600;color:#333;margin:2em 0 0.8em;line-height:1.6;",
            "h4": "font-size:15px;font-weight:500;color:#555;margin:1.5em 0 0.6em;line-height:1.6;",
            "p": "font-size:15px;line-height:2;color:#333;margin:1em 0;letter-spacing:0.5px;text-align:justify;",
            "strong": "font-weight:700;color:#18181B;",
            "code_inline": "color:#18181B;background:#f4f4f5;padding:2px 6px;font-size:90%;font-family:Consolas,Monaco,'Courier New',monospace;",
            "a": "color:#18181B;text-decoration:underline;",
            "blockquote": "border:none;padding:16px 24px;margin:1.5em 2em;color:#666;font-style:italic;font-size:16px;line-height:2;text-align:center;",
            "li": "margin-bottom:8px;line-height:1.8;color:#444;font-size:15px;",
            "img": "max-width:100%;display:block;margin:0 auto;",
            "pre_bg": "#fafafa", "pre_color": "#333",
            "table_header_bg": "#18181B", "table_header_color": "#ffffff",
            "table_border": "#e5e5e5", "table_alt_bg": "#fafafa",
        },
    }
    t = themes.get(theme, themes["default"])

    # 将 {primary} / {bg_accent} 变量展开
    def expand(s: str) -> str:
        return s.replace("{primary}", t["primary"]).replace("{bg_accent}", t["bg_accent"])

    html = md_content

    # ========== 1. 代码块 ==========
    def code_block_replacer(match):
        lang = (match.group(1) or "").strip()
        code = match.group(2)
        escaped = (code
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))
        escaped = escaped.replace('  ', '&nbsp;&nbsp;')
        parts = []
        if lang:
            parts.append(
                f'<p style="margin:16px 0 0 0;padding:8px 16px;background:{t["pre_bg"]};color:{t["pre_color"]};'
                f'font-size:13px;font-weight:bold;'
                f'font-family:Consolas,Monaco,\'Courier New\',monospace;'
                f'border-bottom:1px solid rgba(255,255,255,0.1);">{lang}</p>')
        parts.append(f'<div style="background:{t["pre_bg"]};padding:12px 16px;margin:0;'
                     'overflow-x:auto;-webkit-overflow-scrolling:touch;">')
        code_lines = escaped.split('\n')
        for line in code_lines:
            escaped_line = line if line else '&nbsp;'
            parts.append(
                f'<p style="margin:0;padding:2px 0;background:{t["pre_bg"]};color:{t["pre_color"]};'
                f'font-size:13px;line-height:1.8;'
                f'font-family:Consolas,Monaco,\'Courier New\',monospace;'
                f'white-space:nowrap;">{escaped_line}</p>')
        parts.append('</div>')
        return '\n'.join(parts)

    html = re.sub(r'```(\w*)\n(.*?)```', code_block_replacer, html, flags=re.DOTALL)

    # ========== 2. 表格 ==========
    def table_replacer(match):
        raw = match.group(0)
        lines = raw.strip().split('\n')
        if len(lines) < 2:
            return raw
        headers = [h.strip() for h in lines[0].split('|') if h.strip()]
        data_lines = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                data_lines.append(cells)
        tbl = (f'<table style="width:100%;border-collapse:collapse;margin:16px 0 20px;'
               f'font-size:14px;line-height:1.6;border:1px solid {t["table_border"]};">')
        tbl += '<thead>'
        for h in headers:
            tbl += (f'<td style="padding:10px 12px;background:{t["table_header_bg"]};'
                    f'color:{t["table_header_color"]};font-weight:bold;text-align:left;'
                    f'border:1px solid {t["table_header_bg"]};font-size:14px;">{h}</td>')
        tbl += '</thead><tbody>'
        for i, row in enumerate(data_lines):
            bg = t["table_alt_bg"] if i % 2 == 0 else '#ffffff'
            tbl += f'<tr style="background:{bg};">'
            for cell in row:
                tbl += f'<td style="padding:10px 12px;border:1px solid {t["table_border"]};color:#3a3a3a;">{cell}</td>'
            tbl += '</tr>'
        tbl += '</tbody></table>'
        return tbl

    html = re.sub(r'(\|.+\|\n\|[-:\s|]+\|\n(\|.+\|\n?)+)', table_replacer, html, flags=re.MULTILINE)

    # ========== 3. 标题 ==========
    html = re.sub(r'^#### (.+)$', rf'<h4 style="{expand(t["h4"])}">\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$',  rf'<h3 style="{expand(t["h3"])}">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$',   rf'<h2 style="{expand(t["h2"])}">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$',    rf'<h1 style="{expand(t["h1"])}">\1</h1>', html, flags=re.MULTILINE)

    # ========== 4. 行内格式 ==========
    html = re.sub(r'\*\*(.+?)\*\*', rf'<strong style="{expand(t["strong"])}">\1</strong>', html)
    html = re.sub(r'`(.+?)`', rf'<code style="{expand(t["code_inline"])}">\1</code>', html)
    html = re.sub(r'\[(.+?)\]\((.+?)\)', rf'<a href="\2" style="{expand(t["a"])}">\1</a>', html)
    # 引用块
    html = re.sub(
        r'^>\s*(.+)$',
        rf'<blockquote style="{expand(t["blockquote"])}">\1</blockquote>',
        html, flags=re.MULTILINE)

    # ========== 5. 列表 ==========
    def process_lists(text):
        lines = text.split('\n')
        result = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            ul_match = re.match(r'^(\s*)-\s+(.+)$', line)
            ol_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)

            if ul_match or ol_match:
                list_items = []
                while i < n:
                    current_line = lines[i]
                    ul_m = re.match(r'^(\s*)-\s+(.+)$', current_line)
                    ol_m = re.match(r'^(\s*)(\d+)\.\s+(.+)$', current_line)
                    if ul_m:
                        list_items.append(('ul', ul_m.group(2)))
                        i += 1
                    elif ol_m:
                        list_items.append(('ol', ol_m.group(3)))
                        i += 1
                    else:
                        break

                if list_items:
                    result.append('<ul style="margin:8px 0 16px 0;padding-left:0;list-style:none;">')
                    counter = 0
                    for item_type, content in list_items:
                        li_style = expand(t["li"])
                        if item_type == 'ul':
                            result.append(
                                f'<li style="{li_style}padding-left:20px;position:relative;">'
                                f'<span style="position:absolute;left:0;color:{t["primary"]};">•</span> {content}</li>')
                        else:
                            counter += 1
                            result.append(
                                f'<li style="{li_style}padding-left:24px;position:relative;">'
                                f'<span style="position:absolute;left:0;color:{t["primary"]};font-weight:bold;">{counter}.</span> {content}</li>')
                    result.append('</ul>')
            else:
                result.append(line)
                i += 1

        return '\n'.join(result)

    html = process_lists(html)

    # ========== 6. 段落处理 ==========
    p_style = expand(t["p"])
    lines = html.split('\n')
    processed = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            processed.append('<p style="margin:0;height:8px;"></p>')
        elif not stripped.startswith('<'):
            processed.append(f'<p style="{p_style}">{line}</p>')
        else:
            processed.append(line)
    html = '\n'.join(processed)

    styled_html = (
        '<section style="font-size:15px;color:#3a3a3a;line-height:1.8;padding:20px 16px;'
        'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,\'Helvetica Neue\',Arial,\'PingFang SC\','
        '\'Microsoft YaHei\',sans-serif;">'
        f'{html}'
        '</section>')
    return styled_html
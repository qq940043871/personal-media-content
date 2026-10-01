#!/usr/bin/env python3
"""
飞天闪客 - 图文并茂文章生成 & 飞书知识库发布脚本
==================================================
工作流程:
  1. 读取 output/飞天闪客 下的每个视频目录
  2. 读取文章 markdown + 帧图片
  3. 生成图文混排的增强版 markdown 文章
  4. 使用 lark-cli 导入 docx 并发布到飞书知识库
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

# === Config ===
BASE_DIR = r"D:\ai_coder\p000_wfeishu_solo\output\跟大叔学AI编程"
SPACE_ID = "7500848314766852099"  # 人工智能知识库
LARK_CLI = "lark-cli"
TEMP_DIR = os.path.join(os.path.dirname(BASE_DIR), "_publish_temp")
PUBLISHED_LOG = os.path.join(TEMP_DIR, "_published.json")
LARK_CLI_CMD = "lark-cli.cmd" if sys.platform == "win32" else "lark-cli"

os.makedirs(TEMP_DIR, exist_ok=True)


def run_lark_cli(cmd_args, timeout=120, cwd=None):
    """运行 lark-cli 命令，兼容 Windows 编码"""
    # Windows: 通过 cmd.exe 执行 .cmd 文件
    if sys.platform == "win32":
        # 构建命令字符串 (shell=True 时需要字符串)
        cmd_parts = [LARK_CLI_CMD] + cmd_args
        cmd_str = subprocess.list2cmdline(cmd_parts)
        cmd = cmd_str
        use_shell = True
    else:
        cmd = [LARK_CLI_CMD] + cmd_args
        use_shell = False

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            timeout=timeout,
            shell=use_shell,
            cwd=cwd
        )
        # 解码 stdout/stderr
        try:
            stdout = result.stdout.decode('utf-8') if result.stdout else ''
        except UnicodeDecodeError:
            stdout = result.stdout.decode('gbk', errors='replace') if result.stdout else ''
        try:
            stderr = result.stderr.decode('utf-8') if result.stderr else ''
        except UnicodeDecodeError:
            stderr = result.stderr.decode('gbk', errors='replace') if result.stderr else ''

        result.stdout = stdout
        result.stderr = stderr
        return result
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT (>{timeout}s): {' '.join(cmd_args[:3])}")
        return None
    except Exception as e:
        print(f"    ERROR running lark-cli: {e}")
        return None


def get_short_title(video_dir_name):
    """从视频目录名提取简短标题"""
    # 移除 BV号后缀 [BV1qs5S6gEFn]
    name = re.sub(r'\s*\[BV[^\]]+\]', '', video_dir_name)
    # 移除日期前缀 "2024-12-29 23-33-38_"
    name = re.sub(r'^\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}_', '', name)
    # 移除 _video 后缀
    name = re.sub(r'_video$', '', name)
    # 移除话题标签 #xxx
    name = re.sub(r'#[^_]+', '', name)
    # 清理多余的_ -> 空格
    name = re.sub(r'_+', ' ', name).strip()
    # 清理多余空格
    name = re.sub(r'\s+', ' ', name)
    # 限制长度
    if len(name) > 60:
        name = name[:57] + '...'
    return name


def get_safe_filename(title):
    """生成安全的文件名"""
    safe = re.sub(r'[<>:"/\\|?*#]', '', title)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe.strip('_')[:80]
    return safe or "untitled"


def read_article(article_path):
    """读取文章 markdown 内容"""
    with open(article_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def get_frames(frames_dir, max_images=50):
    """获取帧图片列表（均匀采样，最多 max_images 张）"""
    if not os.path.isdir(frames_dir):
        return []
    frames = sorted([
        f for f in os.listdir(frames_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
    if not frames:
        return []

    full_paths = [os.path.join(frames_dir, f) for f in frames]

    # 最多取 max_images 张（保持足够图片使文章图文并茂）
    if len(full_paths) > max_images:
        step = len(full_paths) / max_images
        full_paths = [full_paths[int(i * step)] for i in range(max_images)]

    return full_paths


def clean_article_content(content):
    """
    清理文章内容：去掉顶部的"作为一名专业的教育内容编辑..."这类前言，
    提取真正的教学内容部分
    """
    # 去掉第一段AI提示词（以"好的，"或"作为一名"开头的内容）
    lines = content.split('\n')

    # 找到第一个 H1 标题
    first_h1 = -1
    for i, line in enumerate(lines):
        if re.match(r'^#\s+', line):
            first_h1 = i
            break

    # 找到第一组 --- 分隔线
    first_sep = -1
    for i, line in enumerate(lines):
        if line.strip() == '---':
            first_sep = i
            break

    # 如果 H1 在第一个分隔线之后，移除 H1 之前的内容
    if first_h1 > 0 and first_sep > 0 and first_h1 > first_sep:
        # 前面可能有前言，保留分隔线之后的内容
        content = '\n'.join(lines[first_h1:])
    elif first_h1 > 0:
        content = '\n'.join(lines[first_h1:])

    return content


def build_image_insertion_sections(content, frames, video_dir_name):
    """
    构建文章 + 图片的混合内容。
    返回：内容块列表，每个元素是 (type, data)
    type: 'text' -> data 是文本段落
          'image' -> data 是图片路径
    """
    text_blocks = split_into_blocks(content)
    # 将图片均匀分配到文本块之间
    blocks = interleave_images(text_blocks, frames)
    return blocks


def split_into_blocks(content):
    """
    将文章分割成合理的块。
    每个章节标题及其内容作为一个块。
    """
    lines = content.split('\n')

    # 按标题分割
    blocks = []
    current_header = None
    current_lines = []

    for line in lines:
        if re.match(r'^#{1,4}\s', line):
            if current_lines:
                blocks.append((current_header, '\n'.join(current_lines)))
            current_header = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        blocks.append((current_header, '\n'.join(current_lines)))

    # 如果只有一个块（没有标题分割），按段落分割
    if len(blocks) <= 1:
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        blocks = []
        for p in paragraphs:
            if re.match(r'^#{1,4}\s', p):
                blocks.append((p.strip(), ''))
            else:
                blocks.append((None, p))

    return blocks


def interleave_images(blocks, frames):
    """
    将图片交织插入到文本块之间。
    策略：每1-2个文本块后插入1-2张图片
    """
    result = []
    img_idx = 0

    for i, (header, text) in enumerate(blocks):
        # 添加文本块
        if header:
            result.append(('text', f"{header}\n{text}" if text else header))
        else:
            result.append(('text', text))

        # 在块之间插入图片（但不是每个块后都插）
        # 在章节末尾或重要段落间插图片
        if i < len(blocks) - 1 and img_idx < len(frames):
            # 每个块后都尝试插一张图（保持图文并茂）
            result.append(('image', frames[img_idx]))
            img_idx += 1

            # 偶尔插两张
            if img_idx < len(frames) and i % 3 == 2:
                result.append(('image', frames[img_idx]))
                img_idx += 1

    # 剩余图片追加到末尾
    while img_idx < len(frames):
        result.append(('image', frames[img_idx]))
        img_idx += 1

    return result


def generate_markdown_enhanced(blocks, title):
    """生成增强版 markdown（带图片路径，供本地查看）"""
    lines = []
    lines.append(f"# {title}")
    lines.append("")

    for block_type, data in blocks:
        if block_type == 'text':
            lines.append(data)
            lines.append("")
        elif block_type == 'image':
            # 使用相对路径
            lines.append(f"![{title}]({data})")
            lines.append("")

    return '\n'.join(lines)


def build_publish_payload(blocks):
    """
    为飞书发布构建数据。
    返回：纯文本内容 + 图片插入指令列表
    """
    text_parts = []
    image_insertions = []

    for block_type, data in blocks:
        if block_type == 'text':
            text_parts.append(data)
        elif block_type == 'image':
            # 记录图片要在哪段文本后插入
            anchor_text = get_insertion_anchor(text_parts)
            image_insertions.append({
                'path': data,
                'anchor': anchor_text,
                'before': False
            })

    full_text = '\n\n'.join(filter(None, text_parts))
    return full_text, image_insertions


def get_insertion_anchor(text_parts):
    """从已添加的文本中找到合适的锚点文本"""
    if not text_parts:
        return None
    # 取最后一段的前30字作为锚点
    last = text_parts[-1][:40] if text_parts[-1] else None
    return last


def extract_section_headings(text_content):
    """从文章内容提取章节标题列表"""
    headings = []
    for line in text_content.split('\n'):
        line = line.strip()
        if re.match(r'^#{1,4}\s', line):
            # 清理 markdown 标记
            clean = re.sub(r'[*#]', '', line).strip()
            if clean:
                headings.append(clean)
    return headings


def publish_article_import(text_content, title, frames, space_id, blocks=None):
    """
    发布文章到飞书知识库：
    1. 先创建临时 markdown 文件（纯文本）
    2. 导入到 drive
    3. 插入图片（使用文本锚点定位）
    4. 移动到知识库
    """
    safe_name = get_safe_filename(title)

    # 创建临时 markdown 文件（纯文本，无图片）
    md_path = os.path.join(TEMP_DIR, f"{safe_name}_text.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n{text_content}")
    print(f"    Temp markdown: {os.path.getsize(md_path)} bytes")

    # 导入到 drive
    doc_info = import_md_to_docx(md_path, title)
    if not doc_info:
        return False

    file_token = doc_info.get("token") or doc_info.get("file_token")
    if not file_token:
        print(f"    ERROR: no file_token returned")
        return False
    print(f"    Document created: {file_token}")

    # 提取章节标题用作锚点
    headings = extract_section_headings(text_content)
    print(f"    Found {len(headings)} section headings for anchor")

    # 插入图片（使用文本锚点定位）
    if frames:
        print(f"    Inserting {len(frames)} images...")

        # 为每张图片分配一个插入位置
        # 工作策略：将图片均匀分配到各章节前
        # 逆向插入（从后往前）避免位置偏移
        img_positions = []
        if headings:
            # 均匀分配图片到各标题前
            step = max(1, len(headings) // max(1, len(frames)))
            frame_idx = 0
            for h_idx in range(0, len(headings), step):
                if frame_idx < len(frames):
                    img_positions.append((frames[frame_idx], headings[h_idx], True))
                    frame_idx += 1

            # 多余图片追加到末尾
            while frame_idx < len(frames):
                img_positions.append((frames[frame_idx], None, False))
                frame_idx += 1

            # 逆向排序：先处理最后的图片，再处理前面的
            # 但带锚点的要先处理后面的（避免位置偏移）
            with_anchor = [(p, a, b) for p, a, b in img_positions if a]
            without_anchor = [(p, a, b) for p, a, b in img_positions if not a]

            # 带锚点的逆向处理（后面位置的先处理）
            ordered = list(reversed(with_anchor)) + without_anchor
        else:
            ordered = [(f, None, False) for f in frames]

        success_count = 0
        for i, (frame_path, anchor, before) in enumerate(ordered):
            if not os.path.exists(frame_path):
                continue
            if insert_image_to_doc(file_token, frame_path, anchor=anchor, before=before):
                success_count += 1
                if (i + 1) % 5 == 0:
                    print(f"      ... {i+1}/{len(ordered)} images")
            time.sleep(0.5)

        print(f"    OK {success_count}/{len(frames)} images inserted")

    # 移动到知识库
    move_result = move_to_wiki(file_token, "docx", space_id)
    if not move_result:
        print(f"    WARN: move to wiki may need attention")

    return True


def import_md_to_docx(md_path, doc_name):
    """将本地 markdown 文件导入为飞书 docx（使用相对路径）"""
    # 复制文件到 TEMP_DIR，从 TEMP_DIR 运行命令（使用相对路径）
    rel_filename = os.path.basename(md_path)
    dest_path = os.path.join(TEMP_DIR, rel_filename)
    if os.path.abspath(md_path) != os.path.abspath(dest_path):
        import shutil
        shutil.copy2(md_path, dest_path)

    result = run_lark_cli([
        "drive", "+import",
        "--file", rel_filename,
        "--type", "docx",
        "--name", doc_name,
        "--as", "user"
    ], timeout=120, cwd=TEMP_DIR)
    if not result or result.returncode != 0:
        err = result.stderr[:300] if result else "no result"
        print(f"    ERROR importing: {err}")
        return None
    try:
        data = json.loads(result.stdout)
        if data.get("ok"):
            return data["data"]
        print(f"    ERROR: {json.dumps(data, ensure_ascii=False)[:300]}")
        return None
    except json.JSONDecodeError:
        print(f"    JSON parse error: {result.stdout[:300]}")
        return None


def insert_image_to_doc(doc_token, image_path, anchor=None, before=False):
    """向已有 docx 中插入图片，支持文本锚点定位"""
    # 复制图片到 TEMP_DIR（使用相对路径）
    img_filename = os.path.basename(image_path)
    dest_path = os.path.join(TEMP_DIR, img_filename)
    if not os.path.exists(dest_path) and os.path.exists(image_path):
        import shutil
        shutil.copy2(image_path, dest_path)
    if not os.path.exists(dest_path):
        return False

    cmd = [
        "docs", "+media-insert",
        "--doc", doc_token,
        "--file", img_filename,
        "--type", "image",
        "--align", "center",
        "--as", "user"
    ]
    if anchor:
        # 截取锚点文本前30字（足够匹配）
        anchor_text = anchor[:60]
        cmd.extend(["--selection-with-ellipsis", anchor_text])
        if before:
            cmd.append("--before")

    result = run_lark_cli(cmd, timeout=90, cwd=TEMP_DIR)
    return result is not None and result.returncode == 0


def move_to_wiki(obj_token, obj_type, space_id):
    """将 Drive 中的文档移动到知识库"""
    result = run_lark_cli([
        "wiki", "+move",
        "--obj-token", obj_token,
        "--obj-type", obj_type,
        "--target-space-id", str(space_id),
        "--as", "user"
    ], timeout=120, cwd=TEMP_DIR)
    if not result or result.returncode != 0:
        err = result.stderr[:300] if result else "no result"
        print(f"    Move result: {err}")
        return False
    try:
        data = json.loads(result.stdout)
        return data.get("ok", False)
    except json.JSONDecodeError:
        return False


def load_published_log():
    """加载已发布记录"""
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_published_log(log_data):
    """保存已发布记录"""
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 60)
    print("跟大叔学AI编程 - 图文文章生成 & 飞书知识库发布")
    print("=" * 60)
    print(f"Space ID: {SPACE_ID}")
    print(f"Base:     {BASE_DIR}")
    print()

    # 获取所有视频目录（只包含有 articles 的）
    video_dirs = []
    for d in sorted(os.listdir(BASE_DIR)):
        video_dir = os.path.join(BASE_DIR, d)
        if not os.path.isdir(video_dir) or d.startswith('_'):
            continue
        articles_dir = os.path.join(video_dir, "articles")
        if os.path.isdir(articles_dir) and any(f.endswith('.md') for f in os.listdir(articles_dir)):
            video_dirs.append(d)

    print(f"Found {len(video_dirs)} articles to process")
    print()

    # 加载已发布记录
    published = load_published_log()
    skip_count = 0

    # 处理每个视频
    success_count = 0
    total = len(video_dirs)

    for idx, video_dir_name in enumerate(video_dirs, 1):
        video_dir = os.path.join(BASE_DIR, video_dir_name)

        # 提取标题
        title = get_short_title(video_dir_name)
        print(f"[{idx}/{total}] {title}")

        # 检查是否已发布
        if video_dir_name in published:
            print(f"  SKIP (already published)")
            skip_count += 1
            continue

        # 读取文章
        articles_dir = os.path.join(video_dir, "articles")
        md_file = [f for f in os.listdir(articles_dir) if f.endswith('.md')][0]
        content = read_article(os.path.join(articles_dir, md_file))

        # 清理内容
        content = clean_article_content(content)

        if len(content) < 100:
            print(f"  SKIP (content too short)")
            continue

        # 获取帧图片
        frames_dir = os.path.join(video_dir, "frames")
        frames = get_frames(frames_dir, max_images=30)
        print(f"  Frames: {len(frames)}")

        # 构建图文混合内容
        blocks = build_image_insertion_sections(content, frames, video_dir_name)
        text_content = '\n\n'.join(data for typ, data in blocks if typ == 'text')

        # 生成本地增强版 markdown
        md_enhanced = generate_markdown_enhanced(blocks, title)
        safe_name = get_safe_filename(title)
        enhanced_path = os.path.join(TEMP_DIR, f"{safe_name}.md")
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            f.write(md_enhanced)
        print(f"  Enhanced markdown: {len(md_enhanced)} chars")

        # 发布到飞书
        print(f"  Publishing to Feishu...")
        result = publish_article_import(text_content, title, frames, SPACE_ID, blocks=blocks)

        if result:
            success_count += 1
            published[video_dir_name] = {
                "title": title,
                "published_at": datetime.now().isoformat(),
                "enhanced_md": enhanced_path
            }
            save_published_log(published)
            print(f"  [OK] Published!")
        else:
            print(f"  [FAIL] Failed to publish")

        print()
        # 每篇文章间延迟，避免 API 限流
        time.sleep(1)

    print("=" * 60)
    print(f"Summary: {success_count} published, {skip_count} skipped, {total - success_count - skip_count} failed")
    if published:
        print(f"Total published (cumulative): {len(published)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
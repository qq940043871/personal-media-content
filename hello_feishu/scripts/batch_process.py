#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# 配置
BASE_DIR = Path(r"D:\ai_coder\p000_llm_video_ark\output\从0到1设计一台计算机")
TEMP_DIR = BASE_DIR / "_temp"
TEMP_DIR.mkdir(exist_ok=True)
SPACE_ID = "7644545565442771916"

# P2-P13的标题列表
ARTICLE_TITLES = [
    "P2 第1话-人脑计算机",
    "P3 第2话-冯诺依曼和哈佛",
    "P4 第3话-再谈RAM和ROM",
    "P5 第4话-寄存器组",
    "P6 第5话-运算器",
    "P7 番外篇-运算器和寄存器组原理",
    "P8 第6话-指令集",
    "P9 第7话-汇编",
    "P10 第8话-RAM寻址",
    "P11 第9话-程序计数器",
    "P12 第10话-图像IO",
    "P13 第11话-跳转"
]

def run_lark_cli(cmd_args, timeout=120, cwd=None):
    """运行lark-cli命令"""
    if sys.platform == "win32":
        cmd = ["lark-cli.cmd"] + cmd_args
        use_shell = True
    else:
        cmd = ["lark-cli"] + cmd_args
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
        # 解码
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
    except Exception as e:
        print(f"Error running lark-cli: {e}")
        return None

def process_single_article(title):
    """处理单篇文章"""
    print(f"\n{'='*60}")
    print(f"Processing: {title}")
    print('='*60)

    # 1. 检查目录是否存在
    article_dir = BASE_DIR / title
    if not article_dir.exists():
        print(f"[ERROR] Directory not found: {article_dir}")
        return False

    # 2. 读取文章
    articles_subdir = article_dir / "articles"
    md_file = articles_subdir / f"{title}.md"
    if not md_file.exists():
        print(f"[ERROR] Article not found: {md_file}")
        return False

    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    print(f"[OK] Read article: {len(md_content)} chars")

    # 3. 准备临时markdown
    temp_md = TEMP_DIR / f"{title}.md"
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 4. 导入文档
    print("\nImporting document...")
    import_cmd = [
        "drive", "+import",
        "--file", f"{title}.md",
        "--type", "docx",
        "--name", title,
        "--as", "user"
    ]
    result = run_lark_cli(import_cmd, cwd=str(TEMP_DIR))

    if not result or result.returncode != 0:
        print(f"[ERROR] Import failed: {result.stderr if result else 'No result'}")
        return False

    try:
        import_data = json.loads(result.stdout)
        if not import_data.get('ok'):
            print(f"[ERROR] Import failed: {import_data}")
            return False
        doc_token = import_data['data']['token']
        print(f"[OK] Imported: token={doc_token}")
    except Exception as e:
        print(f"[ERROR] Parse failed: {e}")
        return False

    # 5. 处理关键帧
    frames_dir = article_dir / "frames"
    frames = []
    if frames_dir.exists():
        frames = sorted([f for f in frames_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']])
        print(f"[OK] Found {len(frames)} keyframes")

    # 6. 复制图片到临时目录
    selected_frames = frames[:20]  # 前20张
    for frame in selected_frames:
        dest = TEMP_DIR / frame.name
        if not dest.exists():
            shutil.copy2(frame, dest)

    # 7. 插入图片
    if selected_frames:
        print(f"\nInserting {len(selected_frames)} images...")
        success_count = 0
        for i, frame in enumerate(selected_frames, 1):
            print(f"  [{i}/{len(selected_frames)}] Inserting: {frame.name}")
            insert_cmd = [
                "docs", "+media-insert",
                "--doc", doc_token,
                "--file", frame.name,
                "--type", "image",
                "--align", "center",
                "--as", "user"
            ]
            result = run_lark_cli(insert_cmd, cwd=str(TEMP_DIR))
            if result and result.returncode == 0:
                success_count += 1
            time.sleep(0.2)
        print(f"[OK] Images inserted: {success_count}/{len(selected_frames)}")

    # 8. 移动到知识库
    print("\nMoving to wiki space...")
    move_cmd = [
        "wiki", "+move",
        "--obj-token", doc_token,
        "--obj-type", "docx",
        "--target-space-id", SPACE_ID,
        "--as", "user"
    ]
    result = run_lark_cli(move_cmd)
    if result and result.returncode == 0:
        print(f"[OK] Moved successfully")
    else:
        print(f"[WARN] Move may have issues: {result.stderr if result else 'No result'}")

    print(f"\n[OK] {title} processed!")
    return True

def main():
    print(f"Ready to process {len(ARTICLE_TITLES)} articles (P2-P13)")

    # 处理每篇文章
    success_count = 0
    for title in ARTICLE_TITLES:
        # 跳过P2，因为已经处理了
        if title == "P2 第1话-人脑计算机":
            print(f"Skipping {title} (already processed)")
            continue
        if process_single_article(title):
            success_count += 1
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"All done: {success_count + 1}/{len(ARTICLE_TITLES)} articles processed!")
    print('='*60)

if __name__ == "__main__":
    main()

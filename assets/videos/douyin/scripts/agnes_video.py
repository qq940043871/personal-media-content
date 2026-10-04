#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AGNES 文生视频工具 — 调 apihub.agnes-ai.com 的 OpenAI Videos 兼容接口

流程：POST /v1/videos 创建任务 → 轮询 /agnesapi?video_id=... → 下载 mp4。
凭据复用根 .env 的 Provider 注册表（PROVIDER_AGNES_API_KEY / _BASE_URL），
模型默认 agnes-video-2.5-flash（文档见 https://wiki.agnes-ai.com/en/docs/agnes-video-25）。

用法（在仓库根或本目录执行）：
    python agnes_video.py --prompt "提示词" -o out.mp4
    python agnes_video.py --prompt "提示词" --seconds 8 --size 1080P --aspect 9:16 --model agnes-video-2.5

退出码：0 成功 / 1 失败（stderr 给原因；429 = 免费档限流，需升级 Token Plan 或等配额）
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# 根目录 .env（脚本可能从任意 cwd 启动，按本文件位置回溯仓库根）
_ROOT = Path(__file__).resolve().parents[4]
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / '.env')
except ImportError:
    pass

BASE_URL = (os.getenv('PROVIDER_AGNES_BASE_URL') or 'https://apihub.agnes-ai.com').rstrip('/')
API_KEY = os.getenv('PROVIDER_AGNES_API_KEY') or ''
DEFAULT_MODEL = 'agnes-video-2.5-flash'
POLL_INTERVAL = 15      # 秒（免费档限制状态查询频率，太快会 429）
POLL_TIMEOUT = 900      # 生成最长等待


class ApiBusy(Exception):
    """限流/排队（429、503 video_queue_full）——可等待后重试"""


def _api(path, payload=None, timeout=120):
    """POST（payload 非空）或 GET 请求，返回解析后的 JSON；限流抛 ApiBusy"""
    url = BASE_URL + path
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload else None,
        method='POST' if payload else 'GET',
        headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:500]
        if e.code in (429, 503):
            raise ApiBusy(f'HTTP {e.code}: {body}')
        raise SystemExit(f'[ERROR] HTTP {e.code} {path}: {body}')
    except urllib.error.URLError as e:
        raise SystemExit(f'[ERROR] 网络错误 {path}: {e}')


def poll(video_id, model=DEFAULT_MODEL, out='agnes_video.mp4'):
    """轮询一个已创建的任务直到完成并下载，成功返回输出路径"""
    print(f'[OK] 轮询任务: {video_id}（model={model}）')
    query = urllib.parse.urlencode({'video_id': video_id, 'model_name': model})
    deadline = time.time() + POLL_TIMEOUT
    while True:
        time.sleep(POLL_INTERVAL)
        try:
            st = _api(f'/agnesapi?{query}', timeout=60)
        except ApiBusy as e:
            print(f'  .. 忙（{e}），继续等待', flush=True)
            if time.time() > deadline:
                raise SystemExit(f'[ERROR] 轮询超时，任务可能仍在进行: {video_id}')
            continue
        status = st.get('status')
        print(f"  .. {status} {st.get('progress', '')}%", flush=True)
        if status == 'completed':
            url = st.get('url')
            if not url:
                raise SystemExit(f'[ERROR] 完成但无 url: {json.dumps(st, ensure_ascii=False)[:500]}')
            break
        if status == 'failed':
            raise SystemExit(f'[ERROR] 生成失败: {json.dumps(st, ensure_ascii=False)[:500]}')
        if time.time() > deadline:
            raise SystemExit(f'[ERROR] 轮询超时（{POLL_TIMEOUT}s），任务可能仍在进行: {video_id}')

    dest = Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(url, timeout=300) as r, open(dest, 'wb') as f:
                f.write(r.read())
            break
        except (urllib.error.URLError, OSError) as e:
            if attempt == 3:
                raise SystemExit(f'[ERROR] 下载失败（已重试 3 次）: {e}\n[INFO] 可手动下载: {url}')
            print(f'  .. 下载失败（{e}），{10 * attempt}s 后重试', flush=True)
            time.sleep(10 * attempt)
    print(f'[OK] 已保存: {dest}（{dest.stat().st_size} 字节）')
    print(f'[OK] 视频: {url}')
    return dest


def generate(prompt, model=DEFAULT_MODEL, seconds='5', size='720P',
             aspect='9:16', out='agnes_video.mp4'):
    """文生视频全流程，成功返回输出路径"""
    if not API_KEY:
        raise SystemExit('[ERROR] PROVIDER_AGNES_API_KEY 未配置（根 .env）')

    try:
        task = _api('/v1/videos', {
            'model': model,
            'prompt': prompt,
            'mode': 'text',
            'seconds': str(seconds),
            'size': size,
            'aspect_ratio': aspect,
        })
    except ApiBusy as e:
        raise SystemExit(f'[ERROR] 创建任务被限流/排队满，稍后重试（{e}）')
    video_id = task.get('video_id') or task.get('id') or task.get('task_id')
    if not video_id:
        raise SystemExit(f'[ERROR] 创建任务无 video_id: {json.dumps(task, ensure_ascii=False)[:500]}')
    print(f'[OK] 任务已创建: {video_id}（model={model}, {seconds}s/{size}/{aspect}）')
    return poll(video_id, model=model, out=out)


def main():
    p = argparse.ArgumentParser(description='AGNES 文生视频')
    p.add_argument('--prompt', help='视频描述提示词（与 --poll 二选一）')
    p.add_argument('--poll', help='恢复轮询一个已创建的任务 ID（限流中断后用）')
    p.add_argument('-o', '--out', default='agnes_video.mp4', help='输出 mp4 路径')
    p.add_argument('--model', default=DEFAULT_MODEL)
    p.add_argument('--seconds', default='5', help='时长 4-12 秒（默认 5）')
    p.add_argument('--size', default='720P', help='720P / 1080P / 1K / 2K')
    p.add_argument('--aspect', default='9:16', help='16:9 / 9:16 / 1:1 等（默认 9:16 竖屏）')
    a = p.parse_args()
    if a.poll:
        poll(a.poll, model=a.model, out=a.out)
        return
    if not a.prompt:
        p.error('需要 --prompt 或 --poll')
    generate(a.prompt, model=a.model, seconds=a.seconds, size=a.size, aspect=a.aspect, out=a.out)


if __name__ == '__main__':
    main()

"""video_toolkit 回归：video info 的 ffprobe 主路径与 ffmpeg 正则兜底

历史缺陷：get_info 曾把 ffprobe 参数（-show_entries/-of json）传给 ffmpeg，
必然失败后走兜底正则，而裸的 \\d+x\\d+ 会先匹配到流 ID 十六进制 [0x1]，
导致分辨率报 0x1、帧率恒为 30。
"""

import json

import core.video_toolkit as vtm
from core.video_toolkit import VideoToolkit


class _FakeCompleted:
    def __init__(self, stdout: bytes, stderr: bytes = b''):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = 0


FFPROBE_PAYLOAD = json.dumps({
    'streams': [{'width': 320, 'height': 240, 'r_frame_rate': '15/1'}],
    'format': {'duration': '1.0'},
}).encode('utf-8')

# 模拟 ffmpeg -i 输出：流 ID [0x1] 与 avc1/0x31637661 都是分辨率正则的陷阱
FFMPEG_I_OUTPUT = (
    "ffmpeg version 6.1.1-essentials_build-www.gyan.dev Copyright (c) 2000-2023\n"
    "Input #0, mov,mp4,m4a,3gp,3gpp,mjpeg, from 'video.mp4':\n"
    "  Duration: 00:00:01.00, start: 0.000000, bitrate: 305 kb/s\n"
    "  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661),"
    " yuv420p, 320x240, 235 kb/s, 15 fps, 15 tbr, 15 tbn\n"
    "  Stream #0:1[0x2](und): Audio: aac (LC), 44100 Hz, stereo, fltp, 128 kb/s\n"
).encode('utf-8')


def test_get_info_uses_ffprobe_and_parses(monkeypatch):
    vt = VideoToolkit()
    vt._ffprobe_resolved = 'ffprobe'  # 预置探测缓存，跳过 -version 探测
    seen = {}

    def fake_run(cmd, **kwargs):
        seen['cmd'] = cmd
        return _FakeCompleted(FFPROBE_PAYLOAD)

    monkeypatch.setattr(vtm.subprocess, 'run', fake_run)
    info = vt.get_info('video.mp4')

    assert seen['cmd'][0] == 'ffprobe'
    assert info == {'duration': 1.0, 'width': 320, 'height': 240, 'fps': 15.0}


def test_fallback_ignores_hex_stream_ids(monkeypatch):
    vt = VideoToolkit()
    vt._ffprobe_resolved = ''  # 无 ffprobe，走 ffmpeg -i 正则兜底

    monkeypatch.setattr(vtm.subprocess, 'run', lambda cmd, **kw: _FakeCompleted(FFMPEG_I_OUTPUT))
    info = vt.get_info('video.mp4')

    assert info['width'] == 320
    assert info['height'] == 240
    assert info['fps'] == 15.0
    assert info['duration'] == 1.0


def test_ffprobe_unavailable_is_cached(monkeypatch):
    import os
    vt = VideoToolkit()
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(vtm.subprocess, 'run', fake_run)
    assert vt._ffprobe_path() is None
    assert vt._ffprobe_path() is None  # 第二次命中缓存，不再探测
    # ffmpeg 带目录时多试同目录兄弟（ffmpeg.exe 旁的 ffprobe.exe）
    expected = 2 if os.path.dirname(vt.ffmpeg_path) else 1
    assert len(calls) == expected

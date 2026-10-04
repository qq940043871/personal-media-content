"""BGM 合成器 — 生成柔和钢琴风背景音乐（HTML→视频线的本地配乐方案）

用 numpy 合成「和弦琶音 + 低音铺底」的暖色 BGM，直接可给
`media-cli.py video html2video --music` 使用。无需联网、无版权问题。

用法：
    python scripts/synth_bgm.py --out media/bgm_上半生.wav --seconds 66
参数：
    --seconds  时长（默认 66）
    --seed     随机种子（同种子可复现）
"""

import argparse
import wave
import numpy as np

SR = 44100

# 和弦进行：C – G – Am – F（每个和弦 2 小节，72bpm）
CHORDS = [
    ('C3', ['C4', 'E4', 'G4', 'C5']),
    ('G2', ['G3', 'B3', 'D4', 'G4']),
    ('A2', ['A3', 'C4', 'E4', 'A4']),
    ('F2', ['F3', 'A3', 'C4', 'F4']),
]
NOTE_SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def freq(note):
    """'C4' → 频率 Hz（A4=440）"""
    name, octv = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((NOTE_SEMI[name] + (octv - 4) * 12 - 9) / 12)


def pluck(f, dur, amp):
    """琶音单音：基频 + 二/三次谐波，指数衰减（模拟轻拨弦）"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.exp(-t * 3.2) * np.minimum(1.0, t / 0.012)   # 快起慢衰
    wave_ = (np.sin(2 * np.pi * f * t)
             + 0.38 * np.sin(2 * np.pi * f * 2 * t)
             + 0.16 * np.sin(2 * np.pi * f * 3 * t))
    return amp * env * wave_


def pad(f, dur, amp):
    """铺底长音：双振荡器轻微失谐 + 慢起慢收"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.minimum(1.0, t / 1.2) * np.minimum(1.0, (dur - t) / 1.2)
    env = np.clip(env, 0, 1)
    wave_ = (np.sin(2 * np.pi * f * 0.998 * t)
             + np.sin(2 * np.pi * f * 1.003 * t)
             + 0.5 * np.sin(2 * np.pi * f / 2 * t))
    return amp * env * wave_ / 2.5


def synth(seconds, seed=7):
    rng = np.random.default_rng(seed)
    bpm = 72
    eighth = 60 / bpm / 2            # 八分音符时长
    bar = eighth * 8                 # 4/4 一小节
    chord_len = bar * 2              # 每和弦 2 小节
    total = np.zeros(int(seconds * SR) + SR)

    t0 = 0.0
    ci = 0
    while t0 < seconds:
        root, arp = CHORDS[ci % len(CHORDS)]
        # 琶音型：1-3-5-8-5-3 循环，八分音符
        pattern = [0, 1, 2, 3, 2, 1]
        k = 0
        t = t0
        while t < t0 + chord_len and t < seconds:
            note = arp[pattern[k % len(pattern)]]
            amp = 0.16 * (0.85 + 0.3 * rng.random())
            seg = pluck(freq(note), eighth * 2.4, amp)
            i = int(t * SR)
            total[i:i + len(seg)] += seg
            t += eighth
            k += 1
        # 低音根音铺底
        seg = pad(freq(root), chord_len, 0.22)
        i = int(t0 * SR)
        total[i:i + len(seg)] += seg
        t0 += chord_len
        ci += 1

    total = total[:int(seconds * SR)]
    # 淡入淡出 + 峰值归一
    fade_in = int(3.0 * SR)
    fade_out = int(5.0 * SR)
    total[:fade_in] *= np.linspace(0, 1, fade_in)
    total[-fade_out:] *= np.linspace(1, 0, fade_out)
    total *= 0.30 / max(1e-9, np.abs(total).max())
    return total


def main():
    ap = argparse.ArgumentParser(description='合成柔和钢琴风 BGM（wav）')
    ap.add_argument('--out', required=True, help='输出 wav 路径')
    ap.add_argument('--seconds', type=float, default=66)
    ap.add_argument('--seed', type=int, default=7)
    args = ap.parse_args()

    audio = synth(args.seconds, args.seed)
    stereo = np.stack([audio, audio], axis=1)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(args.out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'BGM 已生成: {args.out}（{args.seconds}s, 44.1kHz 16bit）')


if __name__ == '__main__':
    main()

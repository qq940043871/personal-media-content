import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.asr_processor import ASRProcessor

def test_asr_local(audio_path=None):
    """测试本地ASR语音转写功能"""
    print("=" * 50)
    print("步骤2/3: 测试本地ASR语音转写模块 (Whisper)")
    print("=" * 50)

    config.ensure_directories()

    asr_processor = ASRProcessor()

    if not audio_path:
        audio_files = glob.glob(os.path.join(config.OUTPUT_AUDIO_DIR, '*.mp3'))
        if not audio_files:
            audio_files = glob.glob(os.path.join(config.OUTPUT_AUDIO_DIR, '*.wav'))
        if not audio_files:
            audio_files = glob.glob(os.path.join(config.OUTPUT_AUDIO_DIR, '*.m4a'))
        if not audio_files:
            print(f"错误: 音频目录 {config.OUTPUT_AUDIO_DIR} 中没有音频文件")
            print("请先运行 test_video.py 生成音频文件")
            return None
        audio_path = audio_files[0]

    if not os.path.exists(audio_path):
        print(f"错误: 音频文件不存在: {audio_path}")
        return None

    audio_size = os.path.getsize(audio_path)
    print(f"测试音频: {audio_path}")
    print(f"音频大小: {audio_size / 1024 / 1024:.2f}MB")
    print(f"\n当前配置:")
    print(f"  模型大小: {config.ASR_LOCAL_MODEL_SIZE}")
    print(f"  设备: {config.ASR_LOCAL_DEVICE}")
    print(f"  模型下载目录: {config.ASR_LOCAL_DOWNLOAD_ROOT}")

    print("\n2.1 使用本地Whisper模型进行语音转写...")
    result = asr_processor.transcribe_local(audio_path, language='zh')

    if result and result.get('success'):
        text = result.get('text', '')
        print(f"\n  转写成功!")
        print(f"  检测语言: {result.get('language')} (概率: {result.get('language_probability', 0):.2%})")
        print(f"  转写文本长度: {len(text)}字符")
        print(f"  文本预览: {text[:200]}...")

        segments = result.get('segments', [])
        if segments:
            print(f"  时间戳段落: {len(segments)}个")
            print(f"  前3个段落预览:")
            for i, seg in enumerate(segments[:3]):
                print(f"    [{asr_processor._format_srt_time(seg['start'])} -> {asr_processor._format_srt_time(seg['end'])}] {seg['text']}")

        print("\n2.2 保存转写结果到文件...")
        saved_paths = asr_processor.save_local_transcript(audio_path, result)
        if saved_paths:
            print(f"  转写结果已保存:")
            print(f"    文本: {saved_paths.get('txt_path')}")
            if saved_paths.get('srt_path'):
                print(f"    字幕: {saved_paths.get('srt_path')}")

        print("\n2.3 测试生成SRT字幕文件...")
        srt_output = os.path.join(config.OUTPUT_AUDIO_TXT_DIR,
                                   os.path.splitext(os.path.basename(audio_path))[0] + '_test.srt')
        srt_result = asr_processor.transcribe_local_with_srt(audio_path, srt_output)
        if srt_result.get('srt_path'):
            print(f"  SRT字幕文件: {srt_result.get('srt_path')}")

    else:
        print(f"\n  错误: 语音转写失败")
        if result:
            print(f"  错误信息: {result.get('error', '未知错误')}")
        return None

    print("\n[OK] 本地ASR语音转写测试通过!")
    return result

if __name__ == '__main__':
    audio_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = test_asr_local(audio_path)
    if result:
        print(f"\n转写结果:")
        print(f"  文本长度: {len(result.get('text', ''))}字符")
        print(f"  段落数量: {len(result.get('segments', []))}")

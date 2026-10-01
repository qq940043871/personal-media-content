import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.asr_processor import ASRProcessor

def test_asr_processor(audio_path=None):
    """测试语音转写功能"""
    print("=" * 50)
    print("步骤2/3: 测试语音转写模块")
    print("=" * 50)
    
    config.ensure_directories()
    
    asr_processor = ASRProcessor()
    
    if not audio_path:
        audio_files = glob.glob(os.path.join(config.OUTPUT_AUDIO_DIR, '*.mp3'))
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
    
    print("\n2.1 调用小米ASR API进行语音转写...")
    result = asr_processor.transcribe(audio_path)
    
    if result and result.get('success'):
        text = result.get('text', '')
        print(f"\n  转写成功!")
        print(f"  转写文本长度: {len(text)}字符")
        print(f"  文本预览: {text[:200]}...")
        
        segments = result.get('segments', [])
        if segments:
            print(f"  时间戳段落: {len(segments)}个")
        
        print("\n2.2 保存转写结果到文件...")
        output_path = asr_processor.save_transcript_to_file(audio_path, result)
        if output_path:
            print(f"  转写结果已保存: {output_path}")
    else:
        print(f"\n  错误: 语音转写失败")
        if result:
            print(f"  错误信息: {result.get('error', '未知错误')}")
        return None
    
    print("\n[OK] 语音转写测试通过!")
    return result

if __name__ == '__main__':
    audio_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = test_asr_processor(audio_path)
    if result:
        print(f"\n转写结果:")
        print(f"  文本长度: {len(result.get('text', ''))}字符")
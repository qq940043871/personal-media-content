import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.video_processor import VideoProcessor

def test_video_processor():
    """测试视频处理功能"""
    print("=" * 50)
    print("步骤1/3: 测试视频处理模块")
    print("=" * 50)
    
    config.ensure_directories()
    
    video_processor = VideoProcessor()
    
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(config.INPUT_VIDEO_DIR, f'*{ext}')))
        video_files.extend(glob.glob(os.path.join(config.INPUT_VIDEO_DIR, f'*{ext.upper()}')))
    
    if not video_files:
        print(f"错误: 输入目录 {config.INPUT_VIDEO_DIR} 中没有视频文件")
        return None
    
    test_video = video_files[0]
    print(f"使用测试视频: {test_video}")
    
    print("\n1.1 获取视频信息...")
    video_info = video_processor.get_video_info(test_video)
    if video_info:
        print(f"  视频时长: {video_info.get('duration', 0):.2f}秒")
        print(f"  视频分辨率: {video_info.get('width', 0)}x{video_info.get('height', 0)}")
        print(f"  帧率: {video_info.get('fps', 0)}fps")
    else:
        print("  警告: 获取视频信息失败，但不影响后续处理")
    
    print("\n1.2 提取关键帧...")
    video_name = os.path.splitext(os.path.basename(test_video))[0]
    frames_dir = os.path.join(config.OUTPUT_FRAMES_DIR, video_name)
    frames_result = video_processor.extract_key_frames(test_video, frames_dir)
    if frames_result.get('success'):
        print(f"  成功提取 {frames_result.get('frame_count', 0)} 个关键帧")
        if frames_result.get('frames'):
            print(f"  保存目录: {frames_dir}")
    else:
        print(f"  错误: {frames_result.get('error', '未知错误')}")
        return None
    
    print("\n1.3 提取音频...")
    audio_result = video_processor.extract_audio(test_video, config.OUTPUT_AUDIO_DIR)
    if audio_result.get('success'):
        print(f"  音频文件: {audio_result.get('audio_path')}")
        audio_size = os.path.getsize(audio_result.get('audio_path', ''))
        print(f"  音频大小: {audio_size / 1024 / 1024:.2f}MB")
    else:
        print(f"  错误: {audio_result.get('error', '未知错误')}")
        return None
    
    result = {
        'video_path': test_video,
        'video_info': video_info,
        'frames': frames_result.get('frames', []),
        'frame_count': frames_result.get('frame_count', 0),
        'audio_path': audio_result.get('audio_path'),
        'success': True
    }
    
    print("\n✓ 视频处理测试通过!")
    return result

if __name__ == '__main__':
    result = test_video_processor()
    if result:
        print(f"\n测试结果: {result}")
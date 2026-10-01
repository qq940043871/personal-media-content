"""单独为已有视频数据生成文章的脚本"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.llm_processor import LLMProcessor

# 视频信息
video_relative_path = "飞天闪客/2024-12-29 23-33-38_你管这破玩意叫网络___video"
video_name = "2024-12-29 23-33-38_你管这破玩意叫网络___video"

# 构建实际路径
base_output_dir = os.path.join(config.BASE_DIR, 'output')
video_output_dir = os.path.join(base_output_dir, video_relative_path)

# 检查各目录
frames_dir = os.path.join(video_output_dir, 'frames')
audio_dir = os.path.join(video_output_dir, 'audio')
audio_txt_dir = os.path.join(video_output_dir, 'audio_txt')
articles_dir = os.path.join(video_output_dir, 'articles')

print(f"视频输出目录: {video_output_dir}")
print(f"帧目录存在: {os.path.exists(frames_dir)}")
print(f"音频目录存在: {os.path.exists(audio_dir)}")
print(f"转写文本目录存在: {os.path.exists(audio_txt_dir)}")
print(f"文章目录存在: {os.path.exists(articles_dir)}")

# 读取转写文本
txt_file = os.path.join(audio_txt_dir, f"{video_name}.txt")
if not os.path.exists(txt_file):
    print(f"错误: 转写文本不存在 {txt_file}")
    sys.exit(1)

with open(txt_file, 'r', encoding='utf-8') as f:
    text = f.read()
print(f"转写文本长度: {len(text)} 字符")

# 获取帧列表
frames = []
if os.path.exists(frames_dir):
    frame_files = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
    frame_files.sort()
    frames = [os.path.join(frames_dir, f) for f in frame_files]
print(f"帧数量: {len(frames)}")

# 生成文章
llm_processor = LLMProcessor()

print("\n开始生成文章...")
try:
    save_path = os.path.join(articles_dir, f"{video_name}.md")
    article_result = llm_processor.generate_full_article_stream({
        'transcript': text,
        'frames': frames,
        'video_info': {'duration': 0}
    }, save_path=save_path)

    if article_result.get('success'):
        print(f"\n文章生成成功: {save_path}")
    else:
        print(f"\n文章生成失败: {article_result.get('error', '未知错误')}")

except Exception as e:
    print(f"\n处理过程中发生错误: {e}")
    import traceback
    traceback.print_exc()
import os
import sys
import glob
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config

def parse_srt(srt_path):
    """解析SRT字幕文件"""
    segments = []
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            text_lines = lines[2:]
            text = ' '.join(text_lines)
            
            start_end = time_line.split(' --> ')
            if len(start_end) == 2:
                start_time = start_end[0]
                end_time = start_end[1]
                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })
    
    return segments

def select_key_frames(frame_dir, segments, max_images=20):
    """选择关键帧图片"""
    frame_files = sorted(glob.glob(os.path.join(frame_dir, '*.jpg')))
    
    if not frame_files:
        return []
    
    if len(frame_files) <= max_images:
        return frame_files
    
    selected = []
    total_frames = len(frame_files)
    segment_count = len(segments)
    
    for i in range(max_images):
        idx = int((i / (max_images - 1)) * (total_frames - 1))
        selected.append(frame_files[idx])
    
    return selected

def generate_lark_doc_xml(srt_path, frame_dir, title="你管这破玩意叫网络"):
    """生成飞书文档XML内容"""
    segments = parse_srt(srt_path)
    key_frames = select_key_frames(frame_dir, segments, max_images=15)
    
    xml_parts = []
    xml_parts.append(f'<title>{title}</title>')
    
    xml_parts.append('<p>本文基于视频转写内容整理，深入浅出地讲解了计算机网络基础知识。</p>')
    xml_parts.append('<hr/>')
    
    frame_idx = 0
    current_section = []
    
    for i, seg in enumerate(segments):
        current_section.append(seg['text'])
        
        if len(current_section) >= 5 or i == len(segments) - 1:
            section_text = ''.join(current_section)
            
            if frame_idx < len(key_frames):
                frame_path = key_frames[frame_idx]
                frame_name = os.path.basename(frame_path)
                
                xml_parts.append(f'<img src="{frame_path}" caption="{frame_name}" name="{frame_name}"/>')
                frame_idx += 1
            
            xml_parts.append(f'<p>{section_text}</p>')
            xml_parts.append('<hr/>')
            current_section = []
    
    xml_parts.append('<p><b>总结</b></p>')
    xml_parts.append('<p>本文通过生动的比喻，从两台电脑的直连开始，逐步介绍了集线器、交换机、路由器等网络设备的工作原理，以及MAC地址、IP地址、子网掩码、ARP协议等核心概念。</p>')
    
    return '\n'.join(xml_parts)

def create_lark_document(content, parent_token=None):
    """创建飞书文档"""
    cmd = ['lark-cli', 'docs', '+create', '--api-version', 'v2', '--content', content]
    
    if parent_token:
        cmd.extend(['--parent', parent_token])
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("飞书文档创建成功!")
        print(result.stdout)
        return result.stdout
    else:
        print(f"创建失败: {result.stderr}")
        return None

def main():
    print("=" * 60)
    print("步骤3/3: 生成图文并茂的飞书文档")
    print("=" * 60)
    
    srt_path = r"d:\ai_coder\p000_llm_video_ark\audio_txt\2024-12-29 23-33-38_你管这破玩意叫网络___video.srt"
    frame_dir = r"d:\ai_coder\p000_llm_video_ark\frames\2024-12-29 23-33-38_你管这破玩意叫网络___video"
    
    if not os.path.exists(srt_path):
        print(f"错误: SRT文件不存在: {srt_path}")
        return
    
    if not os.path.exists(frame_dir):
        print(f"错误: 帧目录不存在: {frame_dir}")
        return
    
    print(f"\n3.1 解析SRT字幕文件...")
    segments = parse_srt(srt_path)
    print(f"  解析到 {len(segments)} 个字幕段落")
    
    print(f"\n3.2 选择关键帧图片...")
    key_frames = select_key_frames(frame_dir, segments)
    print(f"  选择了 {len(key_frames)} 张关键帧")
    
    print(f"\n3.3 生成飞书文档XML内容...")
    xml_content = generate_lark_doc_xml(srt_path, frame_dir)
    print(f"  XML内容生成完成，长度: {len(xml_content)} 字符")
    
    print(f"\n3.4 创建飞书文档...")
    doc_url = create_lark_document(xml_content)
    
    if doc_url:
        print("\n[OK] 飞书文档创建完成!")
    else:
        print("\n[ERROR] 飞书文档创建失败!")

if __name__ == '__main__':
    main()
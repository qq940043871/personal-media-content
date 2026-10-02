#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def parse_srt_to_text(srt_path, output_txt_path=None):
    """
    解析SRT字幕文件，提取纯文本内容
    
    Args:
        srt_path: SRT字幕文件路径
        output_txt_path: 输出文本文件路径，若为None则返回文本内容
    
    Returns:
        纯文本内容字符串
    """
    # 读取SRT文件
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # SRT格式：序号 + 时间戳 + 文本 + 空行
    # 使用正则表达式匹配并提取文本内容
    # 模式：序号\n时间戳\n文本\n\n
    pattern = r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(.+?)(?=\n\n|\n\d+\n|$)'
    
    matches = re.findall(pattern, content, re.DOTALL)
    
    # 将所有文本片段拼接
    text_parts = []
    for match in matches:
        # 去除多余的换行符，合并为单行
        clean_text = match.replace('\n', ' ').strip()
        if clean_text:
            text_parts.append(clean_text)
    
    full_text = ' '.join(text_parts)
    
    # 如果指定了输出路径，保存为文件
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"纯文本已保存到: {output_txt_path}")
    
    return full_text

def parse_srt_with_timestamps(srt_path):
    """
    解析SRT字幕文件，保留时间戳信息
    
    Args:
        srt_path: SRT字幕文件路径
    
    Returns:
        包含时间戳和文本的列表
    """
    segments = []
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按空行分割各个字幕块
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # 序号
            try:
                index = int(lines[0])
            except:
                index = None
            
            # 时间戳
            time_line = lines[1]
            time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
            if time_match:
                start_time = time_match.group(1)
                end_time = time_match.group(2)
            else:
                start_time = None
                end_time = None
            
            # 文本内容
            text_lines = lines[2:]
            text = ' '.join(text_lines).strip()
            
            if text:
                segments.append({
                    'index': index,
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })
    
    return segments

if __name__ == '__main__':
    # SRT文件路径
    srt_file = r'd:\ai_coder\p000_llm_video_ark\audio_txt\2024-12-29 23-33-38_你管这破玩意叫网络___video.srt'
    
    # 输出纯文本文件路径
    output_file = r'd:\ai_coder\p000_llm_video_ark\audio_txt\2024-12-29 23-33-38_你管这破玩意叫网络___video.txt'
    
    print(f"正在解析SRT文件: {srt_file}")
    print("=" * 60)
    
    # 解析并保存纯文本
    full_text = parse_srt_to_text(srt_file, output_file)
    
    # 打印预览
    print("\n纯文本预览（前500字符）:")
    print("-" * 60)
    print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
    print("\n" + "=" * 60)
    print(f"总字符数: {len(full_text)}")
    print(f"总字数: {len(full_text.replace(' ', '').replace('，', '').replace('。', '').replace('？', '').replace('！', ''))}")
    
    # 也可以获取带时间戳的分段内容
    # segments = parse_srt_with_timestamps(srt_file)
    # print(f"\n共解析到 {len(segments)} 个字幕片段")
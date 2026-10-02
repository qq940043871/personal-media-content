import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.llm_processor import LLMProcessor

def test_llm_processor(transcript_text=None, video_info=None, frames=None):
    """测试大模型文章生成功能"""
    print("=" * 50)
    print("步骤3/3: 测试大模型文章生成模块")
    print("=" * 50)
    
    llm_processor = LLMProcessor()
    
    if not transcript_text:
        transcript_text = "今天我们来学习计算机网络的基础知识。网络是现代信息技术的核心，它使得全球范围内的数据传输成为可能。首先，我们需要了解OSI七层模型，这是一个概念框架，将网络通信分为七个层次：物理层、数据链路层、网络层、传输层、会话层、表示层和应用层。每一层都有其特定的功能和协议。"
        print(f"使用默认测试文本: {transcript_text[:50]}...")
    else:
        print(f"转写文本长度: {len(transcript_text)}字符")
    
    print(f"视频信息: {video_info if video_info else '无'}")
    print(f"关键帧数量: {len(frames) if frames else 0}")
    
    print("\n3.1 测试生成摘要...")
    summary_result = llm_processor.generate_summary(transcript_text)
    if summary_result and summary_result.get('success'):
        print(f"  摘要生成成功")
        print(f"  摘要内容: {summary_result.get('summary', '')[:100]}...")
    else:
        print(f"  警告: 摘要生成失败，继续测试其他功能")
    
    print("\n3.2 测试生成大纲...")
    outline_result = llm_processor.generate_outline(transcript_text)
    if outline_result and outline_result.get('success'):
        print(f"  大纲生成成功")
        outline = outline_result.get('outline', [])
        if outline:
            print(f"  大纲章节: {len(outline)}个")
            for i, item in enumerate(outline[:3], 1):
                print(f"    {i}. {item}")
    else:
        print(f"  警告: 大纲生成失败，继续测试其他功能")
    
    print("\n3.3 测试生成完整文章(流式输出)...")
    video_data = {
        'text': transcript_text,
        'video_info': video_info or {},
        'frames': frames or []
    }
    
    print("  开始流式生成文章...")
    print("  " + "-" * 40)
    article_result = llm_processor.generate_full_article_stream(video_data)
    print("  " + "-" * 40)
    
    if article_result and article_result.get('success'):
        print(f"\n  文章生成成功!")
        content = article_result.get('article', '')
        print(f"  文章长度: {len(content)}字符")
        
        keywords = article_result.get('keywords', [])
        if keywords:
            print(f"  关键词: {', '.join(keywords)}")
        
        print("\n3.4 保存文章到文件...")
        output_path = llm_processor.save_article_to_file(article_result)
        if output_path:
            print(f"  文章已保存: {output_path}")
    else:
        print(f"\n  错误: 文章生成失败")
        if article_result:
            print(f"  错误信息: {article_result.get('error', '未知错误')}")
        return None
    
    print("\n[OK] 文章生成测试通过!")
    return article_result

if __name__ == '__main__':
    test_text = sys.argv[1] if len(sys.argv) > 1 else None
    result = test_llm_processor(test_text)
    if result:
        print(f"\n文章生成结果:")
        print(f"  标题: {result.get('title', '未命名')}")
        print(f"  内容长度: {len(result.get('content', ''))}字符")
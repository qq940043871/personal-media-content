import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.feishu_publisher import FeishuPublisher, generate_article_images


def test_feishu_publisher(video_name=None, article_path=None):
    print("=" * 50)
    print("测试飞书文档发布模块")
    print("=" * 50)
    
    config.ensure_directories()
    
    publisher = FeishuPublisher()
    
    if not article_path:
        article_files = glob.glob(os.path.join(config.OUTPUT_ARTICLES_DIR, '*.md'))
        if not article_files:
            print(f"错误: 文章目录 {config.OUTPUT_ARTICLES_DIR} 中没有文章文件")
            print("请先运行 test_llm.py 生成文章文件")
            return None
        article_path = article_files[0]
    
    if not os.path.exists(article_path):
        print(f"错误: 文章文件不存在: {article_path}")
        return None
    
    print(f"文章文件: {article_path}")
    
    with open(article_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    first_line = content.split('\n')[0]
    if first_line.startswith('# '):
        title = first_line[2:].strip()
    else:
        title = os.path.splitext(os.path.basename(article_path))[0]
    
    print(f"文章标题: {title}")
    print(f"文章长度: {len(content)}字符")
    
    if not video_name:
        video_dirs = glob.glob(os.path.join(config.OUTPUT_FRAMES_DIR, '*'))
        if video_dirs:
            video_name = os.path.basename(video_dirs[0])
    
    images = []
    if video_name:
        print(f"\n查找视频帧: {video_name}")
        images = generate_article_images(video_name, max_frames=5)
        print(f"找到 {len(images)} 张图片")
    
    print("\n开始发布到飞书...")
    result = publisher.publish_article(title, content, images)
    
    if result.get('success'):
        print(f"\n[OK] 飞书文档发布成功!")
        print(f"文档链接: {result.get('doc_url')}")
        print(f"插入图片: {result.get('images_count')} 张")
    else:
        print(f"\n[ERROR] 飞书文档发布失败: {result.get('error')}")
        return None
    
    return result


if __name__ == '__main__':
    video_name = sys.argv[1] if len(sys.argv) > 1 else None
    article_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = test_feishu_publisher(video_name, article_path)
    
    if result:
        print(f"\n发布结果:")
        print(f"  文档ID: {result.get('doc_id')}")
        print(f"  文档链接: {result.get('doc_url')}")

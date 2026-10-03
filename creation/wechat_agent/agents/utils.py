"""
文件与路径工具函数
"""
import datetime
import base64
import requests
from pathlib import Path


def sanitize_filename(title: str) -> str:
    """将文章标题转换为安全的文件名"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')
    return title.strip()[:50]


def get_article_dir(title: str) -> Path:
    """
    为文章创建独立的目录并返回路径

    目录结构:
        output/
            YYYYMMDD_HHMMSS_标题/
                article.md
                article.html
                cover.png
                log.txt
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = sanitize_filename(title)
    article_dir = Path("output") / f"{timestamp}_{safe_title}"
    article_dir.mkdir(parents=True, exist_ok=True)
    return article_dir


def save_text_to_file(content: str, filepath: Path, description: str = ""):
    """保存文本内容到文件并输出日志"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        if description:
            print(f"[SAVE] {description} 已保存到: {filepath}")
        return True
    except Exception as e:
        print(f"[WARN] 保存文件失败 {filepath}: {e}")
        return False


def save_image(image_data, filepath: Path, description: str = ""):
    """
    保存图片到文件，支持 bytes / base64 字符串 / URL

    Args:
        image_data: 图片数据 —— bytes/base64 str/http URL
        filepath: 保存路径
        description: 日志描述
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if image_data is None:
            print(f"[WARN] 保存图片失败 {filepath}: 图片数据为 None")
            return False

        if isinstance(image_data, bytes):
            raw = image_data
        elif isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                resp = requests.get(image_data, timeout=30)
                resp.raise_for_status()
                raw = resp.content
            else:
                b64_str = image_data
                if "," in b64_str:
                    b64_str = b64_str.split(",")[1]
                raw = base64.b64decode(b64_str.strip())
        else:
            print(f"[WARN] 保存图片失败 {filepath}: 不支持的数据类型 {type(image_data)}")
            return False

        with open(str(filepath), "wb") as f:
            f.write(raw)

        if description:
            print(f"[SAVE] {description} 已保存到: {filepath} ({len(raw)} bytes)")
        return True
    except Exception as e:
        print(f"[WARN] 保存图片失败 {filepath}: {e}")
        return False


def log_llm_response(content: str, content_type: str, article_dir: Path):
    """记录大模型返回的内容到日志文件"""
    log_file = article_dir / "log.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = f"""
{'='*80}
[{timestamp}] {content_type}
{'='*80}
{content}
{'='*80}

"""
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        print(f"[NOTE] {content_type} 已记录到日志")
    except Exception as e:
        print(f"[WARN] 记录日志失败: {e}")
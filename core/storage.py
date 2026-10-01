"""
素材存储管理 — 统一管理所有内容资产的路径、归档、检索

功能：
- 统一目录结构
- 素材标签化（预留）
- 幂等性检查（文件是否已存在）
- 路径工具函数

使用方式：
    from core.storage import Storage
    storage = Storage()

    # 平台素材库中的小说项目路径（storage/novels/<name>，与 hello_novel 正文目录分离）
    novel_dir = storage.novel_dir('cangyuantu')

    # 检查文件是否已处理（幂等）
    if not storage.exists(output_path):
        do_process()

    # 列出某类所有素材
    videos = storage.list_videos()
"""

import os
import glob
from .config import config


class Storage:
    """统一存储管理器"""

    def __init__(self, base_dir=None):
        self.base_dir = base_dir or config.STORAGE_BASE
        self._ensure_dirs()

    def _ensure_dirs(self):
        config.ensure_base_directories()

    # ===== 路径快捷方式 =====

    @property
    def video_input_dir(self):
        return config.STORAGE_VIDEO_INPUT

    @property
    def video_output_dir(self):
        return config.STORAGE_VIDEO_OUTPUT

    @property
    def articles_dir(self):
        return config.STORAGE_ARTICLES

    @property
    def novels_dir(self):
        return config.STORAGE_NOVELS

    def novel_dir(self, project_name):
        """获取小说项目目录"""
        path = os.path.join(self.novels_dir, project_name)
        os.makedirs(path, exist_ok=True)
        return path

    def video_output_dir_for(self, video_name):
        """获取视频产物目录（兼容 config 同名方法）"""
        return config.get_video_output_dir(video_name)

    # ===== 幂等检查 =====

    @staticmethod
    def exists(path):
        """检查文件/目录是否存在"""
        return os.path.exists(path)

    @staticmethod
    def is_file_empty(path):
        """检查文件是否存在且非空"""
        return os.path.exists(path) and os.path.getsize(path) > 0

    # ===== 列表查询 =====

    def list_videos(self, subdir=''):
        """列出输入视频"""
        video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
        search_dir = os.path.join(self.video_input_dir, subdir) if subdir else self.video_input_dir
        videos = []
        for root, dirs, files in os.walk(search_dir):
            for f in files:
                if f.lower().endswith(video_exts):
                    videos.append(os.path.join(root, f))
        return sorted(videos)

    def list_articles(self):
        """列出所有已生成文章"""
        articles = []
        for root, dirs, files in os.walk(self.articles_dir):
            for f in files:
                if f.endswith('.md'):
                    articles.append(os.path.join(root, f))
        # 同时搜索视频输出目录中的文章
        for root, dirs, files in os.walk(self.video_output_dir):
            for f in files:
                if f.endswith('.md') and '/articles/' in root.replace('\\', '/'):
                    articles.append(os.path.join(root, f))
        return sorted(articles)

    def list_novel_projects(self):
        """列出所有小说项目"""
        if not os.path.exists(self.novels_dir):
            return []
        return sorted([
            d for d in os.listdir(self.novels_dir)
            if os.path.isdir(os.path.join(self.novels_dir, d))
        ])

    # ===== 统计 =====

    def stats(self):
        """快速统计各存储区的文件数量"""
        return {
            'videos_input': len(self.list_videos()),
            'articles': len(self.list_articles()),
            'novel_projects': len(self.list_novel_projects()),
        }

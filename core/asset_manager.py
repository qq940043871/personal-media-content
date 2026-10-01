"""
素材资产管理 — 统一标签、索引、检索、复用

功能：
- 素材注册与标签化（小说章节、视频片段、分镜图、文章等）
- 按标签/类型/项目检索素材
- 素材关联（如：章节 → 分镜 → 视频 → 文章）
- 素材统计
- 使用 SQLite 存储元数据，文件仍在原位置

使用方式：
    from core.asset_manager import AssetManager
    am = AssetManager()

    # 注册素材
    am.register_asset(
        path='hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt',
        asset_type='novel_chapter',
        project='沧元图',
        tags=['玄幻', '第一章', '主角出场'],
        metadata={'chapter_num': 1, 'word_count': 2000}
    )

    # 按标签检索
    assets = am.search_by_tags(['玄幻', '高潮'])

    # 查看关联
    related = am.get_related_assets(asset_id)

    # 统计
    stats = am.stats()
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from .config import config


class AssetManager:
    """素材资产管理器（基于 SQLite）"""

    # 素材类型枚举
    TYPE_NOVEL_CHAPTER = 'novel_chapter'     # 小说章节
    TYPE_NOVEL_OUTLINE = 'novel_outline'     # 小说大纲
    TYPE_VIDEO_CLIP = 'video_clip'           # 视频片段
    TYPE_VIDEO_FULL = 'video_full'           # 完整视频
    TYPE_IMAGE_STORYBOARD = 'image_storyboard'  # 分镜图
    TYPE_IMAGE_COVER = 'image_cover'         # 封面图
    TYPE_ARTICLE_FEISHU = 'article_feishu'   # 飞书文章
    TYPE_ARTICLE_WECHAT = 'article_wechat'   # 公众号文章
    TYPE_SCRIPT = 'script'                   # 分镜脚本
    TYPE_AUDIO = 'audio'                     # 音频

    ALL_TYPES = [
        TYPE_NOVEL_CHAPTER, TYPE_NOVEL_OUTLINE,
        TYPE_VIDEO_CLIP, TYPE_VIDEO_FULL,
        TYPE_IMAGE_STORYBOARD, TYPE_IMAGE_COVER,
        TYPE_ARTICLE_FEISHU, TYPE_ARTICLE_WECHAT,
        TYPE_SCRIPT, TYPE_AUDIO,
    ]

    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.path.join(config.STORAGE_BASE, 'db')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'assets.db')

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 素材表
        c.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                project TEXT DEFAULT '',
                title TEXT DEFAULT '',
                description TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                file_size INTEGER DEFAULT 0,
                created_at REAL,
                updated_at REAL
            )
        ''')

        # 标签表（加速标签检索）
        c.execute('''
            CREATE TABLE IF NOT EXISTS asset_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (asset_id) REFERENCES assets (id) ON DELETE CASCADE
            )
        ''')

        # 关联表（素材之间的关系）
        c.execute('''
            CREATE TABLE IF NOT EXISTS asset_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_asset_id INTEGER NOT NULL,
                to_asset_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at REAL,
                FOREIGN KEY (from_asset_id) REFERENCES assets (id) ON DELETE CASCADE,
                FOREIGN KEY (to_asset_id) REFERENCES assets (id) ON DELETE CASCADE
            )
        ''')

        # 索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_asset_tags_tag ON asset_tags(tag)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_asset_tags_asset ON asset_tags(asset_id)')

        conn.commit()
        conn.close()

    # ===== 素材注册与更新 =====

    def register_asset(self, path, asset_type, project='', title='',
                       description='', tags=None, metadata=None):
        """
        注册一个素材

        Returns:
            int: 素材 ID
        """
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}

        # 规范化路径
        abs_path = os.path.abspath(path)
        file_size = 0
        if os.path.exists(abs_path):
            file_size = os.path.getsize(abs_path)

        now = time.time()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 检查是否已存在（按路径）
        c.execute('SELECT id FROM assets WHERE path = ?', (abs_path,))
        row = c.fetchone()

        if row:
            # 更新
            asset_id = row[0]
            c.execute('''
                UPDATE assets SET
                    asset_type = ?, project = ?, title = ?, description = ?,
                    tags = ?, metadata = ?, file_size = ?, updated_at = ?
                WHERE id = ?
            ''', (
                asset_type, project, title, description,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False),
                file_size, now, asset_id
            ))
            # 重建标签
            c.execute('DELETE FROM asset_tags WHERE asset_id = ?', (asset_id,))
            for tag in tags:
                c.execute(
                    'INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)',
                    (asset_id, tag)
                )
        else:
            # 新增
            c.execute('''
                INSERT INTO assets
                (path, asset_type, project, title, description, tags, metadata,
                 file_size, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                abs_path, asset_type, project, title, description,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False),
                file_size, now, now
            ))
            asset_id = c.lastrowid
            for tag in tags:
                c.execute(
                    'INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)',
                    (asset_id, tag)
                )

        conn.commit()
        conn.close()
        return asset_id

    def update_asset(self, asset_id, **kwargs):
        """更新素材属性"""
        allowed_fields = ['title', 'description', 'project', 'asset_type', 'metadata']
        updates = []
        values = []

        for field in allowed_fields:
            if field in kwargs:
                if field == 'metadata':
                    updates.append(f'{field} = ?')
                    values.append(json.dumps(kwargs[field], ensure_ascii=False))
                else:
                    updates.append(f'{field} = ?')
                    values.append(kwargs[field])

        # tags 单独处理
        if 'tags' in kwargs:
            tags = kwargs['tags']
            updates.append('tags = ?')
            values.append(json.dumps(tags, ensure_ascii=False))

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('DELETE FROM asset_tags WHERE asset_id = ?', (asset_id,))
            for tag in tags:
                c.execute(
                    'INSERT INTO asset_tags (asset_id, tag) VALUES (?, ?)',
                    (asset_id, tag)
                )
            conn.commit()
            conn.close()

        if updates:
            updates.append('updated_at = ?')
            values.append(time.time())
            values.append(asset_id)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                f'UPDATE assets SET {", ".join(updates)} WHERE id = ?',
                tuple(values)
            )
            conn.commit()
            conn.close()

    def delete_asset(self, asset_id):
        """删除素材（只删元数据，不删文件）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        c.execute('DELETE FROM asset_tags WHERE asset_id = ?', (asset_id,))
        c.execute('DELETE FROM asset_relations WHERE from_asset_id = ? OR to_asset_id = ?',
                  (asset_id, asset_id))
        conn.commit()
        conn.close()

    # ===== 检索 =====

    def get_asset(self, asset_id):
        """根据 ID 获取素材"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM assets WHERE id = ?', (asset_id,))
        row = c.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def get_by_path(self, path):
        """根据路径获取素材"""
        abs_path = os.path.abspath(path)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM assets WHERE path = ?', (abs_path,))
        row = c.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def search_by_tags(self, tags, match_all=True, asset_type=None, project=None):
        """
        按标签检索

        Args:
            tags: 标签列表
            match_all: True=所有标签都匹配(AND)，False=任一匹配(OR)
            asset_type: 可选，按类型过滤
            project: 可选，按项目过滤

        Returns:
            list: 素材列表
        """
        if not tags:
            return self.list_assets(asset_type=asset_type, project=project)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if match_all:
            # AND：必须包含所有标签
            placeholders = ','.join(['?'] * len(tags))
            query = f'''
                SELECT a.* FROM assets a
                JOIN asset_tags t ON a.id = t.asset_id
                WHERE t.tag IN ({placeholders})
            '''
            params = list(tags)
            if asset_type:
                query += ' AND a.asset_type = ?'
                params.append(asset_type)
            if project:
                query += ' AND a.project = ?'
                params.append(project)
            query += ' GROUP BY a.id HAVING COUNT(DISTINCT t.tag) = ?'
            params.append(len(tags))
        else:
            # OR：包含任一标签
            placeholders = ','.join(['?'] * len(tags))
            query = f'''
                SELECT DISTINCT a.* FROM assets a
                JOIN asset_tags t ON a.id = t.asset_id
                WHERE t.tag IN ({placeholders})
            '''
            params = list(tags)
            if asset_type:
                query += ' AND a.asset_type = ?'
                params.append(asset_type)
            if project:
                query += ' AND a.project = ?'
                params.append(project)

        query += ' ORDER BY a.updated_at DESC'

        c.execute(query, tuple(params))
        rows = c.fetchall()
        conn.close()

        return [self._row_to_dict(r) for r in rows]

    def list_assets(self, asset_type=None, project=None, limit=100, offset=0):
        """列出素材"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        query = 'SELECT * FROM assets WHERE 1=1'
        params = []

        if asset_type:
            query += ' AND asset_type = ?'
            params.append(asset_type)
        if project:
            query += ' AND project = ?'
            params.append(project)

        query += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        c.execute(query, tuple(params))
        rows = c.fetchall()
        conn.close()

        return [self._row_to_dict(r) for r in rows]

    def list_all_tags(self, project=None):
        """列出所有标签"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if project:
            query = '''
                SELECT DISTINCT t.tag FROM asset_tags t
                JOIN assets a ON t.asset_id = a.id
                WHERE a.project = ?
                ORDER BY t.tag
            '''
            c.execute(query, (project,))
        else:
            c.execute('SELECT DISTINCT tag FROM asset_tags ORDER BY tag')

        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]

    # ===== 关联 =====

    def add_relation(self, from_asset_id, to_asset_id, relation_type):
        """添加素材关联

        relation_type 示例：
        - 'source_of'：A 是 B 的来源（章节 → 分镜）
        - 'generated_from'：B 由 A 生成（视频 → 文章）
        - 'part_of'：A 是 B 的一部分（片段 → 完整视频）
        """
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO asset_relations (from_asset_id, to_asset_id, relation_type, created_at)
            VALUES (?, ?, ?, ?)
        ''', (from_asset_id, to_asset_id, relation_type, now))
        conn.commit()
        conn.close()

    def get_related_assets(self, asset_id, relation_type=None):
        """获取关联素材"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if relation_type:
            c.execute('''
                SELECT a.*, r.relation_type, r.from_asset_id, r.to_asset_id
                FROM asset_relations r
                JOIN assets a ON (r.to_asset_id = a.id AND r.from_asset_id = ?)
                              OR (r.from_asset_id = a.id AND r.to_asset_id = ?)
                WHERE r.relation_type = ?
            ''', (asset_id, asset_id, relation_type))
        else:
            c.execute('''
                SELECT a.*, r.relation_type, r.from_asset_id, r.to_asset_id
                FROM asset_relations r
                JOIN assets a ON (r.to_asset_id = a.id AND r.from_asset_id = ?)
                              OR (r.from_asset_id = a.id AND r.to_asset_id = ?)
            ''', (asset_id, asset_id))

        rows = c.fetchall()
        conn.close()
        return [self._row_to_dict(r, include_relation=True) for r in rows]

    # ===== 统计 =====

    def stats(self):
        """全局统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 总数
        c.execute('SELECT COUNT(*) FROM assets')
        total = c.fetchone()[0]

        # 按类型统计
        c.execute('SELECT asset_type, COUNT(*) FROM assets GROUP BY asset_type')
        by_type = dict(c.fetchall())

        # 按项目统计
        c.execute('SELECT project, COUNT(*) FROM assets WHERE project != "" GROUP BY project')
        by_project = dict(c.fetchall())

        # 标签数
        c.execute('SELECT COUNT(DISTINCT tag) FROM asset_tags')
        tag_count = c.fetchone()[0]

        # 总文件大小
        c.execute('SELECT COALESCE(SUM(file_size), 0) FROM assets')
        total_size = c.fetchone()[0]

        conn.close()

        return {
            'total': total,
            'by_type': by_type,
            'by_project': by_project,
            'tag_count': tag_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
        }

    # ===== 扫描入库（便捷方法）=====

    def scan_novel_project(self, project_name, chapters_dir, file_pattern='*.txt'):
        """
        扫描小说章节目录，批量注册为素材

        Args:
            project_name: 项目名
            chapters_dir: 章节文件目录
            file_pattern: 文件匹配模式

        Returns:
            int: 注册的素材数量
        """
        import glob

        files = sorted(glob.glob(os.path.join(chapters_dir, file_pattern)))
        count = 0

        for filepath in files:
            filename = os.path.basename(filepath)
            # 尝试从文件名提取章节号
            import re
            match = re.search(r'(\d+)', filename)
            chapter_num = int(match.group(1)) if match else 0

            # 读取标题（文件第一行）
            title = filename
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line and len(first_line) < 100:
                        title = first_line.replace('#', '').strip()
            except:
                pass

            file_size = os.path.getsize(filepath)

            self.register_asset(
                path=filepath,
                asset_type=self.TYPE_NOVEL_CHAPTER,
                project=project_name,
                title=title,
                tags=[project_name, '小说', f'第{chapter_num}章'] if chapter_num else [project_name, '小说'],
                metadata={
                    'chapter_num': chapter_num,
                    'word_count': file_size // 2,  # 粗略估算
                    'filename': filename,
                }
            )
            count += 1

        print(f"[AssetManager] 扫描完成，注册了 {count} 个章节素材")
        return count

    # ===== 内部方法 =====

    @staticmethod
    def _row_to_dict(row, include_relation=False):
        d = {
            'id': row['id'],
            'path': row['path'],
            'asset_type': row['asset_type'],
            'project': row['project'],
            'title': row['title'],
            'description': row['description'],
            'tags': json.loads(row['tags']) if row['tags'] else [],
            'metadata': json.loads(row['metadata']) if row['metadata'] else {},
            'file_size': row['file_size'],
            'created_at': datetime.fromtimestamp(row['created_at']).strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
            'updated_at': datetime.fromtimestamp(row['updated_at']).strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
        }
        if include_relation:
            try:
                d['relation_type'] = row['relation_type']
                d['direction'] = 'out' if row['from_asset_id'] == row['id'] else 'in'
            except:
                pass
        return d

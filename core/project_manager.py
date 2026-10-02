"""
项目管理器 — 工作台统一项目模型 + 发布记录（基于 SQLite）

项目类型：
- article 图文文章：正文为 markdown 文件（content_path），可发布飞书 / 公众号
- novel 小说：关联 assets/novels/<book>（book_name），工作台看章节概况
- video 短视频：成片文件（video_path），发布抖音

使用方式：
    from core.project_manager import ProjectManager

    pm = ProjectManager()
    project = pm.create_project('秋日书评', 'article', description='...')
    pm.update_project(project['id'], status='ready')
    pm.list_projects(project_type='article')

    rid = pm.start_publish(project['id'], 'feishu', title='秋日书评')
    pm.finish_publish(rid, 'success', url='https://...')

数据落在 storage/db/projects.db（不入库）。
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from .config import config

PROJECT_TYPES = ('article', 'novel', 'video')
PROJECT_STATUSES = ('draft', 'in_progress', 'ready', 'published', 'archived')
PUBLISH_STATUSES = ('running', 'success', 'failed')

TYPE_LABELS = {'article': '图文文章', 'novel': '小说', 'video': '短视频'}

# update_project 允许修改的字段（白名单，其余忽略）
EDITABLE_FIELDS = ('name', 'status', 'description', 'content_path',
                   'video_path', 'cover_path', 'book_name', 'tags')

_PROJECT_COLS = ('id', 'name', 'project_type', 'status', 'description',
                 'content_path', 'video_path', 'cover_path', 'book_name',
                 'tags', 'created_at', 'updated_at')


class ProjectError(ValueError):
    """项目参数错误（CLI/API 统一转 400）"""


class ProjectManager:
    """项目管理器（基于 SQLite，任务/素材库同款模式）"""

    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.path.join(config.STORAGE_BASE, 'db')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'projects.db')
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                project_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                description TEXT DEFAULT '',
                content_path TEXT DEFAULT '',
                video_path TEXT DEFAULT '',
                cover_path TEXT DEFAULT '',
                book_name TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at REAL,
                updated_at REAL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS publish_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                title TEXT DEFAULT '',
                url TEXT DEFAULT '',
                error TEXT DEFAULT '',
                created_at REAL,
                finished_at REAL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_pub_records_project ON publish_records(project_id)')
        conn.commit()
        conn.close()

    # ===== 项目 CRUD =====

    def create_project(self, name, project_type, description='',
                       content_path='', video_path='', cover_path='',
                       book_name='', tags=None, status='draft'):
        """创建项目；类型/名称非法抛 ProjectError"""
        if project_type not in PROJECT_TYPES:
            raise ProjectError(f'未知项目类型: {project_type}（可选: {", ".join(PROJECT_TYPES)}）')
        name = (name or '').strip()
        if not name:
            raise ProjectError('项目名称不能为空')

        pid = 'p' + str(uuid_token())
        now = time.time()
        status = status if status in PROJECT_STATUSES else 'draft'

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f'''
            INSERT INTO projects ({', '.join(_PROJECT_COLS)})
            VALUES ({', '.join('?' * len(_PROJECT_COLS))})
        ''', (pid, name, project_type, status, description or '',
              content_path or '', video_path or '', cover_path or '',
              book_name or '', json.dumps(tags or [], ensure_ascii=False), now, now))
        conn.commit()
        conn.close()
        return self.get_project(pid)

    def get_project(self, pid):
        rows = self._query('SELECT * FROM projects WHERE id = ?', (pid,))
        return self._finalize(rows[0]) if rows else None

    def list_projects(self, project_type=None, status=None, limit=200, offset=0):
        """项目列表（按更新时间倒序）；类型/状态可作过滤"""
        sql = 'SELECT * FROM projects'
        conds, params = [], []
        if project_type:
            conds.append('project_type = ?')
            params.append(project_type)
        if status:
            conds.append('status = ?')
            params.append(status)
        if conds:
            sql += ' WHERE ' + ' AND '.join(conds)
        sql += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
        params += [limit, offset]
        return [self._finalize(r) for r in self._query(sql, tuple(params))]

    def update_project(self, pid, **fields):
        """白名单字段更新；未知字段忽略，项目不存在抛 ProjectError"""
        current = self.get_project(pid)
        if not current:
            raise ProjectError(f'项目不存在: {pid}')

        sets, params = [], []
        for key in EDITABLE_FIELDS:
            if key not in fields:
                continue
            value = fields[key]
            if key == 'tags':
                value = json.dumps(value or [], ensure_ascii=False)
            if key == 'status' and value not in PROJECT_STATUSES:
                continue
            sets.append(f'{key} = ?')
            params.append(value)
        if sets:
            sets.append('updated_at = ?')
            params.append(time.time())
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(f'UPDATE projects SET {", ".join(sets)} WHERE id = ?',
                      (*params, pid))
            conn.commit()
            conn.close()
        return self.get_project(pid)

    def delete_project(self, pid):
        """删除项目及其发布记录；返回是否删除了项目"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM projects WHERE id = ?', (pid,))
        deleted = c.rowcount > 0
        c.execute('DELETE FROM publish_records WHERE project_id = ?', (pid,))
        conn.commit()
        conn.close()
        return deleted

    # ===== 发布记录 =====

    def start_publish(self, project_id, platform, title=''):
        """登记一次发布（running），返回记录 id；发布结果稍后 finish_publish 回写"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO publish_records (project_id, platform, status, title, created_at)
            VALUES (?, ?, 'running', ?, ?)
        ''', (project_id, platform, title or '', time.time()))
        rid = c.lastrowid
        conn.commit()
        conn.close()
        return rid

    def finish_publish(self, record_id, status, url='', error=''):
        """回写发布结果（status ∈ success/failed）"""
        if status not in ('success', 'failed'):
            status = 'failed'
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            UPDATE publish_records
            SET status = ?, url = ?, error = ?, finished_at = ?
            WHERE id = ?
        ''', (status, url or '', error or '', time.time(), record_id))
        conn.commit()
        conn.close()

    def list_publish_records(self, project_id=None, status=None, limit=100):
        sql = 'SELECT * FROM publish_records'
        conds, params = [], []
        if project_id:
            conds.append('project_id = ?')
            params.append(project_id)
        if status:
            conds.append('status = ?')
            params.append(status)
        if conds:
            sql += ' WHERE ' + ' AND '.join(conds)
        sql += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        return [self._finalize_record(r) for r in self._query(sql, tuple(params))]

    # ===== 统计 =====

    def stats(self):
        by_type, by_status = {}, {}
        for r in self._query('SELECT project_type, COUNT(*) AS n FROM projects GROUP BY project_type'):
            by_type[r['project_type']] = r['n']
        for r in self._query('SELECT status, COUNT(*) AS n FROM projects GROUP BY status'):
            by_status[r['status']] = r['n']
        total = self._query('SELECT COUNT(*) AS n FROM projects')[0]['n']
        pub = {r['status']: r['n'] for r in self._query(
            'SELECT status, COUNT(*) AS n FROM publish_records GROUP BY status')}
        return {
            'total': total,
            'by_type': by_type,
            'by_status': by_status,
            'publish': {'total': sum(pub.values()), **pub},
        }

    # ===== 内部 =====

    def _query(self, sql, params=()):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows

    @classmethod
    def _finalize(cls, proj):
        if not proj:
            return None
        proj['tags'] = json.loads(proj.get('tags') or '[]')
        proj['type_label'] = TYPE_LABELS.get(proj['project_type'], proj['project_type'])
        for key in ('created_at', 'updated_at'):
            if proj.get(key):
                proj[key + '_str'] = datetime.fromtimestamp(proj[key]).strftime('%Y-%m-%d %H:%M')
        return proj

    @staticmethod
    def _finalize_record(rec):
        for key in ('created_at', 'finished_at'):
            if rec.get(key):
                rec[key + '_str'] = datetime.fromtimestamp(rec[key]).strftime('%m-%d %H:%M:%S')
        return rec


def uuid_token():
    """短 id（含时间片，避免极端并发撞车）"""
    import uuid
    return f'{uuid.uuid4().hex[:8]}{int(time.time()) % 100000:05d}'

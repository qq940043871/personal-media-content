"""
任务管理器 — 统一任务调度、状态追踪、失败重试

功能：
- 任务注册（支持多种任务类型）
- 状态追踪（pending/running/done/failed）
- 失败重试（可配置重试次数）
- 任务依赖（任务A完成后才能执行任务B）
- 任务统计/历史
- 基于 SQLite，轻量无依赖

使用方式：
    from core.task_manager import TaskManager

    tm = TaskManager()

    # 创建任务
    task_id = tm.create_task(
        task_type='video_to_article',
        name='处理教学视频P3',
        params={'video_path': 'videos/xxx.mp4'},
    )

    # 开始执行
    tm.start_task(task_id)

    # 完成
    tm.complete_task(task_id, result={'article_path': '...'})

    # 失败（自动重试）
    tm.fail_task(task_id, error='网络超时')

    # 查询
    task = tm.get_task(task_id)
    tasks = tm.list_tasks(status='pending')
    stats = tm.stats()
"""

import os
import sqlite3
import json
import time
import uuid
import traceback
from datetime import datetime
from .config import config


# 任务状态常量
STATUS_PENDING = 'pending'
STATUS_RUNNING = 'running'
STATUS_DONE = 'done'
STATUS_FAILED = 'failed'
STATUS_SKIPPED = 'skipped'

ALL_STATUSES = [STATUS_PENDING, STATUS_RUNNING, STATUS_DONE, STATUS_FAILED, STATUS_SKIPPED]


class TaskManager:
    """任务管理器（基于 SQLite）"""

    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.path.join(config.STORAGE_BASE, 'db')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'tasks.db')

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                params TEXT DEFAULT '{}',
                result TEXT DEFAULT '{}',
                error TEXT DEFAULT '',
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                parent_id TEXT DEFAULT '',
                created_at REAL,
                started_at REAL,
                completed_at REAL,
                duration REAL DEFAULT 0
            )
        ''')

        # 任务日志（每次状态变更记录）
        c.execute('''
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT DEFAULT '',
                created_at REAL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        ''')

        # 索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_task ON task_logs(task_id)')

        conn.commit()
        conn.close()

    # ===== 任务创建 =====

    def create_task(self, task_type, name, params=None, priority=0,
                    max_retries=3, parent_id=''):
        """
        创建新任务

        Returns:
            str: 任务 ID
        """
        task_id = str(uuid.uuid4())[:8] + str(int(time.time()))[-6:]
        now = time.time()

        params_json = json.dumps(params or {}, ensure_ascii=False)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO tasks
            (id, task_type, name, status, priority, params, max_retries, parent_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, task_type, name, STATUS_PENDING, priority,
              params_json, max_retries, parent_id, now))
        conn.commit()
        conn.close()

        self._add_log(task_id, STATUS_PENDING, '任务创建')
        return task_id

    def create_batch(self, tasks):
        """
        批量创建任务

        Args:
            tasks: [{'task_type': str, 'name': str, 'params': dict, ...}, ...]

        Returns:
            list: 任务 ID 列表
        """
        task_ids = []
        for t in tasks:
            tid = self.create_task(
                task_type=t['task_type'],
                name=t['name'],
                params=t.get('params'),
                priority=t.get('priority', 0),
                max_retries=t.get('max_retries', 3),
                parent_id=t.get('parent_id', ''),
            )
            task_ids.append(tid)
        return task_ids

    # ===== 状态流转 =====

    def start_task(self, task_id):
        """标记任务开始执行"""
        now = time.time()
        self._update_status(task_id, STATUS_RUNNING, started_at=now)
        self._add_log(task_id, STATUS_RUNNING, '开始执行')

    def complete_task(self, task_id, result=None):
        """标记任务完成"""
        now = time.time()
        task = self.get_task(task_id)
        duration = now - (task.get('started_at') or now)

        self._update_status(
            task_id, STATUS_DONE,
            result=json.dumps(result or {}, ensure_ascii=False),
            completed_at=now,
            duration=duration,
        )
        self._add_log(task_id, STATUS_DONE, f'执行完成，耗时 {duration:.1f}s')

    def fail_task(self, task_id, error=''):
        """
        标记任务失败，自动判断是否可重试

        Returns:
            bool: True=将自动重试，False=不再重试（已达上限）
        """
        task = self.get_task(task_id)
        if not task:
            return False

        retry_count = task.get('retry_count', 0) + 1
        max_retries = task.get('max_retries', 3)
        now = time.time()

        will_retry = retry_count <= max_retries
        new_status = STATUS_PENDING if will_retry else STATUS_FAILED

        self._update_status(
            task_id, new_status,
            error=error,
            retry_count=retry_count,
        )

        if will_retry:
            self._add_log(task_id, STATUS_PENDING,
                         f'失败重试 {retry_count}/{max_retries}: {error[:100]}')
        else:
            self._add_log(task_id, STATUS_FAILED,
                         f'最终失败（已重试{retry_count}次）: {error[:100]}')

        return will_retry

    def skip_task(self, task_id, reason=''):
        """跳过任务（如幂等检测已存在）"""
        now = time.time()
        self._update_status(task_id, STATUS_SKIPPED, completed_at=now, duration=0)
        self._add_log(task_id, STATUS_SKIPPED, f'跳过: {reason}')

    # ===== 查询 =====

    def get_task(self, task_id):
        """获取任务详情"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = c.fetchone()
        conn.close()
        return self._row_to_dict(row) if row else None

    def list_tasks(self, status=None, task_type=None, limit=50, offset=0):
        """列出任务"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []

        if status:
            query += ' AND status = ?'
            params.append(status)
        if task_type:
            query += ' AND task_type = ?'
            params.append(task_type)

        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        c.execute(query, tuple(params))
        rows = c.fetchall()
        conn.close()

        return [self._row_to_dict(r) for r in rows]

    def get_next_pending(self, task_type=None):
        """获取下一个待执行的任务（按优先级排序）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        query = 'SELECT * FROM tasks WHERE status = ?'
        params = [STATUS_PENDING]

        if task_type:
            query += ' AND task_type = ?'
            params.append(task_type)

        query += ' ORDER BY priority DESC, created_at ASC LIMIT 1'
        c.execute(query, tuple(params))
        row = c.fetchone()
        conn.close()

        return self._row_to_dict(row) if row else None

    def get_task_logs(self, task_id, limit=50):
        """获取任务执行日志"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT * FROM task_logs
            WHERE task_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (task_id, limit))
        rows = c.fetchall()
        conn.close()

        return [{
            'id': r['id'],
            'task_id': r['task_id'],
            'status': r['status'],
            'message': r['message'],
            'created_at': datetime.fromtimestamp(r['created_at']).strftime('%Y-%m-%d %H:%M:%S'),
        } for r in rows]

    # ===== 统计 =====

    def stats(self):
        """任务统计"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 各状态数量
        c.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status')
        by_status = dict(c.fetchall())

        # 各类型数量
        c.execute('SELECT task_type, COUNT(*) FROM tasks GROUP BY task_type')
        by_type = dict(c.fetchall())

        # 总数
        c.execute('SELECT COUNT(*) FROM tasks')
        total = c.fetchone()[0]

        # 今日完成数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        c.execute('SELECT COUNT(*) FROM tasks WHERE status = ? AND completed_at >= ?',
                  (STATUS_DONE, today_start))
        today_done = c.fetchone()[0]

        # 今日失败数
        c.execute('SELECT COUNT(*) FROM tasks WHERE status = ? AND completed_at >= ?',
                  (STATUS_FAILED, today_start))
        today_failed = c.fetchone()[0]

        # 平均耗时（已完成的任务）
        c.execute('SELECT AVG(duration) FROM tasks WHERE status = ? AND duration > 0',
                  (STATUS_DONE,))
        avg_duration = c.fetchone()[0] or 0

        conn.close()

        return {
            'total': total,
            'by_status': by_status,
            'by_type': by_type,
            'today_done': today_done,
            'today_failed': today_failed,
            'avg_duration_seconds': round(avg_duration, 1),
        }

    # ===== 任务执行封装（便捷方法）=====

    def run_task(self, task_id, func, *args, **kwargs):
        """
        执行一个任务（自动处理状态流转和异常捕获）

        Args:
            task_id: 任务 ID
            func: 要执行的函数
            *args, **kwargs: 函数参数

        Returns:
            函数返回值
        """
        try:
            self.start_task(task_id)
            result = func(*args, **kwargs)
            self.complete_task(task_id, result=result if isinstance(result, dict) else {'result': str(result)})
            return result
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            traceback.print_exc()
            will_retry = self.fail_task(task_id, error_msg)
            if will_retry:
                print(f"[Task] 任务 {task_id} 失败，将自动重试")
            else:
                print(f"[Task] 任务 {task_id} 最终失败")
            raise

    def retry_failed_tasks(self, task_type=None):
        """将失败的任务重置为 pending（手动触发重试）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if task_type:
            c.execute('''
                UPDATE tasks SET status = ?, retry_count = 0
                WHERE status = ? AND task_type = ?
            ''', (STATUS_PENDING, STATUS_FAILED, task_type))
        else:
            c.execute('''
                UPDATE tasks SET status = ?, retry_count = 0
                WHERE status = ?
            ''', (STATUS_PENDING, STATUS_FAILED))

        count = c.rowcount
        conn.commit()
        conn.close()
        return count

    def cleanup_old_tasks(self, days=30, keep_done=False):
        """清理旧任务（默认保留30天）"""
        import time as _time
        cutoff = _time.time() - days * 86400

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if keep_done:
            c.execute('''
                DELETE FROM tasks
                WHERE status != ? AND created_at < ?
            ''', (STATUS_DONE, cutoff))
        else:
            c.execute('DELETE FROM tasks WHERE created_at < ?', (cutoff,))

        count = c.rowcount
        conn.commit()
        conn.close()
        return count

    # ===== 内部方法 =====

    def _update_status(self, task_id, status, **kwargs):
        """更新任务状态和其他字段"""
        if not kwargs:
            return

        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values())
        values.extend([status, task_id])

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(f'UPDATE tasks SET {set_clause}, status = ? WHERE id = ?', tuple(values))
        conn.commit()
        conn.close()

    def _add_log(self, task_id, status, message=''):
        """添加任务日志"""
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO task_logs (task_id, status, message, created_at)
            VALUES (?, ?, ?, ?)
        ''', (task_id, status, message, now))
        conn.commit()
        conn.close()

    @staticmethod
    def _row_to_dict(row):
        d = {
            'id': row['id'],
            'task_type': row['task_type'],
            'name': row['name'],
            'status': row['status'],
            'priority': row['priority'],
            'params': json.loads(row['params']) if row['params'] else {},
            'result': json.loads(row['result']) if row['result'] else {},
            'error': row['error'] or '',
            'retry_count': row['retry_count'],
            'max_retries': row['max_retries'],
            'parent_id': row['parent_id'] or '',
            'created_at': row['created_at'],
            'started_at': row['started_at'],
            'completed_at': row['completed_at'],
            'duration': row['duration'] or 0,
            'created_at_str': datetime.fromtimestamp(row['created_at']).strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
            'started_at_str': datetime.fromtimestamp(row['started_at']).strftime('%Y-%m-%d %H:%M:%S') if row['started_at'] else '',
            'completed_at_str': datetime.fromtimestamp(row['completed_at']).strftime('%Y-%m-%d %H:%M:%S') if row['completed_at'] else '',
        }
        return d

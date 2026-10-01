"""
Web 数据看板 — Flask 轻量管理面板

功能：
- 总览仪表盘（任务统计、素材统计、产出统计）
- 任务列表（按状态/类型过滤）
- 任务详情与日志
- 素材检索

启动方式：
    python -m dashboard.app
    python media-cli.py dashboard start

默认端口：5000
访问地址：http://localhost:5000
"""

import os
import sys
from flask import Flask, render_template_string, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager
from core.asset_manager import AssetManager
from core.config import config


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    tm = TaskManager()
    am = AssetManager()

    # ===== 页面路由 =====

    @app.route('/')
    def index():
        return render_template_string(INDEX_HTML)

    @app.route('/tasks')
    def tasks_page():
        return render_template_string(TASKS_HTML)

    @app.route('/assets')
    def assets_page():
        return render_template_string(ASSETS_HTML)

    # ===== API 路由 =====

    @app.route('/api/stats')
    def api_stats():
        """总览统计"""
        task_stats = tm.stats()
        asset_stats = am.stats()

        # 存储统计（文件系统）
        from core.storage import Storage
        storage = Storage()
        storage_stats = storage.stats()

        return jsonify({
            'tasks': task_stats,
            'assets': asset_stats,
            'storage': storage_stats,
        })

    @app.route('/api/tasks')
    def api_tasks():
        """任务列表"""
        status = request.args.get('status')
        task_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        tasks = tm.list_tasks(status=status, task_type=task_type, limit=limit, offset=offset)
        return jsonify({'tasks': tasks, 'total': len(tasks)})

    @app.route('/api/tasks/<task_id>')
    def api_task_detail(task_id):
        """任务详情"""
        task = tm.get_task(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        logs = tm.get_task_logs(task_id)
        return jsonify({'task': task, 'logs': logs})

    @app.route('/api/tasks/retry', methods=['POST'])
    def api_retry_tasks():
        """重试失败任务"""
        data = request.get_json() or {}
        task_type = data.get('type')
        count = tm.retry_failed_tasks(task_type=task_type)
        return jsonify({'reset_count': count})

    @app.route('/api/assets')
    def api_assets():
        """素材列表"""
        asset_type = request.args.get('type')
        project = request.args.get('project')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        assets = am.list_assets(asset_type=asset_type, project=project, limit=limit, offset=offset)
        stats = am.stats()
        return jsonify({'assets': assets, 'stats': stats})

    @app.route('/api/assets/search')
    def api_assets_search():
        """按标签搜索素材"""
        tags = request.args.get('tags', '').split(',')
        tags = [t.strip() for t in tags if t.strip()]
        if not tags:
            return jsonify({'assets': []})

        match_all = request.args.get('match', 'all') == 'all'
        assets = am.search_by_tags(tags, match_all=match_all)
        return jsonify({'assets': assets})

    @app.route('/api/tags')
    def api_tags():
        """所有标签"""
        project = request.args.get('project')
        tags = am.list_all_tags(project=project)
        return jsonify({'tags': tags})

    return app


# ===== HTML 模板 =====

INDEX_HTML = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 内容生产中台 — 总览</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
           background: #f5f7fa; color: #1a1a2e; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; padding: 24px 32px; }
    .header h1 { font-size: 24px; margin-bottom: 4px; }
    .header p { opacity: 0.9; font-size: 14px; }
    .nav { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 0 32px; }
    .nav a { display: inline-block; padding: 14px 20px; color: #555; text-decoration: none;
             border-bottom: 3px solid transparent; font-size: 14px; }
    .nav a.active { color: #667eea; border-bottom-color: #667eea; font-weight: 600; }
    .container { max-width: 1200px; margin: 0 auto; padding: 24px 32px; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
             gap: 16px; margin-bottom: 24px; }
    .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .card .label { font-size: 13px; color: #888; margin-bottom: 8px; }
    .card .value { font-size: 28px; font-weight: 700; color: #1a1a2e; }
    .card .sub { font-size: 12px; color: #aaa; margin-top: 4px; }
    .card.green .value { color: #10b981; }
    .card.red .value { color: #ef4444; }
    .card.blue .value { color: #3b82f6; }
    .card.purple .value { color: #8b5cf6; }
    .section { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px;
               box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .section h2 { font-size: 16px; margin-bottom: 16px; padding-bottom: 12px;
                  border-bottom: 1px solid #eee; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
    th { color: #888; font-weight: 500; font-size: 12px; text-transform: uppercase; }
    .status { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
    .status.done { background: #d1fae5; color: #065f46; }
    .status.running { background: #dbeafe; color: #1e40af; }
    .status.pending { background: #fef3c7; color: #92400e; }
    .status.failed { background: #fee2e2; color: #991b1b; }
    .status.skipped { background: #e5e7eb; color: #374151; }
  </style>
</head>
<body>
  <div class="header">
    <h1>🎬 AI 内容生产中台</h1>
    <p>短视频 · 图文文章 · 长篇小说 · 全链路内容生产管理</p>
  </div>
  <div class="nav">
    <a href="/" class="active">📊 总览</a>
    <a href="/tasks">📋 任务中心</a>
    <a href="/assets">📦 素材库</a>
  </div>
  <div class="container">
    <div class="cards" id="stats-cards"></div>

    <div class="section">
      <h2>🕐 最近任务</h2>
      <table>
        <thead><tr><th>状态</th><th>任务名</th><th>类型</th><th>创建时间</th><th>耗时</th></tr></thead>
        <tbody id="recent-tasks"></tbody>
      </table>
    </div>
  </div>

<script>
async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  const t = data.tasks;
  const a = data.assets;
  const s = data.storage;

  document.getElementById('stats-cards').innerHTML = `
    <div class="card blue"><div class="label">任务总数</div><div class="value">${t.total}</div><div class="sub">今日完成 ${t.today_done} · 失败 ${t.today_failed}</div></div>
    <div class="card green"><div class="label">已完成任务</div><div class="value">${t.by_status.done || 0}</div><div class="sub">平均耗时 ${t.avg_duration_seconds}s</div></div>
    <div class="card"><div class="label">待处理</div><div class="value">${t.by_status.pending || 0}</div><div class="sub">运行中 ${t.by_status.running || 0}</div></div>
    <div class="card purple"><div class="label">素材资产</div><div class="value">${a.total}</div><div class="sub">${a.tag_count} 个标签 · ${a.total_size_mb} MB</div></div>
    <div class="card green"><div class="label">输入视频</div><div class="value">${s.videos_input}</div><div class="sub">videos_input</div></div>
    <div class="card blue"><div class="label">文章数量</div><div class="value">${s.articles}</div><div class="sub">articles</div></div>
    <div class="card"><div class="label">小说项目</div><div class="value">${s.novel_projects}</div><div class="sub">novels</div></div>
  `;
}

async function loadRecentTasks() {
  const res = await fetch('/api/tasks?limit=10');
  const data = await res.json();
  const tbody = document.getElementById('recent-tasks');
  tbody.innerHTML = data.tasks.map(t => `
    <tr>
      <td><span class="status ${t.status}">${t.status}</span></td>
      <td>${t.name}</td>
      <td>${t.task_type}</td>
      <td>${t.created_at_str}</td>
      <td>${t.duration ? t.duration.toFixed(1) + 's' : '-'}</td>
    </tr>
  `).join('');
}

loadStats();
loadRecentTasks();
setInterval(() => { loadStats(); loadRecentTasks(); }, 10000);
</script>
</body>
</html>
'''

TASKS_HTML = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>任务中心 — AI 内容生产中台</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
           background: #f5f7fa; color: #1a1a2e; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; padding: 24px 32px; }
    .header h1 { font-size: 24px; margin-bottom: 4px; }
    .nav { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 0 32px; }
    .nav a { display: inline-block; padding: 14px 20px; color: #555; text-decoration: none;
             border-bottom: 3px solid transparent; font-size: 14px; }
    .nav a.active { color: #667eea; border-bottom-color: #667eea; font-weight: 600; }
    .container { max-width: 1200px; margin: 0 auto; padding: 24px 32px; }
    .filters { background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px;
               box-shadow: 0 2px 8px rgba(0,0,0,0.06); display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .filters label { font-size: 13px; color: #666; }
    .filters select, .filters button { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px;
                                         font-size: 13px; background: white; cursor: pointer; }
    .filters button.primary { background: #667eea; color: white; border-color: #667eea; }
    .filters button.danger { background: #ef4444; color: white; border-color: #ef4444; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; font-size: 13px; }
    th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
    th { background: #fafbfc; color: #888; font-weight: 500; font-size: 12px; text-transform: uppercase; }
    .status { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; }
    .status.done { background: #d1fae5; color: #065f46; }
    .status.running { background: #dbeafe; color: #1e40af; }
    .status.pending { background: #fef3c7; color: #92400e; }
    .status.failed { background: #fee2e2; color: #991b1b; }
    .status.skipped { background: #e5e7eb; color: #374151; }
    .task-detail { background: white; border-radius: 12px; padding: 20px; margin-top: 16px;
                   box-shadow: 0 2px 8px rgba(0,0,0,0.06); display: none; }
    .task-detail h3 { margin-bottom: 12px; }
    .log-item { padding: 8px 12px; border-left: 3px solid #ddd; margin-bottom: 6px; font-size: 13px; }
    .log-item .time { color: #999; font-size: 12px; margin-right: 8px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📋 任务中心</h1>
    <p>查看和管理所有内容生产任务</p>
  </div>
  <div class="nav">
    <a href="/">📊 总览</a>
    <a href="/tasks" class="active">📋 任务中心</a>
    <a href="/assets">📦 素材库</a>
  </div>
  <div class="container">
    <div class="filters">
      <label>状态：</label>
      <select id="filter-status">
        <option value="">全部</option>
        <option value="pending">待处理</option>
        <option value="running">运行中</option>
        <option value="done">已完成</option>
        <option value="failed">失败</option>
        <option value="skipped">已跳过</option>
      </select>
      <label>类型：</label>
      <select id="filter-type"><option value="">全部</option></select>
      <button class="primary" onclick="loadTasks()">🔍 筛选</button>
      <button class="danger" onclick="retryFailed()">🔄 重试失败任务</button>
      <span id="task-count" style="margin-left:auto; color:#888; font-size:13px;"></span>
    </div>

    <table>
      <thead><tr><th>状态</th><th>任务名</th><th>类型</th><th>优先级</th><th>创建时间</th><th>耗时</th><th>重试</th></tr></thead>
      <tbody id="task-list"></tbody>
    </table>

    <div class="task-detail" id="task-detail">
      <h3 id="detail-title">任务详情</h3>
      <div id="detail-body"></div>
      <h4 style="margin-top: 16px;">执行日志</h4>
      <div id="detail-logs"></div>
    </div>
  </div>

<script>
async function loadTypes() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  const types = Object.keys(data.tasks.by_type || {});
  const sel = document.getElementById('filter-type');
  types.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t; opt.textContent = t;
    sel.appendChild(opt);
  });
}

async function loadTasks() {
  const status = document.getElementById('filter-status').value;
  const type = document.getElementById('filter-type').value;
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (type) params.set('type', type);
  params.set('limit', 50);

  const res = await fetch('/api/tasks?' + params);
  const data = await res.json();
  const tbody = document.getElementById('task-list');
  tbody.innerHTML = data.tasks.map(t => `
    <tr onclick="showDetail('${t.id}')" style="cursor:pointer;">
      <td><span class="status ${t.status}">${t.status}</span></td>
      <td>${t.name}</td>
      <td>${t.task_type}</td>
      <td>${t.priority}</td>
      <td>${t.created_at_str}</td>
      <td>${t.duration ? t.duration.toFixed(1) + 's' : '-'}</td>
      <td>${t.retry_count}/${t.max_retries}</td>
    </tr>
  `).join('');
  document.getElementById('task-count').textContent = `共 ${data.total} 条`;
}

async function showDetail(id) {
  const res = await fetch('/api/tasks/' + id);
  const data = await res.json();
  const t = data.task;
  document.getElementById('detail-title').textContent = t.name + ' (' + t.id + ')';
  document.getElementById('detail-body').innerHTML = `
    <p><strong>状态：</strong><span class="status ${t.status}">${t.status}</span></p>
    <p><strong>类型：</strong>${t.task_type}</p>
    <p><strong>参数：</strong><pre style="background:#f6f8fa;padding:8px;border-radius:6px;overflow:auto;">${JSON.stringify(t.params, null, 2)}</pre></p>
    ${t.error ? `<p><strong>错误：</strong><span style="color:#ef4444;">${t.error}</span></p>` : ''}
    ${t.result && Object.keys(t.result).length ? `<p><strong>结果：</strong><pre style="background:#f6f8fa;padding:8px;border-radius:6px;overflow:auto;">${JSON.stringify(t.result, null, 2)}</pre></p>` : ''}
  `;
  document.getElementById('detail-logs').innerHTML = data.logs.map(l => `
    <div class="log-item"><span class="time">${l.created_at}</span><strong>[${l.status}]</strong> ${l.message}</div>
  `).join('');
  document.getElementById('task-detail').style.display = 'block';
}

async function retryFailed() {
  if (!confirm('确定要重试所有失败任务吗？')) return;
  const res = await fetch('/api/tasks/retry', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  const data = await res.json();
  alert(`已重置 ${data.reset_count} 个失败任务`);
  loadTasks();
}

loadTypes();
loadTasks();
setInterval(loadTasks, 10000);
</script>
</body>
</html>
'''

ASSETS_HTML = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>素材库 — AI 内容生产中台</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
           background: #f5f7fa; color: #1a1a2e; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
              color: white; padding: 24px 32px; }
    .header h1 { font-size: 24px; margin-bottom: 4px; }
    .nav { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 0 32px; }
    .nav a { display: inline-block; padding: 14px 20px; color: #555; text-decoration: none;
             border-bottom: 3px solid transparent; font-size: 14px; }
    .nav a.active { color: #667eea; border-bottom-color: #667eea; font-weight: 600; }
    .container { max-width: 1200px; margin: 0 auto; padding: 24px 32px; }
    .sidebar-layout { display: grid; grid-template-columns: 240px 1fr; gap: 16px; }
    .sidebar { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); height: fit-content; }
    .sidebar h3 { font-size: 14px; margin-bottom: 12px; color: #666; }
    .tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .tag { padding: 4px 10px; background: #f0f2f5; border-radius: 12px; font-size: 12px;
           cursor: pointer; color: #555; }
    .tag.active { background: #667eea; color: white; }
    .content { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; }
    .search-bar { padding: 16px 20px; border-bottom: 1px solid #f0f0f0; display: flex; gap: 12px; align-items: center; }
    .search-bar input { flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
    .search-bar select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }
    th { background: #fafbfc; color: #888; font-weight: 500; font-size: 12px; text-transform: uppercase; }
    .type-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #eef2ff; color: #4338ca; }
    .tag-small { display: inline-block; padding: 2px 6px; background: #f3f4f6; border-radius: 4px; font-size: 11px; color: #666; margin-right: 4px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📦 素材库</h1>
    <p>统一管理所有内容资产</p>
  </div>
  <div class="nav">
    <a href="/">📊 总览</a>
    <a href="/tasks">📋 任务中心</a>
    <a href="/assets" class="active">📦 素材库</a>
  </div>
  <div class="container">
    <div class="sidebar-layout">
      <div class="sidebar">
        <h3>🏷️ 标签</h3>
        <div class="tag-list" id="tag-list"></div>
        <h3 style="margin-top:20px;">📊 统计</h3>
        <div id="side-stats" style="font-size:13px; color:#555; line-height:1.8;"></div>
      </div>
      <div class="content">
        <div class="search-bar">
          <input type="text" id="search-input" placeholder="按标签搜索，逗号分隔多个标签...">
          <select id="type-filter">
            <option value="">全部类型</option>
          </select>
          <button onclick="doSearch()" style="padding:8px 16px;background:#667eea;color:white;border:none;border-radius:6px;cursor:pointer;">搜索</button>
        </div>
        <table>
          <thead><tr><th>类型</th><th>标题</th><th>项目</th><th>标签</th><th>大小</th><th>更新时间</th></tr></thead>
          <tbody id="asset-list"></tbody>
        </table>
      </div>
    </div>
  </div>

<script>
let selectedTags = [];

async function loadTags() {
  const res = await fetch('/api/tags');
  const data = await res.json();
  const list = document.getElementById('tag-list');
  list.innerHTML = data.tags.map(t =>
    `<span class="tag" onclick="toggleTag('${t}')">${t}</span>`
  ).join('');
}

async function loadStats() {
  const res = await fetch('/api/assets?limit=1');
  const data = await res.json();
  const s = data.stats;
  const typeFilter = document.getElementById('type-filter');
  Object.keys(s.by_type || {}).forEach(t => {
    const opt = document.createElement('option');
    opt.value = t; opt.textContent = `${t} (${s.by_type[t]})`;
    typeFilter.appendChild(opt);
  });

  document.getElementById('side-stats').innerHTML = `
    总数：<strong>${s.total}</strong><br>
    标签数：<strong>${s.tag_count}</strong><br>
    总大小：<strong>${s.total_size_mb} MB</strong><br>
    ${Object.entries(s.by_project || {}).map(([p,c]) => `${p}: ${c}`).join('<br>')}
  `;
}

async function loadAssets() {
  const type = document.getElementById('type-filter').value;
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  params.set('limit', 50);

  const res = await fetch('/api/assets?' + params);
  const data = await res.json();
  renderAssets(data.assets);
}

async function doSearch() {
  const q = document.getElementById('search-input').value.trim();
  const tags = q.split(',').map(t => t.trim()).filter(t => t);
  if (!tags.length && !selectedTags.length) {
    loadAssets();
    return;
  }
  const allTags = [...new Set([...tags, ...selectedTags])];
  const res = await fetch('/api/assets/search?tags=' + encodeURIComponent(allTags.join(',')));
  const data = await res.json();
  renderAssets(data.assets);
}

function renderAssets(assets) {
  const tbody = document.getElementById('asset-list');
  tbody.innerHTML = assets.map(a => `
    <tr>
      <td><span class="type-badge">${a.asset_type}</span></td>
      <td>${a.title}</td>
      <td>${a.project || '-'}</td>
      <td>${a.tags.slice(0,3).map(t => `<span class="tag-small">${t}</span>`).join('')}</td>
      <td>${(a.file_size / 1024).toFixed(1)} KB</td>
      <td>${a.updated_at}</td>
    </tr>
  `).join('');
}

function toggleTag(tag) {
  const idx = selectedTags.indexOf(tag);
  if (idx >= 0) selectedTags.splice(idx, 1);
  else selectedTags.push(tag);
  document.querySelectorAll('.tag').forEach(el => {
    el.classList.toggle('active', selectedTags.includes(el.textContent));
  });
  doSearch();
}

loadTags();
loadStats();
loadAssets();
</script>
</body>
</html>
'''


if __name__ == '__main__':
    app = create_app()
    print("🎬 AI 内容生产中台 — 数据看板")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止\n")
    app.run(host='0.0.0.0', port=5000, debug=False)

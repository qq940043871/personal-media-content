"""项目工作台测试 — ProjectManager 契约 + dashboard API（不触网，不真发布）"""

import os
import json

import pytest

from core.project_manager import (
    ProjectManager, ProjectError, PROJECT_TYPES, EDITABLE_FIELDS,
)


@pytest.fixture
def pm(tmp_path):
    return ProjectManager(db_path=str(tmp_path / 'projects.db'))


# ===== ProjectManager 单元 =====

def test_create_and_get(pm):
    p = pm.create_project('秋日书评', 'article', description='书评第 12 期',
                          tags=['书评', '秋天'])
    assert p['name'] == '秋日书评'
    assert p['project_type'] == 'article'
    assert p['type_label'] == '图文文章'
    assert p['status'] == 'draft'
    assert p['tags'] == ['书评', '秋天']
    assert p['created_at_str']
    assert pm.get_project(p['id'])['id'] == p['id']


def test_create_rejects_bad_type_and_empty_name(pm):
    with pytest.raises(ProjectError):
        pm.create_project('x', 'podcast')
    with pytest.raises(ProjectError):
        pm.create_project('  ', 'article')


def test_list_filter_and_order(pm):
    a = pm.create_project('文章A', 'article')
    v = pm.create_project('视频B', 'video')
    n = pm.create_project('小说C', 'novel')
    pm.update_project(v['id'], status='ready')  # 提到最新

    projects = pm.list_projects()
    assert [p['id'] for p in projects][:1] == [v['id']]  # 按更新时间倒序
    assert {p['id'] for p in pm.list_projects(project_type='article')} == {a['id']}
    assert {p['id'] for p in pm.list_projects(status='ready')} == {v['id']}
    assert len(pm.list_projects()) == 3


def test_update_whitelist_and_unknown_ignored(pm):
    p = pm.create_project('视频B', 'video', video_path='Z:/old.mp4')
    updated = pm.update_project(p['id'], video_path='Z:/new.mp4',
                                status='ready', bogus_field='x')
    assert updated['video_path'] == 'Z:/new.mp4'
    assert updated['status'] == 'ready'
    assert updated['description'] == ''

    # 非法状态被忽略，其他字段照常生效
    updated2 = pm.update_project(p['id'], status='nope', name='改名')
    assert updated2['status'] == 'ready'
    assert updated2['name'] == '改名'


def test_update_missing_project_raises(pm):
    with pytest.raises(ProjectError):
        pm.update_project('no-such-id', name='x')


def test_delete_removes_records(pm):
    p = pm.create_project('文章A', 'article')
    rid = pm.start_publish(p['id'], 'feishu', title='文章A')
    pm.finish_publish(rid, 'success', url='https://x')
    assert pm.delete_project(p['id']) is True
    assert pm.get_project(p['id']) is None
    assert pm.list_publish_records(project_id=p['id']) == []
    assert pm.delete_project(p['id']) is False


def test_publish_record_lifecycle(pm):
    p = pm.create_project('视频B', 'video')
    rid = pm.start_publish(p['id'], 'douyin', title='视频B')
    running = pm.list_publish_records(project_id=p['id'])
    assert running[0]['status'] == 'running'
    assert running[0]['finished_at'] is None

    pm.finish_publish(rid, 'failed', error='视频不存在')
    done = pm.list_publish_records(project_id=p['id'])
    assert done[0]['status'] == 'failed'
    assert done[0]['error'] == '视频不存在'
    assert done[0]['finished_at'] is not None

    # 非法 status 归一为 failed
    rid2 = pm.start_publish(p['id'], 'douyin')
    pm.finish_publish(rid2, 'weird')
    assert pm.list_publish_records(project_id=p['id'])[0]['status'] == 'failed'


def test_stats(pm):
    pm.create_project('文章A', 'article')
    v = pm.create_project('视频B', 'video')
    pm.update_project(v['id'], status='published')
    rid = pm.start_publish(v['id'], 'douyin')
    pm.finish_publish(rid, 'success')

    s = pm.stats()
    assert s['total'] == 2
    assert s['by_type'] == {'article': 1, 'video': 1}
    assert s['by_status']['published'] == 1
    assert s['publish']['success'] == 1
    assert s['publish']['total'] == 1


def test_project_types_and_fields_consistency():
    assert set(PROJECT_TYPES) == {'article', 'novel', 'video'}
    assert 'cover_path' in EDITABLE_FIELDS


# ===== dashboard API（Flask test client）=====

@pytest.fixture
def client(tmp_path, monkeypatch):
    from core.config import config
    storage = tmp_path / 'storage'
    monkeypatch.setattr(config, 'STORAGE_BASE', str(storage))
    monkeypatch.setattr(config, 'STORAGE_ARTICLES', str(storage / 'articles'))

    from workbench.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


def test_api_create_article_project_creates_content_file(client):
    res = client.post('/api/projects', json={
        'name': '秋日书评', 'project_type': 'article', 'description': '第 12 期'})
    assert res.status_code == 201
    project = res.get_json()['project']
    assert project['content_path']  # 自动落到 storage/articles/projects/

    with open(project['content_path'], 'r', encoding='utf-8') as f:
        assert '秋日书评' in f.read()

    detail = client.get(f"/api/projects/{project['id']}").get_json()
    assert '秋日书评' in detail['content']
    assert detail['publish_records'] == []


def test_api_create_rejects_bad_type(client):
    res = client.post('/api/projects', json={'name': 'x', 'project_type': 'podcast'})
    assert res.status_code == 400
    assert 'podcast' in res.get_json()['error']


def test_api_update_status_validation(client):
    res = client.post('/api/projects', json={'name': '视频B', 'project_type': 'video'})
    pid = res.get_json()['project']['id']

    ok = client.put(f'/api/projects/{pid}', json={'status': 'ready'})
    assert ok.get_json()['project']['status'] == 'ready'

    bad = client.put(f'/api/projects/{pid}', json={'status': 'flying'})
    assert bad.status_code == 400


def test_api_delete_then_404(client):
    pid = client.post('/api/projects', json={
        'name': '小说C', 'project_type': 'novel'}).get_json()['project']['id']
    assert client.delete(f'/api/projects/{pid}').get_json()['ok'] is True
    assert client.get(f'/api/projects/{pid}').status_code == 404


def test_api_publish_validation_paths(client, tmp_path):
    # 小说项目：直接拒绝发布
    novel = client.post('/api/projects', json={
        'name': '小说C', 'project_type': 'novel'}).get_json()['project']
    res = client.post(f"/api/projects/{novel['id']}/publish",
                      json={'platforms': ['feishu']})
    assert res.status_code == 400
    assert '暂不支持' in res.get_json()['error']

    # 图文项目：空正文拒绝
    art = client.post('/api/projects', json={
        'name': '文章A', 'project_type': 'article'}).get_json()['project']
    client.post(f"/api/projects/{art['id']}/content", json={'content': ''})
    res = client.post(f"/api/projects/{art['id']}/publish",
                      json={'platforms': ['feishu']})
    assert res.status_code == 400
    assert '正文为空' in res.get_json()['error']

    # 未知平台拒绝
    client.post(f"/api/projects/{art['id']}/content", json={'content': '# 正文'})
    res = client.post(f"/api/projects/{art['id']}/publish",
                      json={'platforms': ['nope']})
    assert res.status_code == 400
    assert '未知平台' in res.get_json()['error']

    # 未指定平台拒绝
    res = client.post(f"/api/projects/{art['id']}/publish", json={'platforms': []})
    assert res.status_code == 400


def test_api_platforms_lists_known(client):
    data = client.get('/api/platforms').get_json()
    ids = {p['id'] for p in data['platforms']}
    assert ids == {'feishu', 'wechat', 'douyin'}


def test_api_workbench_page_renders(client):
    res = client.get('/workbench')
    assert res.status_code == 200
    assert '项目工作台'.encode('utf-8') in res.data

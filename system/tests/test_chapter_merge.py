"""章节合并测试（tmp 假结构，不依赖仓库真实数据）"""

import pytest

from core.chapter_merge import merge_chapters


def make_book(tmp_path, chapters, units_text=None):
    """搭一本假书：chapters/{第N章}.txt + 可选 process/5-第1卷-剧情单元.txt"""
    src = tmp_path / 'chapters'
    src.mkdir(parents=True)
    for num, title, body in chapters:
        (src / f'8-正文-第{num}章.txt').write_text(
            f'第{num}章 {title}\n\n{body}\n', encoding='utf-8')
    unit_glob = ''
    if units_text:
        proc = tmp_path / 'process'
        proc.mkdir()
        (proc / '5-第1卷-剧情单元.txt').write_text(units_text, encoding='utf-8')
        unit_glob = str(proc / '5-第1卷-剧情单元.txt')
    return src, unit_glob


def read_out(out, name):
    return (out / name).read_text(encoding='utf-8')


def test_fixed_grouping_without_units(tmp_path):
    src, _ = make_book(tmp_path, [
        (1, '开篇', '一' * 100), (2, '风波', '二' * 100), (3, '转折', '三' * 100)])
    out = tmp_path / 'out'
    r = merge_chapters(src, out, per=2)

    assert [g['num'] for g in r['groups']] == [1, 2]
    assert r['groups'][0]['sources'] == [1, 2]
    assert r['groups'][1]['sources'] == [3]
    assert len(list(out.glob('第*.txt'))) == 2
    # 标题取组内首章、源章标题行已剥离
    text = read_out(out, '第001章-开篇.txt')
    assert text.startswith('第1章 开篇')
    assert '第2章' not in text and '风波' not in text


def test_unit_boundary_and_theme(tmp_path):
    src, units = make_book(tmp_path, [
        (n, f'第{n}节', '字' * 50) for n in range(1, 6)],  # 单元共 5 章
        units_text='【单元1：第1-5章 - 童年时光】\n- 主题：童年\n')
    out = tmp_path / 'out'

    # per=5：整单元一章，标题用单元主题
    r = merge_chapters(src, out, per=5, unit_glob=units)
    assert len(r['groups']) == 1
    assert r['groups'][0]['title'] == '童年时光'
    assert r['groups'][0]['sources'] == [1, 2, 3, 4, 5]

    # per=2：单元内均衡切 3 组，标题退回首章标题，绝不跨单元
    r2 = merge_chapters(tmp_path / 'chapters', tmp_path / 'out2', per=2,
                        unit_glob=units)
    all_src = [n for g in r2['groups'] for n in g['sources']]
    assert all_src == [1, 2, 3, 4, 5]
    assert r2['groups'][0]['title'] != '童年时光'
    assert (out / '合并对照.md').exists()


def test_target_greedy_respects_units(tmp_path):
    # 单元 A：3 章（100+2000+100 字，共 2200）；单元 B：1 章（100 字）
    chapters = [(1, 'a1', '一' * 100), (2, 'a2', '二' * 2000), (3, 'a3', '三' * 100),
                (4, 'b1', '四' * 100)]
    src, units = make_book(tmp_path, chapters,
                           units_text='【单元1：第1-3章 - 上山】\n'
                                      '【单元2：第4-4章 - 下山】\n')
    out = tmp_path / 'out'
    r = merge_chapters(src, out, per=8, target=1000, unit_glob=units)

    # 单元 A：1-2 凑满 1000 成组，3 是 100 字碎尾 → 回并前组（2200 字整章）
    # 单元 B 整体 100 < 1000 → 整单元一章，标题用单元主题
    assert [[g['sources'] for g in r['groups']]] == [[[1, 2, 3], [4]]]
    assert r['groups'][0]['title'] == '上山'
    assert r['groups'][1]['title'] == '下山'


def test_errors_on_missing_and_conflict(tmp_path):
    with pytest.raises(FileNotFoundError):
        merge_chapters(tmp_path / 'none', tmp_path / 'out')

    src = tmp_path / 'chapters'
    src.mkdir()
    (src / 'a.txt').write_text('第1章 x\n正文', encoding='utf-8')
    (src / 'b.txt').write_text('第1章 y\n正文', encoding='utf-8')
    with pytest.raises(ValueError, match='章号冲突'):
        merge_chapters(src, tmp_path / 'out')

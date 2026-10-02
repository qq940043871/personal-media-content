"""
小说飞书发布工具 — 基于 core.feishu_publisher 的 Python 版

替代旧的 shell 脚本，支持：
- 批量发布章节到飞书文档
- 按卷/分卷组织知识空间
- 发布记录（幂等，跳过已发布）
- 可配置的文档命名格式

使用方式：
    python publish_to_feishu.py --chapters-dir ./hello_novel/novels/cangyuantu/chapters --space-id xxx
    python publish_to_feishu.py --all --start 1 --end 100 --space-id xxx

也可以作为模块导入：
    from core.novel_publisher import NovelFeishuPublisher
    pub = NovelFeishuPublisher()
    pub.publish_chapter(chapter_path, title='第1章 xxx')
    pub.publish_batch(chapter_paths)
"""

import os
import sys
import re
import json
import glob
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.feishu_publisher import FeishuPublisher
from core.config import config


class NovelFeishuPublisher:
    """小说飞书发布器（批量章节发布）"""

    def __init__(self, record_file=None):
        self.publisher = FeishuPublisher()
        # 幂等记录统一放 storage/db/（运行时数据，随库重建）；旧 CWD 文件自动迁移
        if record_file is None:
            db_dir = os.path.join(config.STORAGE_BASE, 'db')
            os.makedirs(db_dir, exist_ok=True)
            record_file = os.path.join(db_dir, 'feishu_published.json')
        self.record_file = record_file
        self._records = self._load_records()

    def _load_records(self):
        """加载已发布记录；CWD 旧记录文件存在时自动迁移到 storage/db/"""
        if os.path.exists(self.record_file):
            try:
                with open(self.record_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}

        legacy = os.path.join(os.getcwd(), '_feishu_published.json')
        if os.path.exists(legacy):
            try:
                with open(legacy, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                shutil.copyfile(legacy, self.record_file)
                print(f"[NovelPublisher] 已迁移发布记录: {legacy} → {self.record_file}")
                return records
            except Exception:
                pass
        return {}

    def _save_records(self):
        """保存发布记录"""
        with open(self.record_file, 'w', encoding='utf-8') as f:
            json.dump(self._records, f, ensure_ascii=False, indent=2)

    def is_published(self, chapter_path):
        """检查是否已发布"""
        abs_path = os.path.abspath(chapter_path)
        return abs_path in self._records

    def publish_chapter(self, chapter_path, title=None, skip_if_published=True):
        """
        发布单个章节

        Returns:
            dict: {'success': bool, 'doc_id': str, 'doc_url': str, 'skipped': bool}
        """
        abs_path = os.path.abspath(chapter_path)

        if skip_if_published and self.is_published(chapter_path):
            record = self._records[abs_path]
            print(f"  ⏭️  跳过（已发布）: {record.get('title', chapter_path)}")
            return {'success': True, 'skipped': True, **record}

        # 读取章节内容
        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取标题（第一行如果是标题行就用它）
        if not title:
            title = self._extract_title(content, os.path.basename(chapter_path))

        # 转为 Markdown
        md_content = self._chapter_to_markdown(content, title)

        print(f"  📄 发布中: {title}")

        result = self.publisher.create_document(title, md_content)

        if result.get('success'):
            record = {
                'title': title,
                'doc_id': result['doc_id'],
                'doc_url': result['doc_url'],
                'path': abs_path,
                'published_at': self._now_str(),
            }
            self._records[abs_path] = record
            self._save_records()
            print(f"  ✅ 发布成功: {result['doc_url'][:60]}...")
            return {'success': True, 'skipped': False, **record}
        else:
            print(f"  ❌ 发布失败: {result.get('error', '未知错误')}")
            return {'success': False, 'error': result.get('error')}

    def publish_batch(self, chapter_paths, skip_if_published=True):
        """
        批量发布章节

        Returns:
            dict: {'total': int, 'success': int, 'skipped': int, 'failed': int, 'results': list}
        """
        results = []
        success = 0
        skipped = 0
        failed = 0

        total = len(chapter_paths)
        print(f"\n📚 开始批量发布 {total} 个章节\n")

        for i, path in enumerate(chapter_paths, 1):
            print(f"[{i}/{total}]", end=' ')
            try:
                result = self.publish_chapter(path, skip_if_published=skip_if_published)
                results.append(result)
                if result.get('skipped'):
                    skipped += 1
                elif result.get('success'):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ 异常: {e}")
                results.append({'success': False, 'error': str(e), 'path': path})
                failed += 1

        print(f"\n{'='*50}")
        print(f"  发布完成: 共 {total} 章")
        print(f"    ✅ 成功: {success}")
        print(f"    ⏭️  跳过: {skipped}")
        print(f"    ❌ 失败: {failed}")
        print(f"{'='*50}\n")

        return {
            'total': total,
            'success': success,
            'skipped': skipped,
            'failed': failed,
            'results': results,
        }

    def publish_directory(self, directory, pattern='*.txt', recursive=False,
                          skip_if_published=True):
        """
        发布目录下所有章节文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归子目录
            skip_if_published: 是否跳过已发布

        Returns:
            dict: 同 publish_batch
        """
        if recursive:
            files = []
            for root, dirs, filenames in os.walk(directory):
                for fn in filenames:
                    if fn.endswith('.txt'):
                        files.append(os.path.join(root, fn))
            files.sort()
        else:
            files = sorted(glob.glob(os.path.join(directory, pattern)))

        print(f"找到 {len(files)} 个文件")
        return self.publish_batch(files, skip_if_published=skip_if_published)

    # ---- 内部方法 ----

    @staticmethod
    def _extract_title(content, fallback):
        """从章节内容中提取标题"""
        lines = content.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            # 标题行：比较短，可能包含"第x章"
            if len(line) < 50:
                return line.replace('#', '').strip()
            # 第一行非空行（短于80字）
            if len(line) < 80:
                return line[:50]
        return fallback

    @staticmethod
    def _chapter_to_markdown(content, title):
        """将纯文本章节转为 Markdown 格式"""
        lines = content.strip().split('\n')
        md_lines = []

        # 标题
        md_lines.append(f'# {title}')
        md_lines.append('')

        # 正文：每段空行分隔
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # 已有 Markdown 标题，直接保留
                md_lines.append(stripped)
                md_lines.append('')
            elif stripped == '':
                # 空行
                if md_lines and md_lines[-1] != '':
                    md_lines.append('')
            else:
                # 正文段落
                md_lines.append(stripped)
                md_lines.append('')

        return '\n'.join(md_lines)

    @staticmethod
    def _now_str():
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ===== 命令行入口 =====

def main():
    import argparse

    parser = argparse.ArgumentParser(description='小说飞书批量发布工具')
    parser.add_argument('--chapters-dir', help='章节目录路径')
    parser.add_argument('--pattern', default='*.txt', help='文件匹配模式')
    parser.add_argument('--recursive', action='store_true', help='递归子目录')
    parser.add_argument('--file', help='单个文件路径')
    parser.add_argument('--record-file', default='_feishu_published.json',
                        help='发布记录文件路径')
    parser.add_argument('--force', action='store_true', help='强制重新发布（跳过幂等检查）')

    args = parser.parse_args()

    pub = NovelFeishuPublisher(record_file=args.record_file)

    if args.file:
        pub.publish_chapter(args.file, skip_if_published=not args.force)
    elif args.chapters_dir:
        pub.publish_directory(
            args.chapters_dir,
            pattern=args.pattern,
            recursive=args.recursive,
            skip_if_published=not args.force,
        )
    else:
        parser.print_help()
        print("\n示例:")
        print("  python publish_novel_feishu.py --chapters-dir ./hello_novel/novels/cangyuantu/chapters")
        print("  python publish_novel_feishu.py --file ./hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt")
        print("  python publish_novel_feishu.py --chapters-dir ./hello_novel/novels/cangyuantu/chapters --recursive --force")


if __name__ == '__main__':
    main()

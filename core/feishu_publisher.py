"""
飞书文档发布客户端 — 通过 lark-cli 创建文档、插入图片、移动到知识库

使用方式：
    from core.feishu_publisher import FeishuPublisher
    pub = FeishuPublisher()

    # 发布文章
    result = pub.publish_article(
        title="文章标题",
        content_md="# 正文\n...",
        images=[{"path": "img.jpg", "caption": "图1"}]
    )
    print(result['doc_url'])
"""

import os
import sys
import subprocess
import json
import glob
import tempfile
from datetime import datetime

from .config import config

# 桥接 JS 脚本路径（在 core 目录下）
LARK_HELPER_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lark_helper.js')


class FeishuPublisher:
    """飞书文档发布器"""

    def __init__(self):
        self.doc_id = None
        self.doc_url = None

    # ===== 核心操作 =====

    def create_document(self, title, content_md):
        """
        创建飞书文档

        Returns:
            dict: {'success': bool, 'doc_id': str, 'doc_url': str, 'error': str}
        """
        tmp_md = os.path.join(tempfile.gettempdir(), 'feishu_doc_content.md')

        with open(tmp_md, 'w', encoding='utf-8') as f:
            f.write(content_md.lstrip('\n'))

        try:
            stdout, err = self._run_node_helper('create-doc', tmp_md, title)

            if err:
                print(f"[Feishu] 创建文档失败: {err[:300]}")
                return {'success': False, 'error': '创建文档失败'}

            data = self._parse_json_output(stdout)

            if data.get('ok'):
                doc_data = data.get('data', {}).get('document', {})
                self.doc_id = doc_data.get('document_id')
                self.doc_url = doc_data.get('url')
                print(f"[Feishu] 文档创建成功: {self.doc_url}")
                return {
                    'success': True,
                    'doc_id': self.doc_id,
                    'doc_url': self.doc_url
                }

            err_msg = data.get('error', {}).get('message', '未知错误')
            print(f"[Feishu] 创建文档失败: {err_msg}")
            return {'success': False, 'error': err_msg}

        except Exception as e:
            print(f"[Feishu] 命令执行异常: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                os.unlink(tmp_md)
            except OSError:
                pass

    def insert_image(self, image_path, caption=None, selection=None):
        """
        在当前文档中插入图片

        Args:
            image_path: 图片路径
            caption: 图片说明（可选）
            selection: 锚定文本（用 --selection-with-ellipsis 定位插入位置）

        Returns:
            dict: {'success': bool, 'file_token': str}
        """
        if not self.doc_id:
            return {'success': False, 'error': '文档未创建，请先调用 create_document()'}

        abs_image_path = os.path.abspath(image_path)
        if not os.path.exists(abs_image_path):
            return {'success': False, 'error': f'图片不存在: {abs_image_path}'}

        try:
            stdout, err = self._run_node_helper(
                'insert-image', self.doc_id, abs_image_path,
                caption or '', selection or ''
            )

            if err:
                print(f"[Feishu] 图片插入失败: {os.path.basename(abs_image_path)}")
                print(f"[Feishu] 错误: {err[:200]}")
                return {'success': False, 'error': '插入图片失败'}

            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                return {'success': True, 'file_token': None}

            if data.get('ok'):
                file_token = data.get('data', {}).get('file_token')
                print(f"[Feishu] 图片插入成功: {os.path.basename(abs_image_path)}")
                return {'success': True, 'file_token': file_token}

            return {'success': False, 'error': '插入图片失败'}

        except Exception as e:
            print(f"[Feishu] 图片插入异常: {e}")
            return {'success': False, 'error': str(e)}

    def insert_images_batch(self, images):
        """
        批量插入图片

        Args:
            images: [{'path': str, 'caption': str, 'selection': str}, ...]

        Returns:
            list: 每个图片的结果
        """
        results = []
        for img_info in images:
            result = self.insert_image(
                image_path=img_info.get('path'),
                caption=img_info.get('caption'),
                selection=img_info.get('selection')
            )
            results.append({'path': img_info.get('path'), **result})
        return results

    def publish_article(self, title, content_md, images=None):
        """
        一键发布：创建文档 + 插入图片

        Args:
            title: 文档标题
            content_md: Markdown 正文
            images: 图片列表 [{'path': str, 'caption': str}, ...]

        Returns:
            dict: {'success': bool, 'doc_id': str, 'doc_url': str, 'images_count': int}
        """
        print(f"[Feishu] 开始发布文章: {title}")

        create_result = self.create_document(title, content_md)
        if not create_result.get('success'):
            return create_result

        if images:
            print(f"[Feishu] 插入 {len(images)} 张图片...")
            image_results = self.insert_images_batch(images)
            failed = [r for r in image_results if not r.get('success')]
            if failed:
                print(f"[Feishu] 警告: {len(failed)} 张图片插入失败")

        return {
            'success': True,
            'doc_id': self.doc_id,
            'doc_url': self.doc_url,
            'images_count': len(images) if images else 0
        }

    def move_to_wiki(self, wiki_space_id, parent_node_token=None):
        """
        将当前文档移动到飞书知识空间

        Args:
            wiki_space_id: 知识空间 ID
            parent_node_token: 父节点 token（可选）

        Returns:
            dict: {'success': bool}
        """
        if not self.doc_id:
            return {'success': False, 'error': '文档未创建'}

        try:
            args = ['move-to-wiki', self.doc_id, wiki_space_id]
            if parent_node_token:
                args.append(parent_node_token)

            stdout, err = self._run_node_helper(*args)
            if err:
                return {'success': False, 'error': err[:200]}

            data = self._parse_json_output(stdout)
            if data.get('ok'):
                print(f"[Feishu] 文档已移动到知识空间: {wiki_space_id}")
                return {'success': True}
            return {'success': False, 'error': data.get('error', {}).get('message', '移动失败')}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ===== 内部方法 =====

    def _run_node_helper(self, action, *extra_args):
        """调用 Node.js 桥接脚本"""
        env = os.environ.copy()
        env['LARK_CLI_RUN_JS'] = config.LARK_CLI_RUN_JS

        cmd = ['node', LARK_HELPER_JS, action] + list(extra_args)
        result = subprocess.run(
            cmd, capture_output=True, encoding='utf-8', errors='replace', env=env
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return None, stdout + '\n' + stderr

        return stdout, None

    @staticmethod
    def _parse_json_output(stdout):
        """从 stdout 中解析 JSON（兼容前后有其他输出的情况）"""
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            json_start = stdout.find('{')
            json_end = stdout.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                try:
                    return json.loads(stdout[json_start:json_end])
                except json.JSONDecodeError:
                    pass
        return {'ok': False, 'error': {'message': '无法解析响应'}}


# ===== 便捷工具函数 =====

def get_video_frames(video_name, frames_dir=None, max_frames=5):
    """获取视频关键帧列表（用于文章配图）"""
    if frames_dir is None:
        frames_dir = config.get_video_frames_dir(video_name)

    pattern = os.path.join(frames_dir, f"{video_name}_keyframe_*.jpg")
    frames = sorted(glob.glob(pattern))

    if not frames:
        return []

    if len(frames) <= max_frames:
        return frames

    step = len(frames) // max_frames
    return [frames[i] for i in range(0, len(frames), step)][:max_frames]


def generate_article_images(video_name, frames_dir=None, max_frames=5):
    """生成文章配图数据结构（供 FeishuPublisher.insert_images_batch 使用）"""
    frames = get_video_frames(video_name, frames_dir, max_frames)

    images = []
    for i, frame_path in enumerate(frames):
        images.append({
            'path': frame_path,
            'caption': f"视频关键帧 {i + 1}",
            'selection': None
        })

    return images

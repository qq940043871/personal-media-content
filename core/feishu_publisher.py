"""
飞书文档发布客户端 — 通过 lark-cli 创建文档、插入图片、移动到知识库

使用方式：
    from core.feishu_publisher import FeishuPublisher
    pub = FeishuPublisher()

    # 发布文章（兼容旧接口）
    result = pub.publish_article(
        title="文章标题",
        content_md="# 正文\n...",
        images=[{"path": "img.jpg", "caption": "图1"}]
    )
    print(result['doc_url'])

    # 统一契约（MultiPlatformPublisher 使用）
    pr = pub.publish_markdown("标题", "# 正文")   # → PublishResult
    health = pub.health_check()                  # → lark-cli 授权状态
"""

import os
import sys
import subprocess
import json
import tempfile
from datetime import datetime

from .config import config
from .publisher_base import BasePublisher, PublishResult

# 桥接 JS 脚本路径（在 core 目录下）
LARK_HELPER_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lark_helper.js')


class FeishuPublisher(BasePublisher):
    """飞书文档发布器"""

    platform_id = 'feishu'
    platform_name = '飞书文档'

    def __init__(self):
        self.doc_id = None
        self.doc_url = None

    # ===== 统一契约（BasePublisher）=====

    def check_config(self):
        """lark-cli 可用即视为配置完整（授权状态由 health_check 细查）"""
        if os.path.exists(config.LARK_CLI_RUN_JS):
            return True, ''
        return False, (f"lark-cli 不存在: {config.LARK_CLI_RUN_JS}"
                       f"（可用环境变量 LARK_CLI_RUN_JS 覆盖，或 npm i -g @larksuite/cli）")

    def health_check(self):
        """检查 lark-cli 授权状态（bot / user 身份）"""
        stdout, err = self._run_node_helper('auth-status')
        if err is None:
            err = ''
        output = (stdout or '') + '\n' + err
        data = self._parse_json_output(output)

        if not data.get('ok', True):
            return PublishResult(success=False, platform=self.platform_id,
                                 error=f"lark-cli 授权异常: {data.get('error', {}).get('message', '未知')}")

        identities = data.get('identities', {})
        bot_ok = identities.get('bot', {}).get('available', False)
        if identities.get('user', {}).get('available', False):
            return PublishResult(success=True, platform=self.platform_id,
                                 raw={'user': True, 'bot': bot_ok})
        # 建文档走 --as user，bot 身份可用也不够
        return PublishResult(
            success=False, platform=self.platform_id,
            error="lark-cli user 身份未授权（bot 身份" + ("可用但建文档用不到）" if bot_ok else "同样缺失）")
                  + "：请运行 node " + f"\"{config.LARK_CLI_RUN_JS}\" auth login --domain all 完成浏览器授权")

    def publish_markdown(self, title, content_md, options=None) -> PublishResult:
        """统一契约：发布 Markdown 到飞书文档"""
        opts = options or {}
        raw_images = opts.get('images')

        # 归一化：['x.jpg'] 或 [{'path': ...}] 均可
        images = None
        if raw_images:
            images = [img if isinstance(img, dict) else {'path': img} for img in raw_images]

        result = self.publish_article(title, content_md, images=images)
        return PublishResult(
            success=result.get('success', False),
            platform=self.platform_id,
            title=title,
            url=result.get('doc_url', ''),
            id=result.get('doc_id', ''),
            error=result.get('error', ''),
            raw=result,
        )

    # ===== 核心操作 =====

    def create_document(self, title, content_md):
        """
        创建飞书文档

        Returns:
            dict: {'success': bool, 'doc_id': str, 'doc_url': str, 'error': str}
        """
        fd, tmp_md = tempfile.mkstemp(prefix='feishu_doc_', suffix='.md')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
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

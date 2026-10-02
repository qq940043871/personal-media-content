"""
微信公众号发布工具 — 基于微信公众平台 API

定位：tools 对外动作层（skill 化预备，见 tools/README.md 的接口契约）。
功能：
- access_token 获取与缓存
- 上传图文消息内图片 / 永久素材（封面图）
- 新增草稿到草稿箱 / 发布草稿 / 查询发布状态
- Markdown → 微信 HTML 转换（基础版）

用法：
    python -m tools.wechat publish --title "标题" --content-file doc.md [--cover cover.jpg] [--json]
    python -m tools.wechat health --json
示例：
    python -m tools.wechat publish --asset assets/wechat/drafts/x.md --json
输出：
    人读文本；--json 时输出 PublishResult.to_dict()；退出码 0=成功 1=失败
依赖：
    认证公众号凭据（根 .env 的 WECHAT_APP_ID/WECHAT_APP_SECRET），
    且后台「IP 白名单」含本机出口 IP（doctor 会给指引）

也可以作为模块导入：
    from tools.wechat_publisher import WechatPublisher
    pub = WechatPublisher()
    pr = pub.publish_markdown('标题', '# 正文')   # → PublishResult（进草稿箱）
    health = pub.health_check()
"""

import os
import sys
import json
import time
import requests
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.config import config
from tools.publisher_base import BasePublisher, PublishResult


class WechatPublisher(BasePublisher):
    """微信公众号发布客户端"""

    platform_id = 'wechat'
    platform_name = '微信公众号'

    BASE_URL = 'https://api.weixin.qq.com/cgi-bin'

    def __init__(self, app_id=None, app_secret=None):
        self.app_id = app_id or config.WECHAT_APP_ID
        self.app_secret = app_secret or config.WECHAT_APP_SECRET
        self._access_token = None
        self._token_expires_at = 0

    # ===== 统一契约（BasePublisher）=====

    def check_config(self):
        if self.app_id and self.app_secret:
            return True, ''
        return False, '微信公众号未配置（WECHAT_APP_ID / WECHAT_APP_SECRET）'

    def health_check(self) -> PublishResult:
        """实测 access_token 获取；IP 白名单问题给出修复指引"""
        try:
            token = self.get_access_token()
            if token:
                return PublishResult(success=True, platform=self.platform_id,
                                     raw={'token_len': len(token)})
            return PublishResult(success=False, platform=self.platform_id,
                                 error='access_token 获取结果为空')
        except Exception as e:
            msg = str(e)
            if 'invalid ip' in msg:
                msg += ' → 修复：微信公众平台后台 → 设置与开发 → 安全中心 → IP 白名单，添加该出口 IP'
            return PublishResult(success=False, platform=self.platform_id, error=msg)

    def publish_markdown(self, title, content_md, options=None) -> PublishResult:
        """统一契约：Markdown → 公众号草稿箱（可选直接发布）"""
        opts = options or {}
        result = self.publish_article_from_markdown(
            title=title,
            markdown_content=content_md,
            cover_image_path=opts.get('cover_image'),
            author=opts.get('author', ''),
            digest=opts.get('digest', ''),
            content_source_url=opts.get('source_url', ''),
            need_open_comment=opts.get('open_comment', 0),
            only_fans_can_comment=opts.get('fans_only', 0),
            auto_publish=opts.get('publish_now', False),
        )
        return PublishResult(
            success=result.get('success', False),
            platform=self.platform_id,
            title=title,
            url='',
            id=result.get('media_id', ''),
            error=result.get('error', ''),
            raw=result,
        )

    # ===== access_token 管理 =====

    def get_access_token(self, force_refresh=False):
        """
        获取 access_token（自动缓存，过期前自动刷新）

        Returns:
            str: access_token
        """
        now = time.time()

        # 缓存有效（提前5分钟刷新）
        if (not force_refresh
                and self._access_token
                and now < self._token_expires_at - 300):
            return self._access_token

        if not self.app_id or not self.app_secret:
            raise ValueError(
                "缺少微信公众号 AppID 或 AppSecret，请在 .env 中配置 "
                "WECHAT_APP_ID 和 WECHAT_APP_SECRET"
            )

        print("[WeChat] 获取 access_token...")
        url = f"{self.BASE_URL}/token"
        params = {
            'grant_type': 'client_credential',
            'appid': self.app_id,
            'secret': self.app_secret
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'access_token' not in data:
                err_msg = data.get('errmsg', '未知错误')
                raise Exception(f"获取access_token失败: {err_msg}")

            self._access_token = data['access_token']
            self._token_expires_at = now + data.get('expires_in', 7200)
            print("[WeChat] access_token 获取成功")
            return self._access_token

        except requests.exceptions.RequestException as e:
            raise Exception(f"获取access_token网络错误: {e}")

    def _api_url(self, path):
        """拼接带 access_token 的 API URL"""
        token = self.get_access_token()
        sep = '&' if '?' in path else '?'
        return f"{self.BASE_URL}{path}{sep}access_token={token}"

    def _request(self, method, path, **kwargs):
        """统一请求封装，自动处理 token 过期重试"""
        url = self._api_url(path)
        response = requests.request(method, url, timeout=60, **kwargs)
        data = response.json()

        # token 过期，刷新重试一次
        if data.get('errcode') == 40001:
            print("[WeChat] access_token 过期，刷新重试...")
            self.get_access_token(force_refresh=True)
            url = self._api_url(path)
            response = requests.request(method, url, timeout=60, **kwargs)
            data = response.json()

        return data

    # ===== 图片上传 =====

    def upload_image_for_article(self, image_path):
        """
        上传图文消息内的图片，获取可在正文中引用的图片 URL

        注意：这张图不会出现在素材管理中，仅用于图文消息正文内。
        大小限制：10MB，支持 JPG/PNG 格式。

        Args:
            image_path: 本地图片路径

        Returns:
            dict: {'success': bool, 'url': str, 'error': str}
        """
        if not os.path.exists(image_path):
            return {'success': False, 'error': f'图片不存在: {image_path}'}

        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:
            return {'success': False, 'error': f'图片过大({file_size/1024/1024:.2f}MB)，不能超过10MB'}

        print(f"[WeChat] 上传正文图片: {os.path.basename(image_path)}")

        try:
            with open(image_path, 'rb') as f:
                files = {'media': (os.path.basename(image_path), f)}
                data = self._request('POST', '/media/uploadimg', files=files)

            if data.get('errcode', 0) == 0:
                url = data.get('url', '')
                print(f"[WeChat] 图片上传成功: {url[:80]}...")
                return {'success': True, 'url': url}
            else:
                err_msg = data.get('errmsg', '未知错误')
                print(f"[WeChat] 图片上传失败: {err_msg}")
                return {'success': False, 'error': err_msg}

        except Exception as e:
            print(f"[WeChat] 图片上传异常: {e}")
            return {'success': False, 'error': str(e)}

    def upload_material_image(self, image_path):
        """
        上传永久素材图片（用于封面图等）

        注意：永久素材有数量限制，公众号图片素材上限为100000个。
        大小限制：10MB，支持 JPG/PNG 格式。

        Args:
            image_path: 本地图片路径

        Returns:
            dict: {'success': bool, 'media_id': str, 'url': str, 'error': str}
        """
        if not os.path.exists(image_path):
            return {'success': False, 'error': f'图片不存在: {image_path}'}

        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:
            return {'success': False, 'error': f'图片过大({file_size/1024/1024:.2f}MB)，不能超过10MB'}

        print(f"[WeChat] 上传永久素材图片: {os.path.basename(image_path)}")

        try:
            with open(image_path, 'rb') as f:
                files = {'media': (os.path.basename(image_path), f)}
                data = self._request(
                    'POST', '/material/add_material?type=image', files=files
                )

            if 'media_id' in data:
                media_id = data['media_id']
                url = data.get('url', '')
                print(f"[WeChat] 永久素材上传成功: media_id={media_id[:20]}...")
                return {'success': True, 'media_id': media_id, 'url': url}
            else:
                err_msg = data.get('errmsg', '未知错误')
                print(f"[WeChat] 永久素材上传失败: {err_msg}")
                return {'success': False, 'error': err_msg}

        except Exception as e:
            print(f"[WeChat] 永久素材上传异常: {e}")
            return {'success': False, 'error': str(e)}

    # ===== 草稿管理 =====

    def add_draft(self, title, content, thumb_media_id=None,
                  author='', digest='', content_source_url='',
                  need_open_comment=0, only_fans_can_comment=0,
                  article_type='news'):
        """
        新增草稿到公众号草稿箱

        Args:
            title: 标题（不超过32字）
            content: 正文 HTML（支持 HTML 标签，少于2万字符）
            thumb_media_id: 封面图永久素材 ID（图文消息必填）
            author: 作者（不超过16字）
            digest: 摘要（不超过120字，默认取正文前54字）
            content_source_url: 原文链接（阅读原文URL）
            need_open_comment: 是否打开评论 (0关闭/1打开)
            only_fans_can_comment: 是否仅粉丝评论 (0/1)
            article_type: 文章类型 'news'(图文) / 'newspic'(图片)

        Returns:
            dict: {'success': bool, 'media_id': str, 'error': str}
        """
        # 基本校验
        if len(title) > 32:
            print(f"[WeChat] 警告: 标题超过32字，将被截断（当前{len(title)}字）")
            title = title[:32]

        if len(content) > 20000:
            return {'success': False, 'error': f'正文过长({len(content)}字符)，不能超过20000字符'}

        if article_type == 'news' and not thumb_media_id:
            return {'success': False, 'error': '图文消息(article_type=news)必须提供 thumb_media_id（封面图）'}

        article = {
            'title': title,
            'content': content,
            'author': author,
            'digest': digest,
            'content_source_url': content_source_url,
            'need_open_comment': need_open_comment,
            'only_fans_can_comment': only_fans_can_comment,
            'article_type': article_type,
        }

        if thumb_media_id:
            article['thumb_media_id'] = thumb_media_id

        payload = {'articles': [article]}

        print(f"[WeChat] 正在新增草稿: {title}")

        try:
            data = self._request('POST', '/draft/add', json=payload)

            if 'media_id' in data:
                media_id = data['media_id']
                print(f"[WeChat] 草稿创建成功: media_id={media_id[:30]}...")
                return {'success': True, 'media_id': media_id}
            else:
                err_msg = data.get('errmsg', '未知错误')
                errcode = data.get('errcode', '?')
                print(f"[WeChat] 草稿创建失败: [{errcode}] {err_msg}")
                return {'success': False, 'error': err_msg, 'errcode': errcode}

        except Exception as e:
            print(f"[WeChat] 草稿创建异常: {e}")
            return {'success': False, 'error': str(e)}

    def get_draft_list(self, offset=0, count=20, no_content=1):
        """
        获取草稿列表

        Args:
            offset: 偏移量
            count: 数量（最多20）
            no_content: 是否不返回内容 (1不返回/0返回)

        Returns:
            dict: {'success': bool, 'item': list, 'total_count': int}
        """
        payload = {
            'offset': offset,
            'count': count,
            'no_content': no_content
        }

        try:
            data = self._request('POST', '/draft/batchget', json=payload)
            if data.get('errcode', 0) == 0:
                return {'success': True, **data}
            else:
                return {'success': False, 'error': data.get('errmsg', '未知错误')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_draft_count(self):
        """获取草稿总数"""
        try:
            data = self._request('GET', '/draft/count')
            if data.get('errcode', 0) == 0:
                return {'success': True, 'total_count': data.get('total_count', 0)}
            else:
                return {'success': False, 'error': data.get('errmsg', '未知错误')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ===== 发布 =====

    def publish(self, media_id):
        """
        发布草稿（从草稿箱发布到公众号）

        注意：发布成功后，素材将从草稿箱移除。
        发布是异步的，需要用 publish_id 查询状态。

        Args:
            media_id: 草稿的 media_id

        Returns:
            dict: {'success': bool, 'publish_id': str, 'error': str}
        """
        payload = {'media_id': media_id}

        print(f"[WeChat] 正在发布草稿: {media_id[:30]}...")

        try:
            data = self._request('POST', '/freepublish/submit', json=payload)

            if data.get('errcode', 0) == 0:
                publish_id = data.get('publish_id', '')
                print(f"[WeChat] 发布请求已提交: publish_id={publish_id}")
                return {'success': True, 'publish_id': publish_id}
            else:
                err_msg = data.get('errmsg', '未知错误')
                errcode = data.get('errcode', '?')
                print(f"[WeChat] 发布失败: [{errcode}] {err_msg}")
                return {'success': False, 'error': err_msg, 'errcode': errcode}

        except Exception as e:
            print(f"[WeChat] 发布异常: {e}")
            return {'success': False, 'error': str(e)}

    def get_publish_status(self, publish_id):
        """查询发布状态"""
        payload = {'publish_id': publish_id}

        try:
            data = self._request('POST', '/freepublish/get', json=payload)
            if data.get('errcode', 0) == 0:
                return {
                    'success': True,
                    'publish_status': data.get('publish_status'),
                    'article_id': data.get('article_id', ''),
                    'article_detail': data.get('article_detail', {}),
                    'fail_idx': data.get('fail_idx', []),
                }
            else:
                return {'success': False, 'error': data.get('errmsg', '未知错误')}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ===== 便捷方法 =====

    def publish_article_from_markdown(self, title, markdown_content,
                                      cover_image_path=None,
                                      author='', digest='',
                                      content_source_url='',
                                      need_open_comment=0,
                                      only_fans_can_comment=0,
                                      auto_publish=False):
        """
        一键发布：Markdown → 微信HTML → 上传封面 → 创建草稿 → (可选)发布

        Args:
            title: 文章标题
            markdown_content: Markdown 正文
            cover_image_path: 封面图本地路径
            author: 作者
            digest: 摘要
            content_source_url: 原文链接
            need_open_comment: 打开评论
            only_fans_can_comment: 仅粉丝评论
            auto_publish: 是否自动发布（默认只进草稿箱）

        Returns:
            dict: {'success': bool, 'media_id': str, 'publish_id': str, 'error': str}
        """
        # 1. 上传封面图（如果提供了本地路径）
        thumb_media_id = None
        if cover_image_path and os.path.exists(cover_image_path):
            upload_result = self.upload_material_image(cover_image_path)
            if not upload_result.get('success'):
                return {'success': False, 'error': f'封面图上传失败: {upload_result.get("error")}'}
            thumb_media_id = upload_result['media_id']

        # 2. Markdown 转微信 HTML
        html_content = self.markdown_to_wechat_html(markdown_content)

        # 3. 创建草稿
        draft_result = self.add_draft(
            title=title,
            content=html_content,
            thumb_media_id=thumb_media_id,
            author=author,
            digest=digest,
            content_source_url=content_source_url,
            need_open_comment=need_open_comment,
            only_fans_can_comment=only_fans_can_comment,
        )

        if not draft_result.get('success'):
            return draft_result

        result = {
            'success': True,
            'media_id': draft_result['media_id'],
            'publish_id': None
        }

        # 4. 可选：自动发布
        if auto_publish:
            pub_result = self.publish(draft_result['media_id'])
            if pub_result.get('success'):
                result['publish_id'] = pub_result['publish_id']
            else:
                result['publish_error'] = pub_result.get('error')
                print(f"[WeChat] 警告: 草稿已创建但发布失败: {pub_result.get('error')}")

        return result

    # ===== Markdown → 微信 HTML 转换 =====

    @staticmethod
    def markdown_to_wechat_html(md_text):
        """
        基础版 Markdown → 微信公众号 HTML 转换

        支持：
        - 标题（h1~h6）
        - 粗体、斜体
        - 有序/无序列表
        - 引用块
        - 代码块（基础）
        - 行内代码
        - 链接
        - 图片（保留 img 标签，图片需先上传到微信获取URL）
        - 分隔线
        - 段落

        注意：微信公众号对 HTML 标签有严格限制，复杂样式建议使用专门的
        Markdown 转微信工具（如 mdnice、md2wechat 等）。

        Args:
            md_text: Markdown 文本

        Returns:
            str: 微信兼容的 HTML
        """
        lines = md_text.split('\n')
        html_parts = []
        in_code_block = False
        code_buffer = []
        in_list = False
        list_type = None  # 'ul' or 'ol'
        in_quote = False
        quote_buffer = []

        def close_list():
            nonlocal in_list, list_type
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
                list_type = None

        def close_quote():
            nonlocal in_quote, quote_buffer
            if in_quote:
                quote_html = '<br>'.join(quote_buffer)
                html_parts.append(f'<blockquote style="border-left:3px solid #d0d0d0;padding-left:12px;color:#666;margin:12px 0;">{quote_html}</blockquote>')
                in_quote = False
                quote_buffer = []

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 代码块
            if stripped.startswith('```'):
                if not in_code_block:
                    close_list()
                    close_quote()
                    in_code_block = True
                    code_buffer = []
                else:
                    code_html = '\n'.join(code_buffer)
                    html_parts.append(
                        f'<pre style="background:#f7f7f7;padding:12px;border-radius:4px;'
                        f'overflow-x:auto;font-size:14px;line-height:1.6;">'
                        f'<code>{_escape_html(code_html)}</code></pre>'
                    )
                    in_code_block = False
                i += 1
                continue

            if in_code_block:
                code_buffer.append(line)
                i += 1
                continue

            # 空行
            if not stripped:
                close_list()
                close_quote()
                i += 1
                continue

            # 标题
            header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            if header_match:
                close_list()
                close_quote()
                level = len(header_match.group(1))
                text = _inline_format(header_match.group(2))
                sizes = {1: '24px', 2: '20px', 3: '18px', 4: '16px', 5: '15px', 6: '14px'}
                html_parts.append(
                    f'<h{level} style="font-size:{sizes[level]};font-weight:bold;'
                    f'margin:20px 0 12px;line-height:1.5;">{text}</h{level}>'
                )
                i += 1
                continue

            # 分隔线
            if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
                close_list()
                close_quote()
                html_parts.append('<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">')
                i += 1
                continue

            # 引用块
            if stripped.startswith('>'):
                close_list()
                in_quote = True
                quote_text = stripped[1:].strip()
                quote_buffer.append(_inline_format(quote_text))
                i += 1
                continue
            else:
                close_quote()

            # 无序列表
            ul_match = re.match(r'^[-*+]\s+(.+)$', stripped)
            if ul_match:
                if not in_list or list_type != 'ul':
                    close_list()
                    html_parts.append('<ul style="margin:12px 0;padding-left:24px;">')
                    in_list = True
                    list_type = 'ul'
                item_text = _inline_format(ul_match.group(1))
                html_parts.append(f'<li style="margin:6px 0;line-height:1.8;">{item_text}</li>')
                i += 1
                continue

            # 有序列表
            ol_match = re.match(r'^\d+\.\s+(.+)$', stripped)
            if ol_match:
                if not in_list or list_type != 'ol':
                    close_list()
                    html_parts.append('<ol style="margin:12px 0;padding-left:24px;">')
                    in_list = True
                    list_type = 'ol'
                item_text = _inline_format(ol_match.group(1))
                html_parts.append(f'<li style="margin:6px 0;line-height:1.8;">{item_text}</li>')
                i += 1
                continue

            # 普通段落
            close_list()
            para_text = _inline_format(stripped)
            html_parts.append(
                f'<p style="margin:12px 0;line-height:1.8;text-align:justify;">{para_text}</p>'
            )
            i += 1

        close_list()
        close_quote()

        return '\n'.join(html_parts)


# ===== 辅助函数 =====

def _escape_html(text):
    """HTML 转义"""
    return (text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def _inline_format(text):
    """处理行内格式：粗体、斜体、行内代码、链接、图片"""
    # 先保护行内代码
    code_spans = []
    def save_code(m):
        code_spans.append(m.group(1))
        return f'\x00CODE{len(code_spans)-1}\x00'
    text = re.sub(r'`([^`]+)`', save_code, text)

    # 图片 ![alt](url)
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        r'<img src="\2" alt="\1" style="max-width:100%;height:auto;margin:12px 0;">',
        text
    )

    # 链接 [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" style="color:#576b95;text-decoration:none;">\1</a>',
        text
    )

    # 粗体 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight:bold;">\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong style="font-weight:bold;">\1</strong>', text)

    # 斜体 *text* 或 _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)

    # 恢复行内代码
    def restore_code(m):
        idx = int(m.group(1))
        code = code_spans[idx]
        return (f'<code style="background:#f5f5f5;padding:2px 6px;'
                f'border-radius:3px;font-size:13px;color:#c7254e;">{_escape_html(code)}</code>')
    text = re.sub(r'\x00CODE(\d+)\x00', restore_code, text)

    return text


# ===== 独立命令行入口（skill 化契约：--json 输出 / 退出码 0=成功 1=失败）=====

def main():
    import argparse

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--json', action='store_true', help='输出 JSON 结果')
    parser = argparse.ArgumentParser(
        prog='python -m tools.wechat', description='微信公众号发布工具（进草稿箱）')
    sub = parser.add_subparsers(dest='action', required=True)

    p_pub = sub.add_parser('publish', parents=[common], help='发布 Markdown 到公众号草稿箱')
    p_pub.add_argument('--title', help='文章标题（不超过32字；--asset 时默认取文件名）')
    p_pub.add_argument('--content', help='Markdown 正文')
    p_pub.add_argument('--content-file', help='从文件读取 Markdown 正文')
    p_pub.add_argument('--asset', help='资产路径（assets/**/drafts 下；成功后自动归档）')
    p_pub.add_argument('--cover', help='封面图本地路径')
    p_pub.add_argument('--author', help='作者名')
    p_pub.add_argument('--digest', help='摘要（不超过120字）')
    p_pub.add_argument('--source-url', help='原文链接（阅读原文）')
    p_pub.add_argument('--open-comment', action='store_true', help='打开评论')
    p_pub.add_argument('--publish-now', action='store_true', help='创建草稿后立即发布')
    p_pub.add_argument('--asset-root', help='资产库根目录（默认 <仓库>/assets）')

    sub.add_parser('health', parents=[common], help='实测 access_token 获取')

    args = parser.parse_args()

    if args.action == 'publish':
        from tools.asset_store import AssetStore

        title = args.title
        content = args.content or ''
        if args.asset:
            asset_path = os.path.abspath(args.asset)
            with open(asset_path, 'r', encoding='utf-8') as f:
                content = f.read()
            title = title or os.path.splitext(os.path.basename(asset_path))[0]
        if not title:
            raise SystemExit('❌ 请提供 --title（或用 --asset 以文件名代标题）')
        if not content.strip():
            raise SystemExit('❌ 请提供 --content / --content-file / --asset 之一')

        result = WechatPublisher().publish_markdown(title, content, options={
            'cover_image': args.cover,
            'author': args.author or '',
            'digest': args.digest or '',
            'source_url': args.source_url or '',
            'open_comment': 1 if args.open_comment else 0,
            'publish_now': args.publish_now,
        })

        if result.success and args.asset:
            moved = AssetStore(args.asset_root).mark_published(
                os.path.abspath(args.asset), url=result.url, asset_id=result.id)
            if moved.get('success'):
                print(f"[Asset] 已归档: {moved['published_path']}")

        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            if result.success:
                print(f"✅ 草稿创建成功（media_id: {result.id}）"
                      + ('，已发布' if args.publish_now else '，未发布'))
            else:
                print(f"❌ 发布失败: {result.error}")
        raise SystemExit(0 if result.success else 1)

    if args.action == 'health':
        result = WechatPublisher().health_check()
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"{'✅ access_token 正常' if result.success else '❌ ' + result.error}")
        raise SystemExit(0 if result.success else 1)


if __name__ == '__main__':
    main()

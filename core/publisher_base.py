"""
多平台发布统一抽象 — 所有发布平台共用基类

定义统一的发布接口，让飞书、微信公众号、（未来的）知乎/掘金/小红书等
都遵循同一套接口规范，方便批量发布和管理。

统一接口：
    publisher = MultiPlatformPublisher()

    # 一键多平台发布
    results = publisher.publish_all(
        title='文章标题',
        content=markdown_content,
        platforms=['feishu', 'wechat'],
        options={
            'feishu': {'images': [...]},
            'wechat': {'cover_image': 'cover.jpg', 'author': 'xxx'},
        }
    )

    # 单平台发布
    result = publisher.publish('feishu', title, content, options={})

    # 检查支持的平台
    platforms = publisher.available_platforms()
"""

import os
from abc import ABC, abstractmethod


class BasePublisher(ABC):
    """发布器基类 — 所有平台发布器都继承此类"""

    # 平台标识（唯一）
    platform_id = 'base'
    platform_name = '基础发布器'

    @abstractmethod
    def publish(self, title, content, options=None):
        """
        发布内容

        Args:
            title: 标题
            content: Markdown 正文内容
            options: 平台特定参数（dict）

        Returns:
            dict: {
                'success': bool,
                'platform': str,
                'title': str,
                'url': str,        # 发布后的链接（如果有）
                'id': str,         # 平台侧的内容 ID
                'error': str,      # 失败时的错误信息
                'raw': dict,       # 平台原始返回
            }
        """
        pass

    def check_config(self):
        """
        检查配置是否完整

        Returns:
            tuple: (bool, str) — (是否可用, 不可用原因)
        """
        return True, ''


class MultiPlatformPublisher:
    """多平台发布管理器"""

    def __init__(self):
        self._publishers = {}
        self._init_publishers()

    def _init_publishers(self):
        """初始化所有已配置的发布器"""
        # 飞书
        try:
            from .feishu_publisher import FeishuPublisher
            self._publishers['feishu'] = _FeishuAdapter(FeishuPublisher())
        except Exception as e:
            print(f"[MultiPlatform] 飞书发布器初始化失败: {e}")

        # 微信公众号
        try:
            from .wechat_publisher import WechatPublisher
            from .config import config
            if config.WECHAT_APP_ID and config.WECHAT_APP_SECRET:
                self._publishers['wechat'] = _WechatAdapter(WechatPublisher())
            else:
                print("[MultiPlatform] 微信公众号未配置，跳过")
        except Exception as e:
            print(f"[MultiPlatform] 微信发布器初始化失败: {e}")

    def available_platforms(self):
        """获取可用的平台列表"""
        return list(self._publishers.keys())

    def get_publisher(self, platform_id):
        """获取指定平台的发布器"""
        return self._publishers.get(platform_id)

    def publish(self, platform_id, title, content, options=None):
        """发布到单个平台"""
        publisher = self._publishers.get(platform_id)
        if not publisher:
            return {
                'success': False,
                'platform': platform_id,
                'error': f'不支持的平台: {platform_id}'
            }

        print(f"[发布] 正在发布到 {publisher.platform_name}...")
        try:
            result = publisher.publish(title, content, options or {})
            if result.get('success'):
                print(f"[发布] ✅ {publisher.platform_name} 发布成功")
            else:
                print(f"[发布] ❌ {publisher.platform_name} 发布失败: {result.get('error')}")
            return result
        except Exception as e:
            print(f"[发布] ❌ {publisher.platform_name} 异常: {e}")
            return {
                'success': False,
                'platform': platform_id,
                'error': str(e),
            }

    def publish_all(self, title, content, platforms=None, options=None):
        """
        发布到多个平台

        Args:
            title: 标题
            content: Markdown 正文
            platforms: 平台列表，None 表示所有可用平台
            options: {platform_id: {options_dict}}

        Returns:
            dict: {
                'success_count': int,
                'fail_count': int,
                'results': [dict, ...]
            }
        """
        if platforms is None:
            platforms = self.available_platforms()

        options = options or {}
        results = []
        success_count = 0
        fail_count = 0

        for platform_id in platforms:
            result = self.publish(
                platform_id, title, content,
                options=options.get(platform_id, {})
            )
            results.append(result)
            if result.get('success'):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n[发布] 完成：成功 {success_count} 个，失败 {fail_count} 个")

        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'total': len(platforms),
            'results': results,
        }


# ===== 平台适配器 =====

class _FeishuAdapter(BasePublisher):
    """飞书发布适配器"""

    platform_id = 'feishu'
    platform_name = '飞书文档'

    def __init__(self, publisher):
        self.pub = publisher

    def publish(self, title, content, options=None):
        opts = options or {}
        raw_images = opts.get('images')

        # 归一化 images 格式：
        # 支持三种输入：
        #   1. [{'path': 'x.jpg', 'caption': '...'}, ...]  (标准格式)
        #   2. ['x.jpg', 'y.jpg']  (纯路径列表)
        #   3. None
        images = None
        if raw_images:
            images = []
            for img in raw_images:
                if isinstance(img, str):
                    images.append({'path': img})
                elif isinstance(img, dict):
                    images.append(img)

        result = self.pub.publish_article(title, content, images=images)

        return {
            'success': result.get('success', False),
            'platform': self.platform_id,
            'title': title,
            'url': result.get('doc_url', ''),
            'id': result.get('doc_id', ''),
            'error': result.get('error', ''),
            'raw': result,
        }


class _WechatAdapter(BasePublisher):
    """微信公众号发布适配器"""

    platform_id = 'wechat'
    platform_name = '微信公众号'

    def __init__(self, publisher):
        self.pub = publisher

    def publish(self, title, content, options=None):
        opts = options or {}

        result = self.pub.publish_article_from_markdown(
            title=title,
            markdown_content=content,
            cover_image_path=opts.get('cover_image'),
            author=opts.get('author', ''),
            digest=opts.get('digest', ''),
            content_source_url=opts.get('source_url', ''),
            need_open_comment=opts.get('open_comment', 0),
            only_fans_can_comment=opts.get('fans_only', 0),
            auto_publish=opts.get('publish_now', False),
        )

        return {
            'success': result.get('success', False),
            'platform': self.platform_id,
            'title': title,
            'url': '',  # 微信草稿没有直接访问 URL
            'id': result.get('media_id', ''),
            'error': result.get('error', ''),
            'publish_id': result.get('publish_id', ''),
            'raw': result,
        }

"""
多平台发布统一契约 — 发布器协议 + 按名注册（tools 对外动作层的基座）

发布器实现 BasePublisher 协议：

    class XxxPublisher(BasePublisher):
        platform_id = 'xxx'
        platform_name = 'XXX'

        def publish_markdown(self, title, content_md, options=None) -> PublishResult: ...
        def health_check(self) -> PublishResult: ...          # 可选，默认 unsupported
        def check_config(self) -> tuple[bool, str]: ...       # 可选，默认 (True, '')

使用方式：

    publisher = MultiPlatformPublisher()

    # 一键多平台发布（结果为 PublishResult / 兼容 dict 访问）
    summary = publisher.publish_all(
        title='文章标题',
        content=markdown_content,
        platforms=['feishu', 'wechat'],
        options={
            'feishu': {'images': [...]},
            'wechat': {'cover_image': 'cover.jpg', 'author': 'xxx'},
        }
    )

    # 单平台 / 健康检查
    result = publisher.publish('feishu', title, content)
    health = publisher.health_check_all()
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PublishResult:
    """统一的发布/健康检查结果（可当 dict 用：result['success']）"""

    success: bool = False
    platform: str = ''
    title: str = ''
    url: str = ''
    id: str = ''
    error: str = ''
    raw: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            'success': self.success,
            'platform': self.platform,
            'title': self.title,
            'url': self.url,
            'id': self.id,
            'error': self.error,
            'raw': self.raw,
        }

    # ---- dict 风格访问（兼容旧消费方 result['success'] / result.get('url')）----

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __contains__(self, key):
        return hasattr(self, key) or key in ('publish_id',)

    def get(self, key, default=None):
        if key == 'publish_id':
            return self.raw.get('publish_id', default)
        return getattr(self, key, default)


class BasePublisher(ABC):
    """发布器基类 — 所有平台发布器都实现此协议"""

    # 平台标识（唯一）
    platform_id = 'base'
    platform_name = '基础发布器'

    @abstractmethod
    def publish_markdown(self, title, content_md, options=None) -> PublishResult:
        """
        发布 Markdown 内容

        Args:
            title: 标题
            content_md: Markdown 正文
            options: 平台特定参数（dict）

        Returns:
            PublishResult
        """

    def health_check(self) -> PublishResult:
        """平台连通性/配置检查（子类按需实现）"""
        return PublishResult(success=False, platform=self.platform_id,
                             error=f'{self.platform_name} 未实现 health_check')

    def check_config(self):
        """
        检查配置是否完整

        Returns:
            tuple: (bool, str) — (是否可用, 不可用原因)
        """
        return True, ''

    # 兼容别名：旧适配器接口名
    def publish(self, title, content, options=None) -> PublishResult:
        return self.publish_markdown(title, content, options)


class MultiPlatformPublisher:
    """多平台发布管理器 — 按名注册，初始化失败不吞异常（记录到 init_errors）"""

    def __init__(self, platforms=None):
        self._publishers = {}
        self.init_errors = {}
        self._init_publishers(platforms)

    def _init_publishers(self, platforms=None):
        """实例化已登记的发布器；未配置/初始化失败的平台记入 init_errors"""
        wanted = platforms or list(KNOWN_PLATFORMS)
        for platform_id in wanted:
            factory = _load_publisher(platform_id)
            if not factory:
                self.init_errors[platform_id] = f'未知平台: {platform_id}'
                continue
            try:
                publisher = factory()
                ok, reason = publisher.check_config()
                if not ok:
                    self.init_errors[platform_id] = reason
                    continue
                self._publishers[platform_id] = publisher
            except Exception as e:
                self.init_errors[platform_id] = f'初始化失败: {e}'

    def available_platforms(self):
        """获取可用的平台列表"""
        return list(self._publishers.keys())

    def get_publisher(self, platform_id):
        """获取指定平台的发布器"""
        return self._publishers.get(platform_id)

    def publish(self, platform_id, title, content, options=None) -> PublishResult:
        """发布到单个平台"""
        publisher = self._publishers.get(platform_id)
        if not publisher:
            reason = self.init_errors.get(platform_id, f'不支持的平台: {platform_id}')
            return PublishResult(success=False, platform=platform_id, error=reason)

        print(f"[发布] 正在发布到 {publisher.platform_name}...")
        try:
            result = publisher.publish_markdown(title, content, options or {})
            if result.success:
                print(f"[发布] ✅ {publisher.platform_name} 发布成功")
            else:
                print(f"[发布] ❌ {publisher.platform_name} 发布失败: {result.error}")
            return result
        except Exception as e:
            print(f"[发布] ❌ {publisher.platform_name} 异常: {e}")
            return PublishResult(success=False, platform=platform_id, error=str(e))

    def publish_all(self, title, content, platforms=None, options=None):
        """
        发布到多个平台

        Args:
            title: 标题
            content: Markdown 正文
            platforms: 平台列表，None 表示所有可用平台
            options: {platform_id: {options_dict}}

        Returns:
            dict: {'success_count': int, 'fail_count': int, 'total': int, 'results': [PublishResult]}
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
            if result.success:
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

    def health_check_all(self, platforms=None):
        """对（已初始化的）平台逐一做健康检查 → {platform_id: PublishResult}"""
        wanted = platforms or self.available_platforms()
        return {
            platform_id: self._publishers[platform_id].health_check()
            for platform_id in wanted
            if platform_id in self._publishers
        }


def _load_publisher(platform_id):
    """
    延迟导入发布器实现，避免循环依赖与无关平台的导入成本。
    新平台在此登记 (platform_id → Publisher 类) 即可被 MultiPlatformPublisher 发现。
    """
    if platform_id == 'feishu':
        from publishing.feishu_publisher import FeishuPublisher
        return FeishuPublisher
    if platform_id == 'wechat':
        from publishing.wechat_publisher import WechatPublisher
        return WechatPublisher
    if platform_id == 'douyin':
        from publishing.douyin_publisher import DouyinPublisher
        return DouyinPublisher
    return None


# 当前已登记的平台
KNOWN_PLATFORMS = ('feishu', 'wechat', 'douyin')

"""
抖音发布工具 — Playwright 自动化创作者后台（creator.douyin.com）

定位：tools 对外动作层（skill 化预备，见 publishing/README.md 的接口契约）。
为什么走浏览器自动化：抖音没有面向个人开发者的视频发布开放 API
（开放平台的视频发布能力需要企业资质与应用审核），社区通行做法是
Playwright 驱动创作者后台 + 登录态 Cookie 免扫码（思路参考 social-auto-upload）。

用法：
    python -m publishing.douyin login                              # 首次：扫码保存登录态
    python -m publishing.douyin publish --video-file v.mp4 --title "标题" --tags 生活 vlog --json
    python -m publishing.douyin publish --asset assets/videos/douyin/drafts/v.mp4 --json
    python -m publishing.douyin health --json                      # 实测登录态有效性
输出：
    人读文本；--json 时输出 PublishResult.to_dict()；退出码 0=成功 1=失败
依赖：
    pip install playwright && playwright install chromium；
    登录态 Cookie 在 system/storage/douyin/cookies.json（不入库）

也可以作为模块导入：
    from publishing.douyin_publisher import DouyinPublisher
    pub = DouyinPublisher()
    pr = pub.publish_markdown('标题', '', options={'video': 'v.mp4', 'tags': ['生活']})

说明与限制：
- 发布契约是图文契约（publish_markdown），抖音以视频为准载：markdown 正文不上传，
  视频通过 options['video'] 传入；options['desc'] 可覆盖描述文案。
- 话题标签逐个输入后回车尝试关联话题联想，未命中则保留纯文本。
- 创作者后台改版会导致选择器失效——全部集中在类常量 SEL_*，改版时只改这里。
- 风险提示：浏览器自动化属非官方接口，请控制发布频率，账号风险自担。
"""

import os
import re
import json
import time
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.config import config
from publishing.publisher_base import BasePublisher, PublishResult


def _playwright_available():
    """检测 playwright 依赖（独立函数便于测试桩替换与 doctor 复用）"""
    try:
        import playwright  # noqa: F401
        return True, ''
    except ImportError as e:
        return False, (f'未安装 playwright（pip install playwright && '
                       f'playwright install chromium）: {e}')


def _clean_tags(tags):
    """标签输入归一化 → ['生活', 'vlog']；str 按空白/中英文逗号切分，去开头 #"""
    if not tags:
        return []
    if isinstance(tags, str):
        tags = re.split(r'[\s,，、]+', tags)
    return [str(t).strip().lstrip('#') for t in tags if str(t).strip()]


def _format_tags(tags):
    """标签 → 文案尾部话题串（'#a #b '），兼容 str / list / None"""
    return ''.join(f'#{t} ' for t in _clean_tags(tags))


class DouyinPublisher(BasePublisher):
    """抖音视频发布器（Playwright 自动化创作者后台）"""

    platform_id = 'douyin'
    platform_name = '抖音'

    CREATOR_HOME = 'https://creator.douyin.com/'
    # 2026-10 起抖音发布页迁移为 content/post/video（旧 content/upload 会重定向，直达少一次跳转）
    UPLOAD_URL = 'https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page'
    MANAGE_URL = 'https://creator.douyin.com/creator-micro/content/manage'

    # 创作者后台改版时集中调整这些选择器
    SEL_FILE_INPUT = 'input[type="file"]'
    SEL_EDITORS = ('div[contenteditable="true"]', '.ql-editor[contenteditable="true"]')
    # 发布按钮：accessible name / 文本严格等于「发布」（避免误点「定时发布」）
    SEL_PUBLISH_RE = re.compile(r'^\s*发布\s*$')

    # 判定登录失效的页面特征文案
    LOGIN_MARKERS = ('扫码登录', '二维码', '登录后即可')

    def __init__(self, cookies_file=None):
        self.cookies_file = cookies_file or config.DOUYIN_COOKIES_FILE

    # ===== 统一契约（BasePublisher）=====

    def check_config(self):
        ok, reason = _playwright_available()
        if not ok:
            return False, reason
        if not os.path.exists(self.cookies_file):
            return False, (f'抖音未配置登录态: {self.cookies_file}'
                           f'（先运行 python media-cli.py douyin login 扫码授权）')
        try:
            if not self._read_cookies().get('sessionid'):
                return False, ('登录态文件缺少 sessionid Cookie（可能保存不完整），'
                               '请重新运行 python media-cli.py douyin login')
        except Exception as e:
            return False, f'登录态文件解析失败: {e}'
        return True, ''

    def health_check(self) -> PublishResult:
        """实测登录态：带 Cookie 访问上传页，检查是否被要求重新登录"""
        ok, reason = self.check_config()
        if not ok:
            return PublishResult(success=False, platform=self.platform_id, error=reason)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            return PublishResult(success=False, platform=self.platform_id, error=str(e))

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # 体检保持无头，静默快速
                try:
                    context = browser.new_context(storage_state=self.cookies_file)
                    page = context.new_page()
                    page.goto(self.UPLOAD_URL, wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(3000)
                    body_text = page.locator('body').inner_text(timeout=10000)
                    logged_in = ('creator-micro' in page.url
                                 and not any(m in body_text for m in self.LOGIN_MARKERS))
                finally:
                    browser.close()
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_id,
                                 error=f'访问创作者后台失败: {e}')

        if logged_in:
            return PublishResult(success=True, platform=self.platform_id,
                                 url=self.CREATOR_HOME, raw={'cookies': self.cookies_file})
        return PublishResult(
            success=False, platform=self.platform_id,
            error='登录态已失效（上传页要求重新登录），'
                  '请运行 python media-cli.py douyin login 重新扫码')

    def publish_markdown(self, title, content_md, options=None) -> PublishResult:
        """统一契约：视频上传发布（markdown 正文不适用；视频走 options['video']）"""
        opts = options or {}
        video = opts.get('video') or ''
        if not video:
            return PublishResult(
                success=False, platform=self.platform_id, title=title,
                error='抖音发布需要视频：options["video"]'
                      '（CLI 用 --video-file / --video；图文发布暂不支持）')
        if not os.path.exists(video):
            return PublishResult(success=False, platform=self.platform_id, title=title,
                                 error=f'视频文件不存在: {video}')

        text = (opts.get('desc') or '').strip() or title
        tags = _clean_tags(opts.get('tags'))
        try:
            raw = self._publish_video_via_browser(video, text, tags)
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_id, title=title,
                                 error=str(e))
        return PublishResult(success=True, platform=self.platform_id, title=title,
                             url=self.MANAGE_URL, raw=raw)

    # ===== 登录态管理 =====

    def _read_cookies(self):
        """读取登录态文件 → {cookie_name: value}（仅 douyin.com 域）"""
        with open(self.cookies_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        return {c.get('name', ''): c.get('value', '')
                for c in state.get('cookies', [])
                if 'douyin.com' in c.get('domain', '')}

    def login(self, timeout=300) -> PublishResult:
        """弹出浏览器扫码登录创作者后台，保存登录态 Cookie（必须有界面环境）"""
        ok, reason = _playwright_available()
        if not ok:
            return PublishResult(success=False, platform=self.platform_id, error=reason)
        from playwright.sync_api import sync_playwright

        os.makedirs(os.path.dirname(self.cookies_file) or '.', exist_ok=True)
        print(f"[抖音] 打开浏览器，请在页面中扫码登录（{timeout}s 内完成）...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)  # 扫码必须有界面
                try:
                    context = browser.new_context(viewport={'width': 1280, 'height': 860})
                    page = context.new_page()
                    page.goto(self.CREATOR_HOME, wait_until='domcontentloaded', timeout=60000)
                    page.wait_for_url(re.compile(r'creator-micro'), timeout=timeout * 1000)
                    page.wait_for_timeout(2000)
                    context.storage_state(path=self.cookies_file)
                finally:
                    browser.close()
        except Exception as e:
            return PublishResult(success=False, platform=self.platform_id,
                                 error=f'扫码登录未完成: {e}')

        if not self._read_cookies().get('sessionid'):
            return PublishResult(success=False, platform=self.platform_id,
                                 error='登录后未取到 sessionid Cookie，请重试 douyin login')
        print(f"[抖音] 登录态已保存: {self.cookies_file}")
        return PublishResult(success=True, platform=self.platform_id, url=self.CREATOR_HOME)

    # ===== 发布流程（Playwright）=====

    def _publish_video_via_browser(self, video_path, text, tags):
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

        print(f"[抖音] 打开创作者后台（headless={config.DOUYIN_HEADLESS}）...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.DOUYIN_HEADLESS)
            try:
                context = browser.new_context(
                    storage_state=self.cookies_file,
                    viewport={'width': 1380, 'height': 900},
                )
                page = context.new_page()
                page.goto(self.UPLOAD_URL, wait_until='domcontentloaded', timeout=60000)
                try:
                    page.wait_for_selector(self.SEL_FILE_INPUT, state='attached', timeout=30000)
                except PlaywrightTimeout:
                    raise RuntimeError(
                        '上传页未就绪：登录态可能已失效，'
                        '请运行 python media-cli.py douyin login 重新扫码')

                print(f"[抖音] 上传视频: {os.path.basename(video_path)}"
                      f"（大文件耗时较长，进度见下方日志/浏览器窗口）")
                page.set_input_files(self.SEL_FILE_INPUT, video_path)
                self._wait_upload_done(page)
                self._fill_description(page, text, tags)

                btn = self._publish_button(page)
                if btn is None:
                    raise RuntimeError('未找到发布按钮（创作者后台可能改版，'
                                       '请更新 core/douyin_publisher.py 的选择器）')
                btn.click()
                print("[抖音] 已点击发布，等待平台回执...")
                if not self._wait_publish_done(page):
                    raise RuntimeError('已点击发布但未确认到成功回执，'
                                       '请先到创作者后台核对，避免重复发布')
                # 回执可能是假阳性（页面跳转≠作品落库）：到内容管理页核对标题
                if not self._verify_in_manage(page, text):
                    raise RuntimeError('发布回执已确认，但内容管理页未见该作品'
                                       '（可能被平台秒删或仍在入库延迟）——'
                                       '请先到创作者后台人工核对，避免盲目重发')
            finally:
                browser.close()
        return {'video': video_path, 'tags': tags, 'confirmed': True}

    def _publish_button(self, page):
        """定位发布按钮：严格匹配「发布」文本，避免误点「定时发布」"""
        loc = page.locator('button').filter(has_text=self.SEL_PUBLISH_RE)
        if loc.count() > 0:
            return loc.first
        fallback = page.locator('button[class*="publish"]:not([class*="schedule"])')
        return fallback.first if fallback.count() > 0 else None

    def _has_text(self, page, texts):
        for t in texts:
            try:
                if page.get_by_text(t).count() > 0:
                    return True
            except Exception:
                pass
        return False

    def _upload_progress(self, page):
        """从页面任意 progress 元素文本中解析百分比；取不到返回 None"""
        try:
            return page.evaluate(
                """() => {
                    for (const el of document.querySelectorAll('[class*="progress"]')) {
                        const m = (el.textContent || '').match(/(\\d+)\\s*%/);
                        if (m) return parseInt(m[1], 10);
                    }
                    return null;
                }""")
        except Exception:
            return None

    def _wait_upload_done(self, page):
        """轮询等待视频上传完成；超时抛错而不是静默继续"""
        timeout = config.DOUYIN_UPLOAD_TIMEOUT
        deadline = time.time() + timeout
        last_pct = None
        while time.time() < deadline:
            if self._has_text(page, ('重新上传', '上传成功')):
                return
            pct = self._upload_progress(page)
            if pct != last_pct:
                print(f"[抖音] 上传进度: {'进行中' if pct is None else f'{pct}%'}")
                last_pct = pct
            btn = self._publish_button(page)
            if btn is not None and btn.is_enabled() and pct in (None, 100):
                return
            page.wait_for_timeout(2000)
        raise RuntimeError(f'视频上传未在 {timeout}s 内完成'
                           f'（可调大 .env 的 DOUYIN_UPLOAD_TIMEOUT）')

    def _fill_description(self, page, text, tags):
        """描述框输入文案；话题逐个输入并回车尝试关联联想（未命中则留纯文本）"""
        editor = None
        for sel in self.SEL_EDITORS:
            loc = page.locator(sel)
            if loc.count() > 0:
                editor = loc.first
                break
        if editor is None:
            raise RuntimeError('未找到作品描述输入框（创作者后台可能改版，'
                               '请更新 core/douyin_publisher.py 的 SEL_EDITORS）')
        editor.click()
        page.wait_for_timeout(500)
        if text:
            page.keyboard.type(text, delay=20)
        for tag in tags:
            page.keyboard.press('Enter')
            page.keyboard.type(f'#{tag}', delay=20)
            page.wait_for_timeout(1000)   # 等话题联想浮层
            page.keyboard.press('Enter')  # 命中联想第一项；无浮层则为换行
            page.wait_for_timeout(300)
        page.wait_for_timeout(500)

    def _wait_publish_done(self, page, timeout=60):
        """发布回执：跳转内容管理页或出现成功提示，二者其一即确认"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if 'content/manage' in page.url or self._has_text(page, ('发布成功',)):
                return True
            page.wait_for_timeout(1500)
        return False

    def _verify_in_manage(self, page, text, timeout=30):
        """发布后核验：内容管理页的作品列表里应能找到文案片段（回执可能假阳性）"""
        import re as _re
        frags = [f for f in _re.split(r'[，。｜|#!\s]+', text or '') if len(f) >= 4]
        if not frags:
            frags = [text] if text else []
        deadline = time.time() + timeout
        while time.time() < deadline:
            page.goto(self.MANAGE_URL, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)
            body = page.inner_text('body')
            if any(f in body for f in frags):
                return True
            page.wait_for_timeout(5000)
        return False


# ===== 独立命令行入口（skill 化契约：--json 输出 / 退出码 0=成功 1=失败）=====

def main():
    import argparse

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--json', action='store_true', help='输出 JSON 结果')
    parser = argparse.ArgumentParser(
        prog='python -m publishing.douyin', description='抖音发布工具（Playwright 自动化创作者后台）')
    sub = parser.add_subparsers(dest='action', required=True)

    p_login = sub.add_parser('login', parents=[common], help='扫码登录创作者后台，保存登录态 Cookie')
    p_login.add_argument('--timeout', type=int, default=300, help='等待扫码的超时秒数（默认300）')

    p_pub = sub.add_parser('publish', help='上传发布视频')
    p_pub.add_argument('--video-file', help='视频文件路径')
    p_pub.add_argument('--asset', help='视频资产路径（assets/videos/douyin/drafts 下；成功后自动归档）')
    p_pub.add_argument('--title', help='视频标题/描述文案（--asset 时默认取文件名）')
    p_pub.add_argument('--desc', help='描述文案（默认用标题）')
    p_pub.add_argument('--tags', nargs='*', help='话题标签（如 生活 vlog）')
    p_pub.add_argument('--asset-root', help='资产库根目录（默认 <仓库>/assets）')

    sub.add_parser('health', parents=[common], help='检查抖音登录态是否有效')

    args = parser.parse_args()

    if args.action == 'login':
        result = DouyinPublisher().login(timeout=args.timeout)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print('✅ 抖音登录态已就绪' if result.success else f"❌ 登录失败: {result.error}")
        raise SystemExit(0 if result.success else 1)

    if args.action == 'publish':
        from publishing.asset_store import AssetStore

        video = args.video_file
        title = args.title
        if args.asset:
            video = os.path.abspath(args.asset)
            title = title or os.path.splitext(os.path.basename(video))[0]
        if not video:
            raise SystemExit('❌ 请提供 --video-file 或 --asset')
        if not title:
            raise SystemExit('❌ 请提供 --title')

        result = DouyinPublisher().publish_markdown(title, '', options={
            'video': video, 'tags': args.tags or [], 'desc': args.desc or ''})

        if result.success and args.asset:
            moved = AssetStore(args.asset_root).mark_published(
                os.path.abspath(args.asset), url=result.url, asset_id=result.id)
            if moved.get('success'):
                print(f"[Asset] 已归档: {moved['published_path']}")

        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print('✅ 发布流程完成，作品进入平台审核' if result.success
                  else f"❌ 发布失败: {result.error}")
        raise SystemExit(0 if result.success else 1)

    if args.action == 'health':
        result = DouyinPublisher().health_check()
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print('✅ 抖音登录态有效' if result.success else f"❌ {result.error}")
        raise SystemExit(0 if result.success else 1)


if __name__ == '__main__':
    main()

"""
微信公众号 API 工具函数

封装 access_token 获取、图片上传、封面图上传、草稿创建等接口。
"""
import json
import requests
from typing import Optional

from creation.wechat_agent.tools.cover_generator import _resolve_cover_image_bytes


def get_wechat_access_token(appid: str, appsecret: str) -> str:
    """通过 AppID + AppSecret 获取 access_token"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": appid,
        "secret": appsecret
    }
    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()
    if "access_token" not in data:
        raise Exception(f"获取 access_token 失败: {data}")
    return data["access_token"]


def upload_image_to_wechat(access_token: str, image_data: bytes, image_type: str = "image") -> str:
    """
    上传图片到微信素材库，获取图片 URL（用于正文配图）

    Args:
        access_token: 微信 access_token
        image_data: 图片二进制数据
        image_type: 图片类型，默认 image

    Returns:
        图片 URL
    """
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    files = {"media": ("image.png", image_data, "image/png")}
    resp = requests.post(url, files=files, timeout=30)
    data = resp.json()
    if "url" not in data:
        raise Exception(f"上传图片失败: {data}")
    return data["url"]


def upload_thumb_media(access_token: str, cover_image=None, title: str = "AI技术文章") -> str:
    """
    上传封面图到微信素材库（作为文章封面）

    Args:
        access_token: 微信 access_token
        cover_image: 封面图数据（bytes / base64 str / URL），None 时使用默认封面
        title: 文章标题，用于默认封面的文字渲染
    """
    img_bytes = _resolve_cover_image_bytes(cover_image, title)
    print(f"  [UPLOAD] 上传封面图到微信素材库 ({len(img_bytes)} bytes)...")

    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    files = {"media": ("cover.jpg", img_bytes, "image/jpeg")}
    resp = requests.post(url, files=files, timeout=30)
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise Exception(f"上传封面图失败: {data}")
    return data["media_id"]


def add_wechat_draft(access_token: str, title: str, content_html: str, thumb_media_id: str,
                     author: str = None, digest: str = None,
                     need_open_comment: int = 0, only_fans_can_comment: int = 0) -> str:
    """
    创建微信草稿

    Args:
        access_token: 微信 access_token
        title: 文章标题
        content_html: HTML 正文内容
        thumb_media_id: 封面图 media_id
        author: 作者名（可选）
        digest: 摘要（可选，默认用 title 前 120 字）
        need_open_comment: 是否开启评论（0/1）
        only_fans_can_comment: 是否仅粉丝可评论（0/1）

    Returns:
        草稿 media_id
    """
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    article = {
        "title": title,
        "content": content_html,
        "thumb_media_id": thumb_media_id,
        "content_source_url": "",
        "need_open_comment": need_open_comment,
        "only_fans_can_comment": only_fans_can_comment,
    }
    if author:
        article["author"] = author
    if digest:
        article["digest"] = digest

    json_data = json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, data=json_data, timeout=15)
    data = resp.json()
    if data.get("errcode", 0) != 0:
        raise Exception(f"创建草稿失败: {data}")
    return data["media_id"]
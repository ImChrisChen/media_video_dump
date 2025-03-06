from typing import Optional
from pydantic import BaseModel, HttpUrl


class DownloadRequest(BaseModel):
    """下载视频的请求模型

    支持的视频平台示例:
    - YouTube: https://www.youtube.com/watch?v=oJx9DpXtmAE
    - TikTok: https://www.tiktok.com/@username/video/1234567890
    - Facebook: https://www.facebook.com/watch?v=1234567890
    - Instagram: https://www.instagram.com/p/abcdefgh/
    """

    url: str
    proxy: Optional[str] = None
    resolution: Optional[str] = None


class GetVideoResolutionsRequest(BaseModel):
    """获取视频分辨率列表的请求模型"""

    url: str
    proxy: Optional[str] = None


class GetVideoListRequest(BaseModel):
    """获取网址中的视频列表的请求模型"""

    url: str
    proxy: Optional[str] = None

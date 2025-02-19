import json
from math import inf
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
import yt_dlp
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime


class MediaTransferService:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        self.log_file = os.path.join(download_dir, 'download_history.jsonl')
        os.makedirs(self.download_dir, exist_ok=True)

    def _log_download(self, info: Dict[str, Any], url: str):
        """记录下载历史"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "title": info.get('title'),
            "format": info.get('format'),
            "formats": info.get('formats'),
            "format_id": info.get('format_id'),
            "resolution": info.get('resolution'),
            "filesize": info.get('filesize'),
            "duration": info.get('duration'),
            "view_count": info.get('view_count'),
            "webpage_url": info.get('webpage_url'),
            "extractor": info.get('extractor'),
            "download_path": os.path.join(self.download_dir, f"{info.get('title')}.{info.get('ext')}")
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def get_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """获取视频可用的格式列表"""
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []

                for f in info['formats']:
                    format_info = {
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution', 'unknown'),
                        'filesize': f.get('filesize', 'unknown'),
                        'format_note': f.get('format_note', ''),
                        'fps': f.get('fps'),
                    }
                    
                    if f.get('ext') == 'mp4' and f.get('format_note'):
                        formats.append(format_info)

                return formats
        except Exception as e:
            raise Exception(f"Failed to get formats: {str(e)}")

    def _progress_hook(self, d):
        if d['status'] == 'downloading':
            # 0-100
            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100 if d['total_bytes'] else 0
            print('video download percent:', percent)
            # print(f"Downloading {percent:.2f}% at {d['_speed_str']} ETA {d['_eta_str']}")
        elif d['status'] == 'finished':
            print('Download finished, now post-processing...')

    def download(self, url: str, output_path: str = None, format_id: Optional[str] = None, resolution: Optional[str] = None, max_filename_length: int = 150, proxy: Optional[str] = None) -> Dict[str, Any]:
        """下载视频，可以指定格式ID、分辨率和代理"""
        if output_path is None:
            output_path = os.path.join(self.download_dir, '%(upload_date).100s_%(id)s_%(resolution)s_%(title)s.%(ext)s')

        # 设置 yt-dlp 选项
        ydl_opts = {
            'outtmpl': output_path,  # 输出文件名模板
            'noplaylist': True,  # 如果 URL 是播放列表，只下载单个视频
            'overwrites': True,  # 允许覆盖已存在的文件
            # 确保显示进度条
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],  # 添加进度钩子函数
        }

        # 如果提供了代理，添加到选项中
        if proxy:
            ydl_opts['proxy'] = proxy

        # 根据分辨率或格式ID选择下载格式
        if resolution:
            ydl_opts['format'] = f'bv[height={resolution.split("x")[1]}][ext=mp4]+ba[ext=m4a]'
        elif format_id:
            ydl_opts['format'] = format_id
        else:
            ydl_opts['format'] = 'bv[ext=mp4]+ba[ext=m4a]'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=True)
                # 记录下载历史
                self._log_download(info, url)

                # 获取实际下载的文件路径
                video_title = info['title']
                video_ext = info['ext']
                # 添加文件名长度限制处理
                if len(video_title) > max_filename_length:
                    video_title = video_title[:max_filename_length]
                downloaded_file = os.path.join(self.download_dir, f"{info.get('upload_date')}_{info.get('id')}_{info.get('resolution')}_{video_title}.{video_ext}")

                return {
                    "title": video_title,
                    "file_path": downloaded_file,
                    "format": info.get('format'),
                    "format_id": info.get('format_id'),
                    "resolution": info.get('resolution'),
                    "filesize": info.get('filesize'),
                    "duration": info.get('duration'),
                    "view_count": info.get('view_count'),
                    "webpage_url": info.get('webpage_url')
                }
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    def get_resolution_list(self, url: str) -> List[str]:
        """获取视频可用的分辨率列表"""
        try:
            formats = self.get_available_formats(url)
            # 提取所有不重复的分辨率
            resolutions = list(set(f['resolution'] for f in formats if f['resolution'] != 'unknown'))
            # 按照分辨率数值排序（从高到低）
            resolutions.sort(key=lambda x: int(x.split('x')[1]) if 'x' in x else 0, reverse=True)
            return resolutions
        except Exception as e:
            raise Exception(f"获取分辨率列表失败: {str(e)}")


app = FastAPI(
    title="Media Video Dump",
    description="A service for managing media and video files",
    version="0.1.0"
)

# 定义下载目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# 挂载下载目录为静态文件服务
app.mount("/downloads", StaticFiles(directory=DOWNLOAD_DIR), name="downloads")

# 创建 MediaTransferService 实例
media_service = MediaTransferService(DOWNLOAD_DIR)


class DownloadRequest(BaseModel):
    """
    example url:
    video_url = 'https://www.youtube.com/watch?v=oJx9DpXtmAE&list=PLI5YfMzCfRtZ4bHJJDl_IJejxMwZFiBwz'
    video_url = 'https://www.tiktok.com/@hakata4k.official/video/7468249703516261650'
    video_url = 'https://cn.pornhub.com/view_video.php?viewkey=6571c740e2b69'
    video_url = 'https://www.facebook.com/watch?v=2973003642996553'
    video_url = 'https://www.instagram.com/p/DF9Z3YsMLiu/'
    """
    url: str
    format_id: Optional[str] = None
    resolution: Optional[str] = None  # 新增分辨率参数
    proxy: Optional[str] = None


class GetVideoResolutionsRequest(BaseModel):
    url: str


@app.post("/video_resolutions")
async def get_video_resolutions(request: GetVideoResolutionsRequest):
    """获取视频可用的分辨率列表"""
    try:
        formats = media_service.get_available_formats(request.url)
        return {
            "status": "success",
            "message": "Available formats retrieved successfully",
            "data": formats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/resolution_list")
async def get_video_resolution_list(request: GetVideoResolutionsRequest):
    """获取视频可用的分辨率列表"""
    try:
        resolutions = media_service.get_resolution_list(request.url)
        return {
            "status": "success",
            "message": "获取分辨率列表成功",
            "data": resolutions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def download_video(request: DownloadRequest):
    """下载指定格式或分辨率的视频"""
    try:
        result = media_service.download(
            request.url,
            format_id=request.format_id,
            resolution=request.resolution,
            max_filename_length=100,
            proxy=request.proxy
        )
        return {
            "status": "success",
            "message": "Video downloaded successfully",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def read_health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

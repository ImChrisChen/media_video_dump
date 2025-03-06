import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse
import yt_dlp
import random


class MediaTransferService:
    user_agents = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.2365.92 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        # Firefox on Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        self.log_file = os.path.join(download_dir, "download_history.jsonl")
        os.makedirs(self.download_dir, exist_ok=True)

    def _log_download(self, info: Dict[str, Any], url: str):
        print("info:", info)

        """记录下载历史"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "title": info.get("title"),
            "format": info.get("format"),
            "formats": info.get("formats"),
            "format_id": info.get("format_id"),
            "resolution": info.get("resolution"),
            "filesize": info.get("filesize"),
            "filepath": info.get("filepath"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
            "webpage_url": info.get("webpage_url"),
            "extractor": info.get("extractor"),
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def _progress_hook(self, d):
        """处理下载进度回调"""
        if d["status"] == "downloading":
            try:
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                if total > 0:
                    percent = (d["downloaded_bytes"] / total) * 100
                    print("video download percent:", f"{percent:.2f}%")
                else:
                    print("downloading... (size unknown)")
            except Exception as e:
                print(f"Progress calculation error: {str(e)}")
        elif d["status"] == "finished":
            print("Download finished, now post-processing...")

    def download(
        self,
        url: str,
        resolution: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """下载视频，可以指定分辨率和代理"""
        output_path = os.path.join(
            self.download_dir,
            "%(title).100s_%(resolution)s_%(upload_date).100s_%(id)s.%(ext)s",
        )

        ydl_opts = {
            "outtmpl": output_path,
            "noplaylist": True,
            "overwrites": True,
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [self._progress_hook],
            "http_headers": {"User-Agent": random.choice(self.user_agents)},
        }

        if proxy:
            ydl_opts["proxy"] = proxy

        if resolution:
            ydl_opts["format"] = (
                f'bv[height={resolution.split("x")[1]}][ext=mp4]+ba[ext=m4a]'
            )
        else:
            # 默认是最高分辨率
            pass

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                self._log_download(info, url)

                return {
                    "title": info.get("title"),
                    "filepath": info.get("filepath"),
                    "format": info.get("format"),
                    "format_id": info.get("format_id"),
                    "resolution": info.get("resolution"),
                    "filesize": info.get("filesize"),
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "webpage_url": info.get("webpage_url"),
                }
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")

    def get_video_list(
        self, url: str, proxy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取网址中的视频列表

        Args:
            url: 网址
            proxy: 代理地址（可选）

        Returns:
            包含视频信息的列表，每个视频信息包含标题、时长、缩略图等
        """
        try:
            ydl_opts = {
                "quiet": False,
                "no_warnings": False,
                "extract_flat": True,  # 只提取视频信息，不下载
                "http_headers": {"User-Agent": random.choice(self.user_agents)},
            }

            if proxy:
                ydl_opts["proxy"] = proxy

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # 如果是播放列表
                if info.get("_type") == "playlist":
                    videos = info.get("entries", [])
                else:
                    # 单个视频
                    videos = [info]

                domain = urlparse(url).netloc
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                os.makedirs(f"./logs/{domain}/video_list", exist_ok=True)
                file_name = f"./logs/{domain}/video_list/{date}.json"
                with open(file_name, "a", encoding="utf-8") as f:
                    f.write(json.dumps(videos, ensure_ascii=False) + "\n")

                result = []
                for video in videos:
                    video_info = {
                        "id": video.get("id"),
                        "title": video.get("title"),
                        "duration": video.get("duration"),
                        "view_count": video.get("view_count"),
                        "webpage_url": video.get("webpage_url") or video.get("url"),
                        "thumbnail": video.get("thumbnail"),
                        "description": video.get("description"),
                        "uploader": video.get("uploader"),
                        "upload_date": video.get("upload_date"),
                        "webpage_url_domain": video.get("webpage_url_domain"),
                    }
                    result.append(video_info)

                return result

        except Exception as e:
            raise Exception(f"获取视频列表失败: {str(e)}")

    def get_resolution_list(self, url: str, proxy: Optional[str] = None) -> List[str]:
        try:
            ydl_opts = {
                "quiet": False,
                "no_warnings": False,
                "http_headers": {"User-Agent": random.choice(self.user_agents)},
            }

            if proxy:
                ydl_opts["proxy"] = proxy

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = []
                for f in info["formats"]:
                    format_info = {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "resolution": f.get("resolution", None),
                        "filesize": f.get("filesize", None),
                        "fps": f.get("fps", None),
                    }

                    if f.get("ext") == "mp4" and f.get("resolution") is not None:
                        formats.append(format_info)

                resolutions = list(set(f["resolution"] for f in formats))
                resolutions.sort(
                    key=lambda x: int(x.split("x")[1]) if "x" in x else 0, reverse=True
                )
                return resolutions
        except Exception as e:
            print("e:", e)
            raise Exception(f"Get resolution list failed: {str(e)}")

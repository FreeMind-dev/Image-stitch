"""
图片拼接工具

支持静态图片和动态图片（GIF/APNG/WebP）的横向和纵向拼接。
功能特性：
- 静态 + 静态 → PNG/JPEG
- 静态 + 动态 → GIF/APNG/WebP
- 动态 + 动态 → GIF/APNG/WebP
- 支持多张图片拼接
- 保持原图宽高比
- 支持水平和垂直两种拼接方向
- 支持对齐模式（top/center/bottom/left/right）
"""

__version__ = "1.1.0"
__author__ = "Image Stitch Tool"

from .core.image_loader import ImageLoader, ImageInfo
from .core.stitcher import ImageStitcher, AlignMode, HeightMode, Direction
from .core.exporter import Exporter, OutputFormat
from .core.frame_sync import FrameSynchronizer, SyncMode

__all__ = [
    "ImageLoader",
    "ImageInfo",
    "ImageStitcher",
    "AlignMode",
    "HeightMode",
    "Direction",
    "Exporter",
    "OutputFormat",
    "FrameSynchronizer",
    "SyncMode",
]

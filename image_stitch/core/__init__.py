"""
核心模块

包含图像处理的核心功能：
- image_loader: 图像加载，支持静态和动态图片
- frame_sync: 帧同步算法，处理多个动图的帧数/时长差异
- stitcher: 横向拼接逻辑
- exporter: 多格式导出
- cropper: 图片剪裁
"""

from .image_loader import ImageLoader, ImageInfo
from .stitcher import ImageStitcher, AlignMode, HeightMode, Direction
from .exporter import Exporter, OutputFormat
from .frame_sync import FrameSynchronizer, SyncMode
from .cropper import ImageCropper, CropBox

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
    "ImageCropper",
    "CropBox",
]

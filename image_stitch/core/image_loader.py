"""
图像加载模块

支持加载静态图片（PNG/JPEG等）和动态图片（GIF/APNG/WebP）。
自动检测图片类型，提取帧信息和时长。
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from PIL import Image, ImageSequence


@dataclass
class ImageInfo:
    """
    图像信息数据类

    存储图像的完整信息，包括帧列表、时长等。

    属性:
        path: 文件路径
        is_animated: 是否为动画
        n_frames: 帧数
        width: 图片宽度
        height: 图片高度
        format: 图片格式（如 'GIF', 'PNG'）
        frames: 帧列表（PIL.Image 对象）
        durations: 每帧时长列表（毫秒）
        total_duration: 总时长（毫秒）
    """
    path: str
    is_animated: bool
    n_frames: int
    width: int
    height: int
    format: str
    frames: List[Image.Image] = field(default_factory=list)
    durations: List[int] = field(default_factory=list)
    total_duration: int = 0

    def __repr__(self) -> str:
        anim_str = f"animated, {self.n_frames} frames" if self.is_animated else "static"
        return f"ImageInfo({Path(self.path).name}, {self.width}x{self.height}, {anim_str})"


class ImageLoader:
    """
    图像加载器

    支持加载静态和动态图片，自动检测类型并提取帧信息。

    支持格式:
        - 静态: PNG, JPEG, BMP, TIFF, WebP
        - 动态: GIF, APNG, WebP (animated)

    使用示例:
        >>> loader = ImageLoader()
        >>> info = loader.load("animation.gif")
        >>> print(info.n_frames)  # 输出帧数
        >>> print(info.is_animated)  # True
    """

    # 支持的图片格式
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}

    def __init__(self, default_duration: int = 100):
        """
        初始化加载器

        参数:
            default_duration: 默认帧时长（毫秒），用于未指定时长的帧
        """
        self.default_duration = default_duration

    def load(self, path: str) -> ImageInfo:
        """
        加载图像并返回完整信息

        参数:
            path: 图片文件路径

        返回:
            ImageInfo 对象，包含图片的完整信息

        异常:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
            IOError: 无法读取图片
        """
        path = Path(path)

        # 检查文件存在
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        # 检查格式支持
        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {suffix}，支持: {self.SUPPORTED_FORMATS}")

        # 打开图片
        try:
            img = Image.open(path)
        except Exception as e:
            raise IOError(f"无法读取图片 {path}: {e}")

        # 检测是否为动画
        is_animated = getattr(img, "is_animated", False)

        if is_animated:
            return self._load_animated(str(path), img)
        else:
            return self._load_static(str(path), img)

    def _load_static(self, path: str, img: Image.Image) -> ImageInfo:
        """
        加载静态图像

        参数:
            path: 文件路径
            img: PIL Image 对象

        返回:
            ImageInfo 对象
        """
        # 转换为 RGBA 模式以支持透明度
        frame = img.convert("RGBA")

        return ImageInfo(
            path=path,
            is_animated=False,
            n_frames=1,
            width=img.width,
            height=img.height,
            format=img.format or "UNKNOWN",
            frames=[frame],
            durations=[0],  # 静态图无时长
            total_duration=0,
        )

    def _load_animated(self, path: str, img: Image.Image) -> ImageInfo:
        """
        加载动态图像，提取所有帧

        参数:
            path: 文件路径
            img: PIL Image 对象

        返回:
            ImageInfo 对象，包含所有帧和时长信息
        """
        frames: List[Image.Image] = []
        durations: List[int] = []

        # 遍历所有帧
        for frame in ImageSequence.Iterator(img):
            # 获取帧时长，默认为 default_duration
            duration = frame.info.get("duration", self.default_duration)
            # 某些 GIF 的 duration 为 0，使用默认值
            if duration == 0:
                duration = self.default_duration

            # 转换为 RGBA 并复制（避免引用问题）
            frames.append(frame.convert("RGBA").copy())
            durations.append(duration)

        return ImageInfo(
            path=path,
            is_animated=True,
            n_frames=len(frames),
            width=img.width,
            height=img.height,
            format=img.format or "UNKNOWN",
            frames=frames,
            durations=durations,
            total_duration=sum(durations),
        )

    def load_multiple(self, paths: List[str]) -> List[ImageInfo]:
        """
        批量加载多个图像

        参数:
            paths: 图片路径列表

        返回:
            ImageInfo 对象列表
        """
        return [self.load(path) for path in paths]

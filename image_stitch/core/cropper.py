"""
图片剪裁模块

支持对静态和动态图片进行剪裁：
- 静态图片：直接裁剪指定区域
- 动态图片（GIF）：逐帧裁剪，保持时长信息
"""

from dataclasses import dataclass
from typing import Tuple, List, Optional
from PIL import Image

from .image_loader import ImageInfo


@dataclass
class CropBox:
    """
    剪裁区域

    属性:
        x1, y1: 左上角坐标
        x2, y2: 右下角坐标
    """
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        """剪裁区域宽度"""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """剪裁区域高度"""
        return self.y2 - self.y1

    @property
    def as_tuple(self) -> Tuple[int, int, int, int]:
        """转换为 (x1, y1, x2, y2) 元组"""
        return (self.x1, self.y1, self.x2, self.y2)

    def validate(self, img_width: int, img_height: int) -> bool:
        """
        验证剪裁区域是否有效

        参数:
            img_width: 图片宽度
            img_height: 图片高度

        返回:
            是否有效
        """
        return (
            0 <= self.x1 < self.x2 <= img_width
            and 0 <= self.y1 < self.y2 <= img_height
            and self.width > 0
            and self.height > 0
        )

    def clamp(self, img_width: int, img_height: int) -> "CropBox":
        """
        将剪裁区域限制在图片范围内

        参数:
            img_width: 图片宽度
            img_height: 图片高度

        返回:
            调整后的 CropBox
        """
        return CropBox(
            x1=max(0, min(self.x1, img_width - 1)),
            y1=max(0, min(self.y1, img_height - 1)),
            x2=max(1, min(self.x2, img_width)),
            y2=max(1, min(self.y2, img_height)),
        )


class ImageCropper:
    """
    图片剪裁器

    支持静态和动态图片的剪裁操作。

    使用示例:
        >>> cropper = ImageCropper()
        >>> box = CropBox(10, 10, 200, 150)
        >>> cropped_info = cropper.crop(image_info, box)
    """

    def crop(self, info: ImageInfo, box: CropBox) -> ImageInfo:
        """
        剪裁图片

        参数:
            info: 原始 ImageInfo 对象
            box: 剪裁区域

        返回:
            剪裁后的 ImageInfo 对象
        """
        # 验证并调整剪裁区域
        box = box.clamp(info.width, info.height)
        if not box.validate(info.width, info.height):
            raise ValueError(f"无效的剪裁区域: {box.as_tuple}")

        if info.is_animated:
            return self._crop_animated(info, box)
        else:
            return self._crop_static(info, box)

    def _crop_static(self, info: ImageInfo, box: CropBox) -> ImageInfo:
        """
        剪裁静态图片

        参数:
            info: 原始 ImageInfo 对象
            box: 剪裁区域

        返回:
            剪裁后的 ImageInfo 对象
        """
        # 剪裁第一帧
        frame = info.frames[0]
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")
        cropped_frame = frame.crop(box.as_tuple)

        return ImageInfo(
            path=info.path,
            is_animated=False,
            n_frames=1,
            width=box.width,
            height=box.height,
            format=info.format,
            frames=[cropped_frame],
            durations=[0],
            total_duration=0,
        )

    def _crop_animated(self, info: ImageInfo, box: CropBox) -> ImageInfo:
        """
        剪裁动态图片（逐帧剪裁）

        参数:
            info: 原始 ImageInfo 对象
            box: 剪裁区域

        返回:
            剪裁后的 ImageInfo 对象
        """
        # 逐帧剪裁
        cropped_frames = []
        for frame in info.frames:
            # 确保帧是 RGBA 模式
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            cropped_frame = frame.crop(box.as_tuple)
            cropped_frames.append(cropped_frame)

        return ImageInfo(
            path=info.path,
            is_animated=True,
            n_frames=info.n_frames,
            width=box.width,
            height=box.height,
            format=info.format,
            frames=cropped_frames,
            durations=info.durations.copy(),
            total_duration=info.total_duration,
        )

    def crop_preview(self, info: ImageInfo, box: CropBox) -> Image.Image:
        """
        获取剪裁预览（仅第一帧）

        参数:
            info: 原始 ImageInfo 对象
            box: 剪裁区域

        返回:
            预览图片（PIL Image）
        """
        box = box.clamp(info.width, info.height)
        frame = info.frames[0]
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")
        return frame.crop(box.as_tuple)

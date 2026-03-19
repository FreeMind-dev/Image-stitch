"""
图像拼接模块

提供横向和纵向图像拼接功能，支持：
- 多张静态图片拼接
- 多张动态图片拼接
- 静态与动态混合拼接
- 水平（HORIZONTAL）和垂直（VERTICAL）两种拼接方向
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
from PIL import Image

from .image_loader import ImageInfo
from .frame_sync import FrameSynchronizer, SyncResult, SyncMode


class AlignMode(Enum):
    """
    对齐模式

    水平拼接时：TOP/CENTER/BOTTOM 控制垂直对齐
    垂直拼接时：LEFT/CENTER/RIGHT 控制水平对齐
    """
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class HeightMode(Enum):
    """
    尺寸匹配模式

    水平拼接：控制目标高度（MAX=最高, MIN=最矮）
    垂直拼接：控制目标宽度（MAX=最宽, MIN=最窄）

    MAX: 以最大尺寸为基准，其他图片等比例放大（默认）
    MIN: 以最小尺寸为基准，其他图片等比例缩小
    CUSTOM: 使用自定义尺寸
    """
    MAX = "max"
    MIN = "min"
    CUSTOM = "custom"


class Direction(Enum):
    """
    拼接方向

    HORIZONTAL: 水平拼接（左→右，默认）
    VERTICAL: 垂直拼接（上→下）
    """
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class StitchResult:
    """
    拼接结果

    属性:
        frames: 拼接后的帧列表
        durations: 每帧时长列表（毫秒）
        is_animated: 是否为动画
        width: 输出宽度
        height: 输出高度
    """
    frames: List[Image.Image]
    durations: List[int]
    is_animated: bool
    width: int
    height: int


class ImageStitcher:
    """
    图像拼接器

    将多张图片横向或纵向拼接，支持静态和动态图片。
    默认会等比例缩放所有图片，使尺寸对齐。

    使用示例:
        >>> stitcher = ImageStitcher(spacing=10)
        >>> result = stitcher.stitch([info1, info2, info3])
        >>> result.frames[0].save("output.png")

        >>> # 垂直拼接
        >>> stitcher = ImageStitcher(direction=Direction.VERTICAL)
        >>> result = stitcher.stitch([info1, info2])
    """

    def __init__(
        self,
        align: AlignMode = AlignMode.CENTER,
        spacing: int = 0,
        bg_color: Tuple[int, int, int, int] = (255, 255, 255, 0),
        sync_mode: SyncMode = SyncMode.TIME_SYNC,
        max_frames: int = 300,
        height_mode: HeightMode = HeightMode.MAX,
        target_height: Optional[int] = None,
        direction: Direction = Direction.HORIZONTAL,
    ):
        """
        初始化拼接器

        参数:
            align: 对齐方式（水平拼接时控制垂直对齐，垂直拼接时控制水平对齐）
            spacing: 图片之间的间距（像素）
            bg_color: 背景颜色 (R, G, B, A)，默认透明白色
            sync_mode: 帧同步模式
            max_frames: 最大帧数限制
            height_mode: 尺寸匹配模式（MAX=以最大为准，MIN=以最小为准）
            target_height: 自定义目标尺寸（仅当 height_mode=CUSTOM 时使用）
            direction: 拼接方向（HORIZONTAL=水平, VERTICAL=垂直）
        """
        if spacing < 0:
            raise ValueError("spacing 不能为负数")

        self.align = align
        self.spacing = spacing
        self.bg_color = bg_color
        self.synchronizer = FrameSynchronizer(mode=sync_mode, max_frames=max_frames)
        self.height_mode = height_mode
        self.target_height = target_height
        self.direction = direction

    def stitch(self, images: List[ImageInfo]) -> StitchResult:
        """
        拼接多张图片

        参数:
            images: ImageInfo 对象列表

        返回:
            StitchResult 对象，包含拼接后的帧和时长信息
        """
        if not images:
            raise ValueError("至少需要一张图片")

        if len(images) == 1:
            # 单张图片，直接返回
            return StitchResult(
                frames=images[0].frames.copy(),
                durations=images[0].durations.copy(),
                is_animated=images[0].is_animated,
                width=images[0].width,
                height=images[0].height,
            )

        # 检查是否包含动画
        has_animation = any(info.is_animated for info in images)

        if has_animation:
            return self._stitch_animated(images)
        else:
            return self._stitch_static(images)

    def _stitch_static(self, images: List[ImageInfo]) -> StitchResult:
        """
        拼接静态图片

        参数:
            images: ImageInfo 对象列表

        返回:
            StitchResult 对象
        """
        # 获取各图片的第一帧
        frames = [info.frames[0] for info in images]

        # 拼接
        stitched = self._stitch_frames(frames)

        return StitchResult(
            frames=[stitched],
            durations=[0],
            is_animated=False,
            width=stitched.width,
            height=stitched.height,
        )

    def _stitch_animated(self, images: List[ImageInfo]) -> StitchResult:
        """
        拼接包含动画的图片

        参数:
            images: ImageInfo 对象列表

        返回:
            StitchResult 对象
        """
        # 同步帧序列
        sync_result = self.synchronizer.sync(images)

        # 预先计算目标尺寸（确保所有帧缩放比例一致）
        if self.direction == Direction.VERTICAL:
            original_sizes = [info.width for info in images]
            target_size = self._calculate_target_width(original_sizes)
        else:
            original_sizes = [info.height for info in images]
            target_size = self._calculate_target_height(original_sizes)

        # 逐帧拼接
        stitched_frames = []
        for indices in sync_result.frame_indices:
            # 获取各图片对应帧
            frames = [
                images[i].frames[idx]
                for i, idx in enumerate(indices)
            ]
            # 拼接（传入原始尺寸和目标尺寸，确保缩放一致）
            stitched = self._stitch_frames(frames, original_sizes, target_size)
            stitched_frames.append(stitched)

        return StitchResult(
            frames=stitched_frames,
            durations=sync_result.durations,
            is_animated=True,
            width=stitched_frames[0].width,
            height=stitched_frames[0].height,
        )

    # ==================== 尺寸计算 ====================

    def _calculate_target_height(self, heights: List[int]) -> int:
        """
        计算目标高度（水平拼接时使用）

        参数:
            heights: 各图片的高度列表

        返回:
            目标高度（像素）
        """
        if self.height_mode == HeightMode.MAX:
            return max(heights)
        elif self.height_mode == HeightMode.MIN:
            return min(heights)
        elif self.height_mode == HeightMode.CUSTOM and self.target_height:
            return self.target_height
        else:
            return max(heights)

    def _calculate_target_width(self, widths: List[int]) -> int:
        """
        计算目标宽度（垂直拼接时使用）

        参数:
            widths: 各图片的宽度列表

        返回:
            目标宽度（像素）
        """
        if self.height_mode == HeightMode.MAX:
            return max(widths)
        elif self.height_mode == HeightMode.MIN:
            return min(widths)
        elif self.height_mode == HeightMode.CUSTOM and self.target_height:
            return self.target_height
        else:
            return max(widths)

    # ==================== 帧缩放 ====================

    def _scale_to_height(
        self, frame: Image.Image, original_height: int, target_height: int
    ) -> Image.Image:
        """
        等比例缩放到目标高度

        参数:
            frame: PIL Image 对象
            original_height: 原始高度
            target_height: 目标高度

        返回:
            缩放后的 PIL Image 对象
        """
        if original_height == target_height:
            return frame

        scale = target_height / original_height
        new_width = int(frame.width * scale)

        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")

        return frame.resize((new_width, target_height), Image.Resampling.LANCZOS)

    def _scale_to_width(
        self, frame: Image.Image, original_width: int, target_width: int
    ) -> Image.Image:
        """
        等比例缩放到目标宽度

        参数:
            frame: PIL Image 对象
            original_width: 原始宽度
            target_width: 目标宽度

        返回:
            缩放后的 PIL Image 对象
        """
        if original_width == target_width:
            return frame

        scale = target_width / original_width
        new_height = int(frame.height * scale)

        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")

        return frame.resize((target_width, new_height), Image.Resampling.LANCZOS)

    # ==================== 帧拼接（方向分派） ====================

    def _stitch_frames(
        self,
        frames: List[Image.Image],
        original_sizes: Optional[List[int]] = None,
        target_size: Optional[int] = None,
    ) -> Image.Image:
        """
        拼接单帧图片列表，根据方向自动分派

        参数:
            frames: PIL Image 对象列表
            original_sizes: 原始尺寸列表（水平=高度, 垂直=宽度）
            target_size: 目标尺寸

        返回:
            拼接后的 PIL Image 对象
        """
        if not frames:
            raise ValueError("帧列表不能为空")

        if self.direction == Direction.VERTICAL:
            return self._stitch_vertical(frames, original_sizes, target_size)
        return self._stitch_horizontal(frames, original_sizes, target_size)

    def _stitch_horizontal(
        self,
        frames: List[Image.Image],
        original_heights: Optional[List[int]] = None,
        target_height: Optional[int] = None,
    ) -> Image.Image:
        """
        水平拼接（左→右），等比例缩放使高度一致

        参数:
            frames: PIL Image 对象列表
            original_heights: 原始高度列表（动画时传入以保持缩放一致）
            target_height: 目标高度

        返回:
            拼接后的 PIL Image 对象
        """
        # 确定目标高度
        if target_height is None:
            heights = [frame.height for frame in frames]
            target_height = self._calculate_target_height(heights)

        if original_heights is None:
            original_heights = [frame.height for frame in frames]

        # 缩放所有帧到目标高度
        scaled_frames = [
            self._scale_to_height(frame, original_heights[i], target_height)
            for i, frame in enumerate(frames)
        ]

        # 计算输出尺寸
        total_width = (
            sum(f.width for f in scaled_frames)
            + self.spacing * (len(scaled_frames) - 1)
        )

        # 创建画布
        canvas = Image.new("RGBA", (total_width, target_height), self.bg_color)

        # 逐个粘贴图片
        x_offset = 0
        for frame in scaled_frames:
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            canvas.paste(frame, (x_offset, 0), frame)
            x_offset += frame.width + self.spacing

        return canvas

    def _stitch_vertical(
        self,
        frames: List[Image.Image],
        original_widths: Optional[List[int]] = None,
        target_width: Optional[int] = None,
    ) -> Image.Image:
        """
        垂直拼接（上→下），等比例缩放使宽度一致

        参数:
            frames: PIL Image 对象列表
            original_widths: 原始宽度列表（动画时传入以保持缩放一致）
            target_width: 目标宽度

        返回:
            拼接后的 PIL Image 对象
        """
        # 确定目标宽度
        if target_width is None:
            widths = [frame.width for frame in frames]
            target_width = self._calculate_target_width(widths)

        if original_widths is None:
            original_widths = [frame.width for frame in frames]

        # 缩放所有帧到目标宽度
        scaled_frames = [
            self._scale_to_width(frame, original_widths[i], target_width)
            for i, frame in enumerate(frames)
        ]

        # 计算输出尺寸
        total_height = (
            sum(f.height for f in scaled_frames)
            + self.spacing * (len(scaled_frames) - 1)
        )

        # 创建画布
        canvas = Image.new("RGBA", (target_width, total_height), self.bg_color)

        # 逐个粘贴图片（上→下）
        y_offset = 0
        for frame in scaled_frames:
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")

            # 水平对齐计算
            if self.align in (AlignMode.LEFT, AlignMode.TOP):
                x = 0
            elif self.align in (AlignMode.RIGHT, AlignMode.BOTTOM):
                x = target_width - frame.width
            else:  # CENTER
                x = (target_width - frame.width) // 2

            canvas.paste(frame, (x, y_offset), frame)
            y_offset += frame.height + self.spacing

        return canvas

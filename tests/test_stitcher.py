"""
图像拼接模块单元测试

测试 ImageStitcher 在水平/垂直方向、静态/动态场景下的拼接行为：
- 水平静态拼接
- 垂直静态拼接
- 动画拼接
- 间距参数
- HeightMode.MAX / MIN
- 单图返回原图
- 空列表异常
"""

import pytest
from PIL import Image

from image_stitch.core.stitcher import (
    ImageStitcher, StitchResult, AlignMode, HeightMode, Direction,
)
from image_stitch.core.frame_sync import SyncMode
from image_stitch.core.image_loader import ImageInfo


# ==================== 水平静态拼接测试 ====================

class TestHorizontalStatic:
    """水平方向静态图片拼接测试"""

    def test_basic_stitch(self, red_info, green_info, blue_info):
        """三张静态图水平拼接，产生单帧结果"""
        stitcher = ImageStitcher()
        result = stitcher.stitch([red_info, green_info, blue_info])

        assert isinstance(result, StitchResult)
        assert result.is_animated is False
        assert len(result.frames) == 1
        assert result.frames[0].mode == "RGBA"

    def test_height_mode_max(self, red_info, green_info, blue_info):
        """HeightMode.MAX: 输出高度等于最高图片的高度"""
        stitcher = ImageStitcher(height_mode=HeightMode.MAX)
        result = stitcher.stitch([red_info, green_info, blue_info])

        # 三张图的高度: 80, 100, 120 -> max = 120
        assert result.height == 120

    def test_height_mode_min(self, red_info, green_info, blue_info):
        """HeightMode.MIN: 输出高度等于最矮图片的高度"""
        stitcher = ImageStitcher(height_mode=HeightMode.MIN)
        result = stitcher.stitch([red_info, green_info, blue_info])

        # 三张图的高度: 80, 100, 120 -> min = 80
        assert result.height == 80

    def test_width_is_sum(self, red_info, green_info):
        """水平拼接宽度等于各图等比缩放后宽度之和"""
        stitcher = ImageStitcher(spacing=0, height_mode=HeightMode.MAX)
        result = stitcher.stitch([red_info, green_info])

        # 目标高度 = max(80, 100) = 100
        # red: 100x80 -> 缩放到高 100 -> 宽 125
        # green: 80x100 -> 不缩放 -> 宽 80
        assert result.width == 125 + 80
        assert result.height == 100

    def test_spacing(self, red_info, green_info):
        """间距参数增加拼接宽度"""
        spacing = 20
        stitcher_no_space = ImageStitcher(spacing=0, height_mode=HeightMode.MAX)
        stitcher_with_space = ImageStitcher(spacing=spacing, height_mode=HeightMode.MAX)

        result_no = stitcher_no_space.stitch([red_info, green_info])
        result_yes = stitcher_with_space.stitch([red_info, green_info])

        # 两张图之间有 1 个间距
        assert result_yes.width == result_no.width + spacing

    def test_spacing_three_images(self, red_info, green_info, blue_info):
        """三张图之间有 2 个间距"""
        spacing = 10
        stitcher_no_space = ImageStitcher(spacing=0, height_mode=HeightMode.MAX)
        stitcher_with_space = ImageStitcher(spacing=spacing, height_mode=HeightMode.MAX)

        result_no = stitcher_no_space.stitch([red_info, green_info, blue_info])
        result_yes = stitcher_with_space.stitch([red_info, green_info, blue_info])

        assert result_yes.width == result_no.width + spacing * 2


# ==================== 垂直静态拼接测试 ====================

class TestVerticalStatic:
    """垂直方向静态图片拼接测试"""

    def test_basic_vertical(self, red_info, green_info, blue_info):
        """三张静态图垂直拼接，产生单帧结果"""
        stitcher = ImageStitcher(direction=Direction.VERTICAL)
        result = stitcher.stitch([red_info, green_info, blue_info])

        assert result.is_animated is False
        assert len(result.frames) == 1

    def test_vertical_width_mode_max(self, red_info, green_info, blue_info):
        """垂直拼接 HeightMode.MAX: 输出宽度等于最宽图片宽度"""
        stitcher = ImageStitcher(
            direction=Direction.VERTICAL,
            height_mode=HeightMode.MAX,
        )
        result = stitcher.stitch([red_info, green_info, blue_info])

        # 三张图宽度: 100, 80, 100 -> max = 100
        assert result.width == 100

    def test_vertical_width_mode_min(self, red_info, green_info, blue_info):
        """垂直拼接 HeightMode.MIN: 输出宽度等于最窄图片宽度"""
        stitcher = ImageStitcher(
            direction=Direction.VERTICAL,
            height_mode=HeightMode.MIN,
        )
        result = stitcher.stitch([red_info, green_info, blue_info])

        # 三张图宽度: 100, 80, 100 -> min = 80
        assert result.width == 80

    def test_vertical_spacing(self, red_info, green_info):
        """垂直拼接间距参数增加高度"""
        spacing = 15
        stitcher_no = ImageStitcher(direction=Direction.VERTICAL, spacing=0)
        stitcher_yes = ImageStitcher(direction=Direction.VERTICAL, spacing=spacing)

        result_no = stitcher_no.stitch([red_info, green_info])
        result_yes = stitcher_yes.stitch([red_info, green_info])

        assert result_yes.height == result_no.height + spacing

    def test_vertical_height_is_sum(self, red_info, green_info):
        """垂直拼接高度等于各图等比缩放后高度之和"""
        stitcher = ImageStitcher(
            direction=Direction.VERTICAL,
            spacing=0,
            height_mode=HeightMode.MAX,
        )
        result = stitcher.stitch([red_info, green_info])

        # 目标宽度 = max(100, 80) = 100
        # red: 100x80 -> 不缩放 -> 高 80
        # green: 80x100 -> 缩放到宽 100 -> 高 125
        assert result.height == 80 + 125
        assert result.width == 100


# ==================== 动画拼接测试 ====================

class TestAnimatedStitch:
    """动画图片拼接测试"""

    def test_animated_stitch(self, anim1_info, anim2_info):
        """两个动画拼接产生动画结果"""
        stitcher = ImageStitcher(sync_mode=SyncMode.LOOP)
        result = stitcher.stitch([anim1_info, anim2_info])

        assert result.is_animated is True
        assert len(result.frames) >= 1
        assert len(result.durations) == len(result.frames)

    def test_animated_frame_dimensions(self, anim1_info, anim2_info):
        """动画拼接所有帧尺寸一致"""
        stitcher = ImageStitcher(sync_mode=SyncMode.LOOP)
        result = stitcher.stitch([anim1_info, anim2_info])

        for frame in result.frames:
            assert frame.width == result.width
            assert frame.height == result.height

    def test_mixed_static_animated(self, red_info, anim1_info):
        """静态与动态混合拼接产生动画"""
        stitcher = ImageStitcher(sync_mode=SyncMode.LOOP)
        result = stitcher.stitch([red_info, anim1_info])

        assert result.is_animated is True
        assert len(result.frames) >= 1

    def test_animated_vertical(self, anim1_info, anim2_info):
        """垂直方向动画拼接"""
        stitcher = ImageStitcher(
            direction=Direction.VERTICAL,
            sync_mode=SyncMode.LOOP,
        )
        result = stitcher.stitch([anim1_info, anim2_info])

        assert result.is_animated is True
        assert len(result.frames) >= 1


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """边界情况测试"""

    def test_single_image_returns_unchanged(self, red_info):
        """单张图片直接返回，不做拼接"""
        stitcher = ImageStitcher()
        result = stitcher.stitch([red_info])

        assert result.width == red_info.width
        assert result.height == red_info.height
        assert result.is_animated == red_info.is_animated
        assert len(result.frames) == len(red_info.frames)

    def test_single_animated_returns_unchanged(self, anim1_info):
        """单张动画直接返回"""
        stitcher = ImageStitcher()
        result = stitcher.stitch([anim1_info])

        assert result.width == anim1_info.width
        assert result.height == anim1_info.height
        assert result.is_animated is True
        assert result.durations == anim1_info.durations

    def test_empty_list_raises(self):
        """空列表抛出 ValueError"""
        stitcher = ImageStitcher()
        with pytest.raises(ValueError, match="至少需要一张图片"):
            stitcher.stitch([])

    def test_same_image_twice(self, red_info):
        """同一张图片拼接两次"""
        stitcher = ImageStitcher(spacing=0, height_mode=HeightMode.MAX)
        result = stitcher.stitch([red_info, red_info])

        # 两张相同图片水平拼接，宽度翻倍
        assert result.width == red_info.width * 2
        assert result.height == red_info.height

    def test_negative_spacing_raises(self):
        """负间距应被直接拒绝"""
        with pytest.raises(ValueError, match="spacing"):
            ImageStitcher(spacing=-1)

    def test_short_duration_animation_does_not_crash(self):
        """超短动画在 TIME_SYNC 下仍可完成拼接"""
        frame = Image.new("RGBA", (12, 12), (255, 0, 0, 255))
        short_info = ImageInfo(
            path="short.webp",
            is_animated=True,
            n_frames=1,
            width=12,
            height=12,
            format="WEBP",
            frames=[frame],
            durations=[10],
            total_duration=10,
        )

        result = ImageStitcher().stitch([short_info, short_info])

        assert result.is_animated is True
        assert len(result.frames) == 1
        assert result.durations == [20]


# ==================== StitchResult 数据结构测试 ====================

class TestStitchResultConsistency:
    """StitchResult 输出一致性验证"""

    def test_static_result_structure(self, red_info, green_info):
        """静态结果的结构一致性"""
        stitcher = ImageStitcher()
        result = stitcher.stitch([red_info, green_info])

        assert len(result.frames) == 1
        assert len(result.durations) == 1
        assert result.durations[0] == 0

    def test_animated_result_structure(self, anim1_info, anim2_info):
        """动画结果的结构一致性"""
        stitcher = ImageStitcher(sync_mode=SyncMode.LOOP)
        result = stitcher.stitch([anim1_info, anim2_info])

        assert len(result.frames) == len(result.durations)
        assert all(isinstance(f, Image.Image) for f in result.frames)
        assert all(isinstance(d, int) for d in result.durations)

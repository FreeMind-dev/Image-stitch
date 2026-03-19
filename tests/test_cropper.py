"""
图片剪裁模块单元测试

测试 ImageCropper 和 CropBox 的核心功能：
- 静态图片剪裁
- 动态图片逐帧剪裁
- CropBox 验证与钳位
- 无效剪裁区域异常处理
"""

import pytest
from PIL import Image

from image_stitch.core.cropper import ImageCropper, CropBox
from image_stitch.core.image_loader import ImageInfo


# ==================== CropBox 属性测试 ====================

class TestCropBoxProperties:
    """CropBox 数据类属性测试"""

    def test_width_height(self):
        """宽度和高度计算正确"""
        box = CropBox(10, 20, 110, 80)
        assert box.width == 100
        assert box.height == 60

    def test_as_tuple(self):
        """as_tuple 属性返回正确元组"""
        box = CropBox(5, 10, 50, 40)
        assert box.as_tuple == (5, 10, 50, 40)


# ==================== CropBox 验证测试 ====================

class TestCropBoxValidation:
    """CropBox validate 方法测试"""

    def test_valid_box(self):
        """有效剪裁区域通过验证"""
        box = CropBox(0, 0, 50, 50)
        assert box.validate(100, 100) is True

    def test_valid_full_image(self):
        """覆盖整张图片的剪裁区域有效"""
        box = CropBox(0, 0, 100, 80)
        assert box.validate(100, 80) is True

    def test_invalid_x1_ge_x2(self):
        """x1 >= x2 无效"""
        box = CropBox(50, 0, 50, 50)
        assert box.validate(100, 100) is False

        box2 = CropBox(60, 0, 50, 50)
        assert box2.validate(100, 100) is False

    def test_invalid_y1_ge_y2(self):
        """y1 >= y2 无效"""
        box = CropBox(0, 50, 50, 50)
        assert box.validate(100, 100) is False

    def test_invalid_exceeds_width(self):
        """超出图片宽度无效"""
        box = CropBox(0, 0, 150, 50)
        assert box.validate(100, 100) is False

    def test_invalid_exceeds_height(self):
        """超出图片高度无效"""
        box = CropBox(0, 0, 50, 150)
        assert box.validate(100, 100) is False

    def test_invalid_negative_x1(self):
        """负数坐标无效"""
        box = CropBox(-10, 0, 50, 50)
        assert box.validate(100, 100) is False

    def test_invalid_negative_y1(self):
        """负数 y1 无效"""
        box = CropBox(0, -10, 50, 50)
        assert box.validate(100, 100) is False


# ==================== CropBox 钳位测试 ====================

class TestCropBoxClamp:
    """CropBox clamp 方法测试"""

    def test_clamp_within_bounds(self):
        """已在范围内的不做变动"""
        box = CropBox(10, 10, 50, 50)
        clamped = box.clamp(100, 100)
        assert clamped.as_tuple == (10, 10, 50, 50)

    def test_clamp_negative_coordinates(self):
        """负坐标钳位到 0"""
        box = CropBox(-10, -20, 50, 50)
        clamped = box.clamp(100, 100)
        assert clamped.x1 == 0
        assert clamped.y1 == 0

    def test_clamp_exceeding_width(self):
        """超出宽度的坐标钳位到图片边界"""
        box = CropBox(10, 10, 200, 50)
        clamped = box.clamp(100, 100)
        assert clamped.x2 == 100

    def test_clamp_exceeding_height(self):
        """超出高度的坐标钳位到图片边界"""
        box = CropBox(10, 10, 50, 200)
        clamped = box.clamp(100, 100)
        assert clamped.y2 == 100

    def test_clamp_all_out_of_bounds(self):
        """全部坐标超出范围"""
        box = CropBox(-50, -50, 500, 500)
        clamped = box.clamp(100, 100)
        assert clamped.x1 == 0
        assert clamped.y1 == 0
        assert clamped.x2 == 100
        assert clamped.y2 == 100


# ==================== 静态图片剪裁测试 ====================

class TestCropStatic:
    """静态图片剪裁测试"""

    def test_crop_basic(self, red_info):
        """基本静态图剪裁"""
        cropper = ImageCropper()
        box = CropBox(10, 10, 50, 40)
        result = cropper.crop(red_info, box)

        assert isinstance(result, ImageInfo)
        assert result.is_animated is False
        assert result.n_frames == 1
        assert result.width == 40  # 50 - 10
        assert result.height == 30  # 40 - 10

    def test_crop_full_image(self, red_info):
        """剪裁整张图片返回原始尺寸"""
        cropper = ImageCropper()
        box = CropBox(0, 0, red_info.width, red_info.height)
        result = cropper.crop(red_info, box)

        assert result.width == red_info.width
        assert result.height == red_info.height

    def test_crop_preserves_path(self, red_info):
        """剪裁后保持原始路径"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(red_info, box)

        assert result.path == red_info.path

    def test_crop_preserves_format(self, red_info):
        """剪裁后保持原始格式"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(red_info, box)

        assert result.format == red_info.format

    def test_crop_frame_mode(self, red_info):
        """剪裁后帧为 RGBA 模式"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(red_info, box)

        assert result.frames[0].mode == "RGBA"

    def test_crop_static_duration_zero(self, red_info):
        """剪裁后静态图时长为 0"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(red_info, box)

        assert result.durations == [0]
        assert result.total_duration == 0


# ==================== 动态图片剪裁测试 ====================

class TestCropAnimated:
    """动态图片逐帧剪裁测试"""

    def test_crop_animated_basic(self, anim1_info):
        """基本动画剪裁"""
        cropper = ImageCropper()
        box = CropBox(10, 10, 60, 60)
        result = cropper.crop(anim1_info, box)

        assert result.is_animated is True
        assert result.n_frames == anim1_info.n_frames
        assert result.width == 50  # 60 - 10
        assert result.height == 50  # 60 - 10

    def test_crop_animated_preserves_frames(self, anim1_info):
        """剪裁后帧数不变"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(anim1_info, box)

        assert len(result.frames) == anim1_info.n_frames

    def test_crop_animated_preserves_durations(self, anim1_info):
        """剪裁后保持原始帧时长"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(anim1_info, box)

        assert result.durations == anim1_info.durations
        assert result.total_duration == anim1_info.total_duration

    def test_crop_animated_all_frames_correct_size(self, anim1_info):
        """动画剪裁后所有帧尺寸一致"""
        cropper = ImageCropper()
        box = CropBox(5, 5, 55, 55)
        result = cropper.crop(anim1_info, box)

        for frame in result.frames:
            assert frame.width == 50
            assert frame.height == 50

    def test_crop_animated_frame_mode(self, anim1_info):
        """动画剪裁后所有帧为 RGBA"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        result = cropper.crop(anim1_info, box)

        for frame in result.frames:
            assert frame.mode == "RGBA"


# ==================== 无效剪裁区域测试 ====================

class TestCropInvalid:
    """无效剪裁区域异常处理测试"""

    def test_zero_area_after_clamp(self, red_info):
        """钳位后面积为零的剪裁区域抛出 ValueError

        注意: CropBox 先 clamp 再 validate。
        如果钳位后 x1 >= x2 或 y1 >= y2，则 validate 失败。
        """
        cropper = ImageCropper()
        # 完全在图片外部的裁剪框，钳位后 x1=99, x2=100, y1=99, y2=100
        # 这是有效的（1x1 区域），所以我们构造一个真正无效的
        # x1=100 会被 clamp 为 min(100, 99)=99, x2=101 被 clamp 为 100
        # y1=100 被 clamp 为 min(100, 79)=79, y2=101 被 clamp 为 80
        # 这仍然有效 (99, 79, 100, 80)，是 1x1 区域
        # 要触发 ValueError，需要 clamp 后 x1 >= x2
        # CropBox clamp: x1 = max(0, min(self.x1, img_width - 1))
        #                x2 = max(1, min(self.x2, img_width))
        # 如果 x1 = 200, x2 = -5: clamp -> x1=99, x2=1 -> x1 >= x2 -> 无效!
        box = CropBox(200, 200, -5, -5)
        with pytest.raises(ValueError):
            cropper.crop(red_info, box)


# ==================== crop_preview 测试 ====================

class TestCropPreview:
    """crop_preview 预览功能测试"""

    def test_preview_returns_image(self, red_info):
        """预览返回 PIL Image 对象"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 40)
        preview = cropper.crop_preview(red_info, box)

        assert isinstance(preview, Image.Image)
        assert preview.width == 50
        assert preview.height == 40

    def test_preview_animated_first_frame(self, anim1_info):
        """动画预览只使用第一帧"""
        cropper = ImageCropper()
        box = CropBox(0, 0, 50, 50)
        preview = cropper.crop_preview(anim1_info, box)

        assert isinstance(preview, Image.Image)
        assert preview.width == 50
        assert preview.height == 50

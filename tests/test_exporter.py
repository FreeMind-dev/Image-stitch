"""
导出模块单元测试

测试 Exporter 对不同格式（PNG, JPEG, GIF, APNG, WebP）的导出行为：
- 静态图片导出
- 动画导出
- 自动格式检测
- export_image_info 方法
"""

import pytest
from pathlib import Path
from PIL import Image

from image_stitch.core.exporter import Exporter, OutputFormat
from image_stitch.core.stitcher import StitchResult, ImageStitcher
from image_stitch.core.frame_sync import SyncMode


# ==================== 辅助 Fixture ====================

@pytest.fixture
def static_result(red_info, green_info):
    """生成静态拼接结果"""
    stitcher = ImageStitcher()
    return stitcher.stitch([red_info, green_info])


@pytest.fixture
def animated_result(anim1_info, anim2_info):
    """生成动画拼接结果"""
    stitcher = ImageStitcher(sync_mode=SyncMode.LOOP)
    return stitcher.stitch([anim1_info, anim2_info])


# ==================== 静态 PNG 导出测试 ====================

class TestExportStaticPng:
    """静态 PNG 导出测试"""

    def test_export_png(self, static_result, tmp_path):
        """导出静态 PNG 文件"""
        exporter = Exporter(format=OutputFormat.PNG)
        output = exporter.export(static_result, str(tmp_path / "out.png"))

        assert Path(output).exists()
        assert Path(output).suffix == ".png"

    def test_export_png_valid_image(self, static_result, tmp_path):
        """导出的 PNG 可被 PIL 正确打开"""
        exporter = Exporter(format=OutputFormat.PNG)
        output = exporter.export(static_result, str(tmp_path / "out.png"))

        img = Image.open(output)
        assert img.width == static_result.width
        assert img.height == static_result.height


# ==================== 静态 JPEG 导出测试 ====================

class TestExportStaticJpeg:
    """静态 JPEG 导出测试"""

    def test_export_jpeg(self, static_result, tmp_path):
        """导出 JPEG 文件"""
        exporter = Exporter(format=OutputFormat.JPEG)
        output = exporter.export(static_result, str(tmp_path / "out.jpg"))

        assert Path(output).exists()
        assert Path(output).suffix == ".jpg"

    def test_export_jpeg_valid_image(self, static_result, tmp_path):
        """导出的 JPEG 可被 PIL 正确打开且为 RGB 模式"""
        exporter = Exporter(format=OutputFormat.JPEG)
        output = exporter.export(static_result, str(tmp_path / "out.jpg"))

        img = Image.open(output)
        assert img.mode == "RGB"  # JPEG 不支持透明通道

    def test_export_jpeg_quality(self, static_result, tmp_path):
        """不同质量参数生成不同大小的文件"""
        exporter_high = Exporter(format=OutputFormat.JPEG, quality=95)
        exporter_low = Exporter(format=OutputFormat.JPEG, quality=10)

        out_high = exporter_high.export(static_result, str(tmp_path / "high.jpg"))
        out_low = exporter_low.export(static_result, str(tmp_path / "low.jpg"))

        # 高质量文件应比低质量文件大
        assert Path(out_high).stat().st_size >= Path(out_low).stat().st_size


# ==================== 动态 GIF 导出测试 ====================

class TestExportAnimatedGif:
    """动态 GIF 导出测试"""

    def test_export_gif(self, animated_result, tmp_path):
        """导出动画 GIF 文件"""
        exporter = Exporter(format=OutputFormat.GIF)
        output = exporter.export(animated_result, str(tmp_path / "out.gif"))

        assert Path(output).exists()
        assert Path(output).suffix == ".gif"

    def test_export_gif_is_animated(self, animated_result, tmp_path):
        """导出的 GIF 确实是动画"""
        exporter = Exporter(format=OutputFormat.GIF)
        output = exporter.export(animated_result, str(tmp_path / "out.gif"))

        img = Image.open(output)
        assert getattr(img, "is_animated", False) is True

    def test_export_gif_frame_count(self, animated_result, tmp_path):
        """导出 GIF 的帧数与输入匹配"""
        exporter = Exporter(format=OutputFormat.GIF)
        output = exporter.export(animated_result, str(tmp_path / "out.gif"))

        img = Image.open(output)
        assert img.n_frames == len(animated_result.frames)

    def test_export_gif_dimensions(self, animated_result, tmp_path):
        """导出 GIF 尺寸匹配"""
        exporter = Exporter(format=OutputFormat.GIF)
        output = exporter.export(animated_result, str(tmp_path / "out.gif"))

        img = Image.open(output)
        assert img.width == animated_result.width
        assert img.height == animated_result.height

    @pytest.mark.parametrize("fmt", [OutputFormat.PNG, OutputFormat.JPEG])
    def test_explicit_static_only_format_raises_for_animated(self, animated_result, tmp_path, fmt):
        """动画结果显式导出为静态格式时应报错，而不是悄悄改格式"""
        exporter = Exporter(format=fmt)

        with pytest.raises(ValueError, match="动画结果不支持导出为 PNG/JPEG"):
            exporter.export(animated_result, str(tmp_path / "out"))


# ==================== 动态 APNG 导出测试 ====================

class TestExportAnimatedApng:
    """动态 APNG 导出测试"""

    def test_export_apng(self, animated_result, tmp_path):
        """导出 APNG 文件"""
        exporter = Exporter(format=OutputFormat.APNG)
        output = exporter.export(animated_result, str(tmp_path / "out.png"))

        assert Path(output).exists()
        assert Path(output).suffix == ".png"

    def test_export_apng_is_animated(self, animated_result, tmp_path):
        """导出的 APNG 确实是动画"""
        exporter = Exporter(format=OutputFormat.APNG)
        output = exporter.export(animated_result, str(tmp_path / "out.png"))

        img = Image.open(output)
        assert getattr(img, "is_animated", False) is True

    def test_export_apng_frame_count(self, animated_result, tmp_path):
        """导出 APNG 的帧数与输入匹配"""
        exporter = Exporter(format=OutputFormat.APNG)
        output = exporter.export(animated_result, str(tmp_path / "out.png"))

        img = Image.open(output)
        assert img.n_frames == len(animated_result.frames)


# ==================== 动态 WebP 导出测试 ====================

class TestExportAnimatedWebp:
    """动态 WebP 导出测试"""

    def test_export_webp(self, animated_result, tmp_path):
        """导出 WebP 文件"""
        exporter = Exporter(format=OutputFormat.WEBP)
        output = exporter.export(animated_result, str(tmp_path / "out.webp"))

        assert Path(output).exists()
        assert Path(output).suffix == ".webp"

    def test_export_webp_is_animated(self, animated_result, tmp_path):
        """导出的 WebP 确实是动画"""
        exporter = Exporter(format=OutputFormat.WEBP)
        output = exporter.export(animated_result, str(tmp_path / "out.webp"))

        img = Image.open(output)
        assert getattr(img, "is_animated", False) is True

    def test_export_webp_frame_count(self, animated_result, tmp_path):
        """导出 WebP 的帧数与输入匹配"""
        exporter = Exporter(format=OutputFormat.WEBP)
        output = exporter.export(animated_result, str(tmp_path / "out.webp"))

        img = Image.open(output)
        assert img.n_frames == len(animated_result.frames)


# ==================== 自动格式检测测试 ====================

class TestAutoFormat:
    """自动格式检测测试"""

    def test_auto_png_extension(self, static_result, tmp_path):
        """AUTO 模式 + .png 扩展名 -> PNG"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(static_result, str(tmp_path / "out.png"))
        assert Path(output).suffix == ".png"

    def test_auto_gif_extension_static(self, static_result, tmp_path):
        """AUTO 模式 + .gif 扩展名（静态内容） -> GIF"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(static_result, str(tmp_path / "out.gif"))
        assert Path(output).suffix == ".gif"

    def test_auto_gif_extension_animated(self, animated_result, tmp_path):
        """AUTO 模式 + .gif 扩展名（动态内容） -> GIF"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(animated_result, str(tmp_path / "out.gif"))
        assert Path(output).suffix == ".gif"

    def test_auto_jpg_extension(self, static_result, tmp_path):
        """AUTO 模式 + .jpg 扩展名 -> JPEG"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(static_result, str(tmp_path / "out.jpg"))
        assert Path(output).suffix == ".jpg"

    def test_auto_webp_extension(self, animated_result, tmp_path):
        """AUTO 模式 + .webp 扩展名 -> WebP"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(animated_result, str(tmp_path / "out.webp"))
        assert Path(output).suffix == ".webp"

    def test_auto_unknown_extension_static(self, static_result, tmp_path):
        """AUTO 模式 + 未知扩展名（静态） -> 默认 PNG"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(static_result, str(tmp_path / "out.xyz"))
        assert Path(output).suffix == ".png"

    def test_auto_unknown_extension_animated(self, animated_result, tmp_path):
        """AUTO 模式 + 未知扩展名（动态） -> 默认 GIF"""
        exporter = Exporter(format=OutputFormat.AUTO)
        output = exporter.export(animated_result, str(tmp_path / "out.xyz"))
        assert Path(output).suffix == ".gif"


# ==================== export_image_info 测试 ====================

class TestExportImageInfo:
    """export_image_info 方法测试"""

    def test_export_static_image_info(self, red_info, tmp_path):
        """从静态 ImageInfo 直接导出 PNG"""
        exporter = Exporter(format=OutputFormat.PNG)
        output = exporter.export_image_info(red_info, str(tmp_path / "out.png"))

        assert Path(output).exists()
        img = Image.open(output)
        assert img.width == red_info.width
        assert img.height == red_info.height

    def test_export_animated_image_info(self, anim1_info, tmp_path):
        """从动画 ImageInfo 直接导出 GIF"""
        exporter = Exporter(format=OutputFormat.GIF)
        output = exporter.export_image_info(anim1_info, str(tmp_path / "out.gif"))

        assert Path(output).exists()
        img = Image.open(output)
        assert getattr(img, "is_animated", False) is True
        assert img.n_frames == anim1_info.n_frames

    def test_export_image_info_webp(self, anim2_info, tmp_path):
        """从动画 ImageInfo 直接导出 WebP"""
        exporter = Exporter(format=OutputFormat.WEBP)
        output = exporter.export_image_info(anim2_info, str(tmp_path / "out.webp"))

        assert Path(output).exists()
        img = Image.open(output)
        assert getattr(img, "is_animated", False) is True


# ==================== 输出目录创建测试 ====================

class TestOutputDirectory:
    """输出目录自动创建测试"""

    def test_creates_parent_directory(self, static_result, tmp_path):
        """自动创建不存在的输出目录"""
        nested_dir = tmp_path / "sub" / "dir"
        exporter = Exporter(format=OutputFormat.PNG)
        output = exporter.export(static_result, str(nested_dir / "out.png"))

        assert Path(output).exists()
        assert nested_dir.is_dir()

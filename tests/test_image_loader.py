"""
图像加载模块单元测试

测试 ImageLoader 对静态/动态图片的加载、错误处理和批量加载功能。
"""

import pytest
from pathlib import Path
from PIL import Image

from image_stitch.core.image_loader import ImageLoader, ImageInfo


# ==================== 静态图片加载测试 ====================

class TestLoadStatic:
    """静态图片加载测试"""

    def test_load_png(self, loader, red_png_path):
        """加载 PNG 静态图片，验证基本属性"""
        info = loader.load(red_png_path)

        assert isinstance(info, ImageInfo)
        assert info.is_animated is False
        assert info.n_frames == 1
        assert info.width == 100
        assert info.height == 80
        assert info.format == "PNG"
        assert len(info.frames) == 1
        assert len(info.durations) == 1
        assert info.durations[0] == 0  # 静态图无时长
        assert info.total_duration == 0

    def test_load_png_frame_mode(self, loader, red_png_path):
        """加载的静态帧应转换为 RGBA 模式"""
        info = loader.load(red_png_path)
        assert info.frames[0].mode == "RGBA"

    def test_load_different_sizes(self, loader, red_png_path, green_png_path, blue_png_path):
        """加载不同尺寸的 PNG 图片"""
        red = loader.load(red_png_path)
        green = loader.load(green_png_path)
        blue = loader.load(blue_png_path)

        assert (red.width, red.height) == (100, 80)
        assert (green.width, green.height) == (80, 100)
        assert (blue.width, blue.height) == (100, 120)


# ==================== 动态图片加载测试 ====================

class TestLoadAnimated:
    """动态 GIF 加载测试"""

    def test_load_gif_basic(self, loader, anim1_gif_path):
        """加载 GIF 动画，验证基本属性"""
        info = loader.load(anim1_gif_path)

        assert isinstance(info, ImageInfo)
        assert info.is_animated is True
        assert info.n_frames == 3
        assert info.width == 100
        assert info.height == 100
        assert info.format == "GIF"

    def test_load_gif_frames(self, loader, anim1_gif_path):
        """GIF 帧数和时长列表长度匹配"""
        info = loader.load(anim1_gif_path)

        assert len(info.frames) == info.n_frames
        assert len(info.durations) == info.n_frames

    def test_load_gif_frame_mode(self, loader, anim1_gif_path):
        """所有 GIF 帧应转换为 RGBA 模式"""
        info = loader.load(anim1_gif_path)

        for frame in info.frames:
            assert frame.mode == "RGBA"

    def test_load_gif_durations(self, loader, anim1_gif_path):
        """GIF 帧时长应大于 0"""
        info = loader.load(anim1_gif_path)

        for dur in info.durations:
            assert dur > 0

    def test_load_gif_total_duration(self, loader, anim1_gif_path):
        """总时长等于各帧时长之和"""
        info = loader.load(anim1_gif_path)
        assert info.total_duration == sum(info.durations)

    def test_load_different_gifs(self, loader, anim1_gif_path, anim2_gif_path):
        """加载不同的 GIF 文件"""
        info1 = loader.load(anim1_gif_path)
        info2 = loader.load(anim2_gif_path)

        assert info1.n_frames == 3
        assert info2.n_frames == 5
        assert info1.width != info2.width or info1.height != info2.height

    def test_load_large_gif(self, loader, test_a_gif_path):
        """加载帧数较多的 GIF"""
        info = loader.load(test_a_gif_path)

        assert info.is_animated is True
        assert info.n_frames == 10
        assert info.width == 200
        assert info.height == 150


# ==================== 错误处理测试 ====================

class TestLoadErrors:
    """加载错误处理测试"""

    def test_missing_file(self, loader):
        """加载不存在的文件抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path/image.png")

    def test_unsupported_format(self, loader, tmp_path):
        """加载不支持的格式抛出 ValueError"""
        # 创建一个 .txt 后缀的文件
        fake_file = tmp_path / "test.txt"
        fake_file.write_text("not an image")

        with pytest.raises(ValueError, match="不支持的文件格式"):
            loader.load(str(fake_file))

    def test_unsupported_format_svg(self, loader, tmp_path):
        """SVG 格式不支持"""
        fake_file = tmp_path / "test.svg"
        fake_file.write_text("<svg></svg>")

        with pytest.raises(ValueError):
            loader.load(str(fake_file))


# ==================== 批量加载测试 ====================

class TestLoadMultiple:
    """批量加载测试"""

    def test_load_multiple_static(self, loader, red_png_path, green_png_path, blue_png_path):
        """批量加载多张静态图片"""
        paths = [red_png_path, green_png_path, blue_png_path]
        results = loader.load_multiple(paths)

        assert len(results) == 3
        assert all(isinstance(r, ImageInfo) for r in results)
        assert all(not r.is_animated for r in results)

    def test_load_multiple_mixed(self, loader, red_png_path, anim1_gif_path):
        """批量加载混合类型（静态 + 动态）"""
        results = loader.load_multiple([red_png_path, anim1_gif_path])

        assert len(results) == 2
        assert results[0].is_animated is False
        assert results[1].is_animated is True

    def test_load_multiple_empty(self, loader):
        """批量加载空列表返回空列表"""
        results = loader.load_multiple([])
        assert results == []

    def test_load_multiple_single(self, loader, red_png_path):
        """批量加载单个文件"""
        results = loader.load_multiple([red_png_path])
        assert len(results) == 1


# ==================== 默认时长测试 ====================

class TestDefaultDuration:
    """默认帧时长参数测试"""

    def test_custom_default_duration(self, anim1_gif_path):
        """自定义默认帧时长"""
        loader = ImageLoader(default_duration=200)
        assert loader.default_duration == 200


# ==================== ImageInfo 数据类测试 ====================

class TestImageInfoRepr:
    """ImageInfo 显示表示测试"""

    def test_static_repr(self, red_info):
        """静态图的 repr 包含 'static'"""
        r = repr(red_info)
        assert "static" in r
        assert "red.png" in r

    def test_animated_repr(self, anim1_info):
        """动态图的 repr 包含 'animated' 和帧数"""
        r = repr(anim1_info)
        assert "animated" in r
        assert "3 frames" in r

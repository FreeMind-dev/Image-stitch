"""
测试共享 Fixtures

提供所有测试模块共用的 pytest fixtures，包括：
- 测试图片路径
- 预加载的 ImageInfo 对象
- 临时输出目录
"""

import pytest
from pathlib import Path

from image_stitch.core.image_loader import ImageLoader, ImageInfo

# ==================== 路径常量 ====================

# 测试图片根目录
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"


# ==================== 路径 Fixtures ====================

@pytest.fixture
def test_images_dir():
    """测试图片目录路径"""
    return TEST_IMAGES_DIR


@pytest.fixture
def red_png_path():
    """红色静态 PNG 路径 (100x80)"""
    return str(TEST_IMAGES_DIR / "red.png")


@pytest.fixture
def green_png_path():
    """绿色静态 PNG 路径 (80x100)"""
    return str(TEST_IMAGES_DIR / "green.png")


@pytest.fixture
def blue_png_path():
    """蓝色静态 PNG 路径 (100x120)"""
    return str(TEST_IMAGES_DIR / "blue.png")


@pytest.fixture
def anim1_gif_path():
    """动画 GIF 1 路径 (100x100, 3帧)"""
    return str(TEST_IMAGES_DIR / "anim1.gif")


@pytest.fixture
def anim2_gif_path():
    """动画 GIF 2 路径 (80x100, 5帧)"""
    return str(TEST_IMAGES_DIR / "anim2.gif")


@pytest.fixture
def test_a_gif_path():
    """测试动画 GIF A 路径 (200x150, 10帧)"""
    return str(TEST_IMAGES_DIR / "test_a.gif")


@pytest.fixture
def test_b_gif_path():
    """测试动画 GIF B 路径 (150x200, 8帧)"""
    return str(TEST_IMAGES_DIR / "test_b.gif")


@pytest.fixture
def test_c_png_path():
    """测试静态 PNG C 路径 (100x180)"""
    return str(TEST_IMAGES_DIR / "test_c.png")


# ==================== ImageLoader Fixture ====================

@pytest.fixture
def loader():
    """ImageLoader 实例"""
    return ImageLoader()


# ==================== 预加载 ImageInfo Fixtures ====================

@pytest.fixture
def red_info(loader, red_png_path):
    """预加载的红色 PNG ImageInfo (100x80, 静态)"""
    return loader.load(red_png_path)


@pytest.fixture
def green_info(loader, green_png_path):
    """预加载的绿色 PNG ImageInfo (80x100, 静态)"""
    return loader.load(green_png_path)


@pytest.fixture
def blue_info(loader, blue_png_path):
    """预加载的蓝色 PNG ImageInfo (100x120, 静态)"""
    return loader.load(blue_png_path)


@pytest.fixture
def anim1_info(loader, anim1_gif_path):
    """预加载的动画 GIF 1 ImageInfo (100x100, 3帧)"""
    return loader.load(anim1_gif_path)


@pytest.fixture
def anim2_info(loader, anim2_gif_path):
    """预加载的动画 GIF 2 ImageInfo (80x100, 5帧)"""
    return loader.load(anim2_gif_path)


@pytest.fixture
def test_a_info(loader, test_a_gif_path):
    """预加载的测试动画 A ImageInfo (200x150, 10帧)"""
    return loader.load(test_a_gif_path)


@pytest.fixture
def test_b_info(loader, test_b_gif_path):
    """预加载的测试动画 B ImageInfo (150x200, 8帧)"""
    return loader.load(test_b_gif_path)


@pytest.fixture
def test_c_info(loader, test_c_png_path):
    """预加载的测试静态 C ImageInfo (100x180, 静态)"""
    return loader.load(test_c_png_path)

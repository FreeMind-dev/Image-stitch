"""
GUI 图形界面子包

提供图片拼接工具的图形界面组件：
- ImageStitchGUI: 主窗口
- CropDialog: 图片剪裁对话框
- StitchDialog: 图片拼接对话框
- theme: 统一主题配置

使用示例:
    >>> from image_stitch.gui import ImageStitchGUI, run_gui
    >>> # 方式1：直接启动
    >>> run_gui()
    >>> # 方式2：手动创建
    >>> import tkinter as tk
    >>> root = tk.Tk()
    >>> app = ImageStitchGUI(root)
    >>> root.mainloop()
"""

from .main_window import ImageStitchGUI, run_gui
from .crop_dialog import CropDialog
from .stitch_dialog import StitchDialog
from . import theme

__all__ = [
    "ImageStitchGUI",
    "CropDialog",
    "StitchDialog",
    "run_gui",
    "theme",
]

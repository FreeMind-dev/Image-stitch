"""
GUI 图形界面模块（兼容入口）

此文件保留用于向后兼容，实际实现已移至 gui/ 子包：
- gui/main_window.py: 主窗口
- gui/crop_dialog.py: 剪裁对话框
- gui/stitch_dialog.py: 拼接对话框

推荐直接使用：
    from image_stitch.gui import ImageStitchGUI, CropDialog, StitchDialog, run_gui
"""

# 从 gui 子包导入所有公共接口
from .gui import (
    ImageStitchGUI,
    CropDialog,
    StitchDialog,
    run_gui,
)

# 保持原有的公共接口
__all__ = [
    "ImageStitchGUI",
    "CropDialog",
    "StitchDialog",
    "run_gui",
]


if __name__ == "__main__":
    import sys
    sys.exit(run_gui())

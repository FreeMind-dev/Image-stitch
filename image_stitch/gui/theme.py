"""
GUI 主题配置模块

定义统一的颜色、字体和样式常量，确保各界面组件风格一致。
采用现代扁平化设计风格。
"""

import tkinter as tk
from tkinter import ttk


# ==================== 配色方案 ====================
COLORS = {
    # 基础色
    "bg": "#F0F4F8",                # 页面背景（柔和灰蓝）
    "panel": "#FFFFFF",             # 面板/卡片背景
    "canvas": "#E8EDF2",            # 画布/预览区背景

    # 主题色（蓝色系）
    "primary": "#3B82F6",           # 主色调
    "primary_hover": "#2563EB",     # 主色悬停
    "primary_active": "#1D4ED8",    # 主色激活
    "primary_light": "#DBEAFE",     # 主色浅色背景
    "primary_lighter": "#EFF6FF",   # 主色极浅背景

    # 功能色
    "success": "#22C55E",           # 成功/确认
    "success_hover": "#16A34A",
    "warning": "#F59E0B",           # 警告
    "danger": "#EF4444",            # 危险/删除
    "danger_hover": "#DC2626",

    # 文字色
    "text": "#1E293B",              # 主文字
    "text_secondary": "#475569",    # 次要文字
    "text_muted": "#94A3B8",        # 淡化文字
    "text_inverse": "#FFFFFF",      # 反色文字（按钮上的白字）

    # 边框色
    "border": "#CBD5E1",            # 默认边框
    "border_light": "#E2E8F0",      # 浅色边框
    "border_focus": "#3B82F6",      # 聚焦边框

    # 选中色
    "selected": "#3B82F6",          # 选中项目
    "selected_bg": "#DBEAFE",       # 选中背景
    "selected_text": "#FFFFFF",     # 选中文字

    # 特殊用途
    "crop_border": "#22C55E",       # 裁剪选区边框（绿色）
    "crop_handle": "#FFFFFF",       # 裁剪控制柄
    "thumb_border": "#3B82F6",      # 缩略图边框
    "overlay": "#000000",           # 遮罩层
    "hint": "#94A3B8",              # 提示文字
}

# ==================== 字体配置 ====================
# 使用空字符串作为字体族名，自动使用系统默认字体（跨平台兼容）
FONTS = {
    "title": ("", 15, "bold"),
    "subtitle": ("", 11, "bold"),
    "body": ("", 10),
    "body_bold": ("", 10, "bold"),
    "small": ("", 9),
    "tiny": ("", 8),
}

# ==================== 尺寸常量 ====================
SIZES = {
    "padding": 12,
    "padding_small": 6,
    "padding_large": 16,
    "button_width": 12,
    "button_width_small": 8,
    "thumb_size": 54,
    "thumb_margin": 6,
    "handle_size": 8,
    "edge_threshold": 10,
    "preview_max_w": 520,
    "preview_max_h": 420,
}


def setup_styles(root: tk.Tk) -> ttk.Style:
    """
    配置 ttk 全局样式

    参数:
        root: Tkinter 根窗口

    返回:
        配置好的 ttk.Style 对象
    """
    style = ttk.Style()

    # 选择最佳可用主题
    try:
        ws = root.tk.call("tk", "windowingsystem")
        if ws == "aqua":
            style.theme_use("aqua")
        elif ws == "win32":
            style.theme_use("vista")
        else:
            style.theme_use("clam")
    except tk.TclError:
        pass

    # 全局基础样式
    style.configure(".", font=FONTS["body"], background=COLORS["bg"])

    # ---- Label 样式 ----
    style.configure("Title.TLabel", font=FONTS["title"], foreground=COLORS["text"])
    style.configure("Subtitle.TLabel", font=FONTS["subtitle"], foreground=COLORS["text"])
    style.configure("Body.TLabel", font=FONTS["body"], foreground=COLORS["text"])
    style.configure("Small.TLabel", font=FONTS["small"], foreground=COLORS["text_secondary"])
    style.configure("Muted.TLabel", font=FONTS["tiny"], foreground=COLORS["text_muted"])
    style.configure("Info.TLabel", font=FONTS["small"], foreground=COLORS["text_secondary"])

    # 状态栏
    style.configure(
        "Status.TLabel",
        font=FONTS["small"],
        foreground=COLORS["text_secondary"],
        background=COLORS["panel"],
        padding=(12, 6),
    )

    # ---- Button 样式 ----
    style.configure(
        "TButton",
        font=FONTS["body"],
        padding=(10, 5),
    )

    # 主要操作按钮（蓝底白字）
    style.configure(
        "Primary.TButton",
        font=FONTS["body_bold"],
        foreground=COLORS["text_inverse"],
        background=COLORS["primary"],
        padding=(12, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", COLORS["primary_hover"]), ("pressed", COLORS["primary_active"])],
        foreground=[("active", COLORS["text_inverse"])],
    )

    # 成功按钮（绿底白字）
    style.configure(
        "Success.TButton",
        font=FONTS["body_bold"],
        foreground=COLORS["text_inverse"],
        background=COLORS["success"],
        padding=(12, 6),
    )
    style.map(
        "Success.TButton",
        background=[("active", COLORS["success_hover"])],
        foreground=[("active", COLORS["text_inverse"])],
    )

    # 危险按钮
    style.configure(
        "Danger.TButton",
        font=FONTS["body"],
        foreground=COLORS["danger"],
    )

    # ---- Frame/LabelFrame 样式 ----
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Panel.TFrame", background=COLORS["panel"])
    style.configure(
        "TLabelframe",
        background=COLORS["bg"],
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        font=FONTS["subtitle"],
        foreground=COLORS["text"],
        background=COLORS["bg"],
    )

    # ---- Combobox / Spinbox 样式 ----
    style.configure("TCombobox", padding=4)
    style.configure("TSpinbox", padding=4)

    # ---- Separator 样式 ----
    style.configure("TSeparator", background=COLORS["border_light"])

    return style

"""
图片拼接工具主窗口模块

核心功能：
- 添加/删除/排序/剪裁图片
- 预览单张图片（支持动画播放）
- 点击 Stitch 打开拼接对话框进行拼接和导出

注意：拼接设置和导出功能已移至 StitchDialog
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional
from pathlib import Path
from PIL import Image, ImageTk

from ..core.image_loader import ImageLoader, ImageInfo
from ..core.cropper import CropBox
from .crop_dialog import CropDialog
from .stitch_dialog import StitchDialog
from .theme import COLORS, FONTS, SIZES, setup_styles


class ImageStitchGUI:
    """
    图片拼接工具图形界面

    功能:
        - 添加/删除/排序/剪裁图片
        - 预览单张图片（支持动画播放）
        - 点击 Stitch 打开拼接对话框
    """

    # 窗口尺寸
    WINDOW_WIDTH = 860
    WINDOW_HEIGHT = 640
    PREVIEW_MAX_WIDTH = 540
    PREVIEW_MAX_HEIGHT = 440

    # 支持的文件格式
    SUPPORTED_FORMATS = [
        ("Image Files", "*.png *.jpg *.jpeg *.gif *.webp *.bmp *.tiff"),
        ("PNG Files", "*.png"),
        ("JPEG Files", "*.jpg *.jpeg"),
        ("GIF Files", "*.gif"),
        ("WebP Files", "*.webp"),
        ("All Files", "*.*"),
    ]

    def __init__(self, root: tk.Tk):
        """
        初始化 GUI

        参数:
            root: Tkinter 根窗口
        """
        self.root = root
        self.root.title("Image Stitch Tool v1.1")
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.minsize(750, 530)
        self.root.configure(bg=COLORS["bg"])

        # 数据
        self.loader = ImageLoader()
        self.image_infos: List[ImageInfo] = []
        self.preview_image: Optional[ImageTk.PhotoImage] = None

        # 动画播放状态
        self.animation_id: Optional[str] = None
        self.animation_frames: List[ImageTk.PhotoImage] = []
        self.animation_durations: List[int] = []
        self.current_frame_idx: int = 0

        # 设置样式
        setup_styles(self.root)

        # 创建界面
        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = ttk.Frame(self.root, padding=SIZES["padding"])
        main_container.pack(fill=tk.BOTH, expand=True)

        # ===== 顶部工具栏 =====
        self._create_toolbar(main_container)

        # ===== 分隔线 =====
        ttk.Separator(main_container, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(8, 10))

        # ===== 内容区域 =====
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：图片列表面板
        self._create_left_panel(content_frame)

        # 中间：预览面板
        self._create_center_panel(content_frame)

        # ===== 底部状态栏 =====
        self._create_statusbar()

    def _create_toolbar(self, parent):
        """创建顶部工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X)

        # 左侧按钮组
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        ttk.Button(
            btn_frame, text="Add Images", command=self._add_images, width=12
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_frame, text="Crop", command=self._crop_selected, width=8
        ).pack(side=tk.LEFT, padx=6)

        ttk.Button(
            btn_frame, text="Stitch", command=self._open_stitch_dialog,
            width=10, style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=6)

        # 右侧标题
        title_frame = ttk.Frame(toolbar)
        title_frame.pack(side=tk.RIGHT)

        ttk.Label(
            title_frame, text="Image Stitch Tool", style="Title.TLabel"
        ).pack(side=tk.RIGHT, padx=4)

        ttk.Label(
            title_frame, text="v1.1", style="Muted.TLabel"
        ).pack(side=tk.RIGHT, padx=(0, 6), pady=(6, 0))

    def _create_left_panel(self, parent):
        """创建左侧图片列表面板"""
        left_frame = ttk.LabelFrame(parent, text="Image List", padding=SIZES["padding_small"])
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        # 图片列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            height=18,
            width=30,
            font=FONTS["small"],
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectbackground=COLORS["primary"],
            selectforeground=COLORS["text_inverse"],
            activestyle="none",
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["border_focus"],
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # 操作按钮（两行）
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        btn_row1 = ttk.Frame(btn_frame)
        btn_row1.pack(fill=tk.X)
        ttk.Button(btn_row1, text="Up", command=self._move_up, width=7).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row1, text="Down", command=self._move_down, width=7).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row1, text="Delete", command=self._remove_selected, width=8).pack(side=tk.LEFT, padx=2)

        btn_row2 = ttk.Frame(btn_frame)
        btn_row2.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row2, text="Clear All", command=self._clear_all, width=24).pack()

    def _create_center_panel(self, parent):
        """创建中间预览面板"""
        center_frame = ttk.LabelFrame(parent, text="Preview", padding=SIZES["padding_small"])
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 预览画布
        preview_container = ttk.Frame(center_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(
            preview_container,
            bg=COLORS["canvas"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # 预览信息
        self.info_label = ttk.Label(center_frame, text="", style="Info.TLabel")
        self.info_label.pack(pady=(6, 0))

        # 初始提示文字
        self._show_preview_hint("Add images to get started")

    def _create_statusbar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 上方分隔线
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
        )
        status_label.pack(fill=tk.X)

    def _bind_events(self):
        """绑定事件"""
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_selection_change())
        self.listbox.bind("<Double-Button-1>", lambda e: self._crop_selected())
        self.root.bind("<Delete>", lambda e: self._remove_selected())
        self.root.bind("<Control-o>", lambda e: self._add_images())
        self.root.bind("<Control-s>", lambda e: self._open_stitch_dialog())

        # 拖拽支持
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
        except ImportError:
            pass

    # ========== 图片管理方法 ==========

    def _add_images(self):
        """添加图片"""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=self.SUPPORTED_FORMATS,
        )

        if files:
            self._load_images(list(files))

    def _load_images(self, paths: List[str]):
        """
        加载图片文件

        参数:
            paths: 图片文件路径列表
        """
        for path in paths:
            try:
                info = self.loader.load(path)
                self.image_infos.append(info)
                self._update_listbox()
                self.status_var.set(f"Added: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Load Error", f"Cannot load {path}:\n{e}")

        if self.image_infos:
            self.status_var.set(f"{len(self.image_infos)} images loaded  |  Click to preview, Ctrl+S to stitch")

    def _update_listbox(self):
        """更新列表显示"""
        self.listbox.delete(0, tk.END)
        for info in self.image_infos:
            name = Path(info.path).name
            if len(name) > 22:
                name = name[:19] + "..."
            anim_str = f" ({info.n_frames}f)" if info.is_animated else ""
            self.listbox.insert(tk.END, f"{name} [{info.width}x{info.height}]{anim_str}")

    def _remove_selected(self):
        """删除选中的图片"""
        selection = self.listbox.curselection()
        if selection:
            for idx in reversed(selection):
                del self.image_infos[idx]
            self._update_listbox()
            self._stop_animation()
            self._show_preview_hint("Click an image to preview")
            self.status_var.set(f"{len(self.image_infos)} images")

    def _move_up(self):
        """上移选中项"""
        selection = self.listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            self.image_infos[idx - 1], self.image_infos[idx] = (
                self.image_infos[idx],
                self.image_infos[idx - 1],
            )
            self._update_listbox()
            self.listbox.select_set(idx - 1)
            self._on_selection_change()

    def _move_down(self):
        """下移选中项"""
        selection = self.listbox.curselection()
        if selection and selection[0] < len(self.image_infos) - 1:
            idx = selection[0]
            self.image_infos[idx], self.image_infos[idx + 1] = (
                self.image_infos[idx + 1],
                self.image_infos[idx],
            )
            self._update_listbox()
            self.listbox.select_set(idx + 1)
            self._on_selection_change()

    def _clear_all(self):
        """清空所有图片"""
        self.image_infos.clear()
        self._update_listbox()
        self._stop_animation()
        self.preview_image = None
        self._show_preview_hint("Add images to get started")
        self.status_var.set("Ready")

    def _crop_selected(self):
        """剪裁选中的图片"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an image to crop")
            return

        idx = selection[0]
        info = self.image_infos[idx]

        def on_crop_done(cropped_info: ImageInfo, box: CropBox):
            self.image_infos[idx] = cropped_info
            self._update_listbox()
            self._preview_single_image(idx)
            self.status_var.set(f"Cropped: {Path(info.path).name}")

        CropDialog(self.root, info, on_crop_done)

    def _on_drop(self, event):
        """拖拽放下事件"""
        files = self.root.tk.splitlist(event.data)
        self._load_images(list(files))

    # ========== 动画播放相关方法 ==========

    def _scale_preview_frame(self, frame: Image.Image) -> Image.Image:
        """
        缩放帧以适应预览区域

        参数:
            frame: PIL Image 帧

        返回:
            缩放后的帧
        """
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")

        w, h = frame.size
        scale = min(self.PREVIEW_MAX_WIDTH / w, self.PREVIEW_MAX_HEIGHT / h, 1.0)
        if scale < 1.0:
            new_size = (int(w * scale), int(h * scale))
            frame = frame.resize(new_size, Image.Resampling.LANCZOS)
        return frame

    def _play_animation(self):
        """播放动画下一帧"""
        if not self.animation_frames:
            return

        if self.current_frame_idx >= len(self.animation_frames):
            self.current_frame_idx = 0

        canvas_w = self.preview_canvas.winfo_width() or self.PREVIEW_MAX_WIDTH
        canvas_h = self.preview_canvas.winfo_height() or self.PREVIEW_MAX_HEIGHT

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_w // 2,
            canvas_h // 2,
            image=self.animation_frames[self.current_frame_idx],
            anchor=tk.CENTER
        )

        delay = max(self.animation_durations[self.current_frame_idx], 20)
        self.animation_id = self.root.after(delay, self._play_animation)
        self.current_frame_idx += 1

    def _stop_animation(self):
        """停止动画播放"""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None
        self.animation_frames = []
        self.current_frame_idx = 0

    def _show_preview_hint(self, text: str):
        """
        在预览区显示提示文字

        参数:
            text: 提示文字内容
        """
        self.preview_canvas.delete("all")

        self.preview_canvas.update_idletasks()
        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()

        if canvas_w < 10:
            canvas_w = self.PREVIEW_MAX_WIDTH
        if canvas_h < 10:
            canvas_h = self.PREVIEW_MAX_HEIGHT

        self.preview_canvas.create_text(
            canvas_w // 2,
            canvas_h // 2,
            text=text,
            font=FONTS["body"],
            fill=COLORS["hint"],
            tags="hint"
        )
        self.info_label.config(text="")

    def _on_selection_change(self):
        """选择变化时的处理 - 预览选中的单张图片"""
        selection = self.listbox.curselection()
        if selection:
            self._preview_single_image(selection[0])
        else:
            self._stop_animation()
            self._show_preview_hint("Click an image to preview")

    def _preview_single_image(self, index: int):
        """
        预览单张图片（支持动画播放）

        参数:
            index: 图片在列表中的索引
        """
        self._stop_animation()

        if not (0 <= index < len(self.image_infos)):
            return

        info = self.image_infos[index]

        canvas_w = self.preview_canvas.winfo_width() or self.PREVIEW_MAX_WIDTH
        canvas_h = self.preview_canvas.winfo_height() or self.PREVIEW_MAX_HEIGHT

        if info.is_animated and info.n_frames > 1:
            # 动图：预处理所有帧并启动动画播放
            self.animation_frames = []
            for frame in info.frames:
                scaled = self._scale_preview_frame(frame.copy())
                self.animation_frames.append(ImageTk.PhotoImage(scaled))
            self.animation_durations = info.durations.copy()
            self.current_frame_idx = 0
            self._play_animation()
        else:
            # 静态图：显示单帧
            frame = self._scale_preview_frame(info.frames[0].copy())
            self.preview_image = ImageTk.PhotoImage(frame)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_w // 2,
                canvas_h // 2,
                image=self.preview_image,
                anchor=tk.CENTER
            )

        # 更新信息标签
        anim_str = f"Animation ({info.n_frames} frames, {info.total_duration}ms)" if info.is_animated else "Static"
        self.info_label.config(text=f"{info.width} x {info.height}  |  {anim_str}")

    def _open_stitch_dialog(self):
        """
        打开拼接对话框
        """
        if len(self.image_infos) < 2:
            messagebox.showwarning("Warning", "Need at least 2 images to stitch")
            return

        self._stop_animation()
        StitchDialog(self.root, self.image_infos)


def run_gui() -> int:
    """
    启动 GUI

    返回:
        退出码
    """
    root = tk.Tk()
    app = ImageStitchGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_gui())

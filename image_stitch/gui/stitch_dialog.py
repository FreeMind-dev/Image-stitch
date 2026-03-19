"""
图片拼接对话框模块

功能：
- 美观的复选框选择图片
- 预览区底部可拖拽缩略图调整顺序
- 动画预览拼接效果
- 导出设置（高度模式、间距、同步模式、拼接方向）
- 一键导出（动图自动用GIF，静图自动用PNG）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional
from pathlib import Path
from PIL import Image, ImageTk

from ..core.image_loader import ImageInfo
from ..core.stitcher import ImageStitcher, HeightMode, Direction, StitchResult
from ..core.exporter import Exporter, OutputFormat
from ..core.frame_sync import SyncMode
from .theme import COLORS, FONTS, SIZES


class StitchDialog(tk.Toplevel):
    """
    图片拼接对话框

    功能：
    - 美观的复选框选择图片
    - 预览区底部可拖拽缩略图调整顺序
    - 点击 Preview 按钮预览拼接效果（支持动画）
    - 完整的导出设置（高度模式、间距、同步模式、拼接方向）
    - 一键导出（动图用GIF，静图用PNG）
    """

    # 预览区最大尺寸
    PREVIEW_MAX_WIDTH = 560
    PREVIEW_MAX_HEIGHT = 340

    # 缩略图尺寸
    THUMB_SIZE = SIZES["thumb_size"]
    THUMB_MARGIN = SIZES["thumb_margin"]

    def __init__(self, parent: tk.Tk, image_infos: List[ImageInfo]):
        """
        初始化拼接对话框

        参数:
            parent: 父窗口
            image_infos: 可选图片列表
        """
        super().__init__(parent)
        self.parent = parent
        self.image_infos = list(image_infos)

        # 选择状态
        self.check_vars: List[tk.BooleanVar] = []
        self.check_canvases: List[tk.Canvas] = []

        # 缩略图相关
        self.thumbnails: List[ImageTk.PhotoImage] = []
        self.selected_order: List[int] = []
        self.drag_data = {"item": None, "x": 0, "start_idx": None}

        # 拼接结果
        self.stitch_result: Optional[StitchResult] = None

        # 动画播放状态
        self.stitch_animation_id: Optional[str] = None
        self.stitch_animation_frames: List[ImageTk.PhotoImage] = []
        self.stitch_animation_durations: List[int] = []
        self.stitch_current_frame_idx: int = 0
        self.preview_image: Optional[ImageTk.PhotoImage] = None

        # 导出设置变量
        self.height_mode_var = tk.StringVar(value="max")
        self.spacing_var = tk.IntVar(value=0)
        self.sync_mode_var = tk.StringVar(value="time_sync")
        self.direction_var = tk.StringVar(value="horizontal")

        self._setup_window()
        self._create_widgets()
        self._generate_thumbnails()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        """设置窗口属性"""
        self.title("Stitch Images")
        self.transient(self.parent)
        self.grab_set()
        self.geometry("960x700")
        self.minsize(860, 620)
        self.resizable(True, True)
        self.configure(bg=COLORS["bg"])

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding=SIZES["padding"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== 内容区域（左右布局） =====
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # ----- 左侧：图片选择 + 设置 -----
        left_frame = ttk.Frame(content_frame, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)

        # 图片选择区域
        self._create_selection_panel(left_frame)

        # 导出设置区域
        self._create_settings_panel(left_frame)

        # ----- 右侧：预览区域 -----
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 预览画布
        self._create_preview_panel(right_frame)

        # 缩略图排序条
        self._create_thumbnail_bar(right_frame)

        # 初始提示
        self.after(100, lambda: self._show_preview_hint("Select images and click Preview"))

        # ===== 底部按钮栏 =====
        self._create_bottom_buttons(main_frame)

    def _create_selection_panel(self, parent):
        """创建图片选择面板"""
        select_frame = ttk.LabelFrame(parent, text="Select Images", padding=SIZES["padding_small"])
        select_frame.pack(fill=tk.BOTH, expand=True)

        # 滚动画布
        canvas_container = ttk.Frame(select_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.checkbox_canvas = tk.Canvas(
            canvas_container,
            highlightthickness=0,
            bg=COLORS["panel"],
        )
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.checkbox_canvas.yview)
        self.checkbox_frame = ttk.Frame(self.checkbox_canvas)

        self.checkbox_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.checkbox_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.checkbox_window = self.checkbox_canvas.create_window(
            (0, 0), window=self.checkbox_frame, anchor=tk.NW
        )
        self.checkbox_frame.bind("<Configure>", self._on_checkbox_frame_configure)
        self.checkbox_canvas.bind("<Configure>", self._on_canvas_configure)

        # 创建图片列表
        self._create_checkbox_list()

        # 全选/取消全选按钮
        btn_row = ttk.Frame(select_frame)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_row, text="Select All", command=self._select_all, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_row, text="None", command=self._select_none, width=8).pack(side=tk.LEFT, padx=2)

    def _create_settings_panel(self, parent):
        """创建导出设置面板"""
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding=SIZES["padding_small"])
        settings_frame.pack(fill=tk.X, pady=(10, 0))

        # 拼接方向
        self._add_setting_row(
            settings_frame, "Direction:", self.direction_var,
            ["horizontal", "vertical"], 0
        )

        # 尺寸模式
        self._add_setting_row(
            settings_frame, "Size Mode:", self.height_mode_var,
            ["max", "min"], 1
        )

        # 间距
        spacing_row = ttk.Frame(settings_frame)
        spacing_row.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=3)
        ttk.Label(spacing_row, text="Spacing:", width=10, style="Small.TLabel").pack(side=tk.LEFT)
        ttk.Spinbox(
            spacing_row, from_=0, to=100,
            textvariable=self.spacing_var, width=10,
            font=FONTS["small"],
        ).pack(side=tk.LEFT, padx=(4, 0))

        # 同步模式
        self._add_setting_row(
            settings_frame, "Sync Mode:", self.sync_mode_var,
            ["time_sync", "loop", "longest", "shortest", "lcm"], 3
        )

        # 格式说明
        ttk.Label(
            settings_frame,
            text="Export: Auto (GIF for animated, PNG for static)",
            style="Muted.TLabel",
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

    def _add_setting_row(self, parent, label: str, var: tk.StringVar, values: list, row: int):
        """添加一行设置项"""
        ttk.Label(
            parent, text=label, width=10, style="Small.TLabel"
        ).grid(row=row, column=0, sticky=tk.W, pady=3)
        ttk.Combobox(
            parent, textvariable=var, values=values,
            width=12, state="readonly", font=FONTS["small"],
        ).grid(row=row, column=1, sticky=tk.W, padx=(4, 0), pady=3)

    def _create_preview_panel(self, parent):
        """创建预览面板"""
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding=SIZES["padding_small"])
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg=COLORS["canvas"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # 预览信息
        self.info_label = ttk.Label(preview_frame, text="", style="Info.TLabel")
        self.info_label.pack(pady=(6, 0))

    def _create_thumbnail_bar(self, parent):
        """创建缩略图排序条"""
        thumb_frame = ttk.LabelFrame(parent, text="Drag to Reorder", padding=SIZES["padding_small"])
        thumb_frame.pack(fill=tk.X, pady=(10, 0))

        self.thumb_canvas = tk.Canvas(
            thumb_frame,
            height=self.THUMB_SIZE + 12,
            bg=COLORS["canvas"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.thumb_canvas.pack(fill=tk.X)

        # 绑定缩略图拖拽事件
        self.thumb_canvas.bind("<Button-1>", self._on_thumb_click)
        self.thumb_canvas.bind("<B1-Motion>", self._on_thumb_drag)
        self.thumb_canvas.bind("<ButtonRelease-1>", self._on_thumb_release)

    def _create_bottom_buttons(self, parent):
        """创建底部按钮栏"""
        # 分隔线
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(10, 8))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame, text="Preview", command=self._update_stitch_preview,
            width=12, style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            btn_frame, text="Export", command=self._export,
            width=12, style="Success.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            btn_frame, text="Close", command=self._on_close, width=10
        ).pack(side=tk.RIGHT, padx=4)

    # ========== 复选框列表相关 ==========

    def _on_checkbox_frame_configure(self, event):
        """复选框frame大小变化时更新滚动区域"""
        self.checkbox_canvas.configure(scrollregion=self.checkbox_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """画布大小变化时调整内部frame宽度"""
        self.checkbox_canvas.itemconfig(self.checkbox_window, width=event.width)

    def _create_checkbox_list(self):
        """创建图片列表（带美化复选框）"""
        self.check_vars = []
        self.check_canvases = []
        for i, info in enumerate(self.image_infos):
            self._create_checkbox_row(i, info)

    def _create_checkbox_row(self, idx: int, info: ImageInfo):
        """创建单个复选框行"""
        row_frame = ttk.Frame(self.checkbox_frame)
        row_frame.pack(fill=tk.X, pady=2)

        var = tk.BooleanVar(value=False)
        self.check_vars.append(var)

        # 自绘复选框
        check_canvas = tk.Canvas(
            row_frame, width=20, height=20,
            bg=COLORS["panel"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            cursor="hand2"
        )
        check_canvas.pack(side=tk.LEFT, padx=(4, 8))
        self.check_canvases.append(check_canvas)

        check_canvas.bind("<Button-1>", lambda e, i=idx: self._toggle_check(i))

        # 文件名标签
        name = Path(info.path).name
        if len(name) > 22:
            name = name[:19] + "..."
        anim_str = f" ({info.n_frames}f)" if info.is_animated else ""
        display_text = f"{name}{anim_str}"

        name_label = ttk.Label(
            row_frame, text=display_text, cursor="hand2", style="Small.TLabel"
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        name_label.bind("<Button-1>", lambda e, i=idx: self._toggle_check(i))

    def _draw_checkbox(self, idx: int):
        """绘制复选框状态"""
        if idx >= len(self.check_canvases):
            return

        canvas = self.check_canvases[idx]
        canvas.delete("all")

        if self.check_vars[idx].get():
            # 选中：蓝色背景 + 白色勾
            canvas.configure(bg=COLORS["primary"], highlightbackground=COLORS["primary_hover"])
            canvas.create_line(4, 10, 8, 14, fill=COLORS["text_inverse"], width=2)
            canvas.create_line(8, 14, 16, 6, fill=COLORS["text_inverse"], width=2)
        else:
            # 未选中
            canvas.configure(bg=COLORS["panel"], highlightbackground=COLORS["border"])

    def _toggle_check(self, idx: int):
        """切换复选框状态"""
        if 0 <= idx < len(self.check_vars):
            current = self.check_vars[idx].get()
            self.check_vars[idx].set(not current)
            self._draw_checkbox(idx)
            self._update_thumb_selection()

    def _select_all(self):
        """全选"""
        for i, var in enumerate(self.check_vars):
            var.set(True)
            self._draw_checkbox(i)
        self._update_thumb_selection()

    def _select_none(self):
        """取消全选"""
        for i, var in enumerate(self.check_vars):
            var.set(False)
            self._draw_checkbox(i)
        self._update_thumb_selection()

    # ========== 缩略图相关 ==========

    def _generate_thumbnails(self):
        """生成所有图片的缩略图"""
        self.thumbnails = []
        self.selected_order = []

        for info in self.image_infos:
            frame = info.frames[0].copy()
            frame.thumbnail((self.THUMB_SIZE, self.THUMB_SIZE), Image.Resampling.LANCZOS)

            # 创建正方形画布（居中粘贴）
            thumb = Image.new("RGBA", (self.THUMB_SIZE, self.THUMB_SIZE), (240, 240, 240, 255))
            x = (self.THUMB_SIZE - frame.width) // 2
            y = (self.THUMB_SIZE - frame.height) // 2
            if frame.mode == "RGBA":
                thumb.paste(frame, (x, y), frame)
            else:
                thumb.paste(frame, (x, y))

            self.thumbnails.append(ImageTk.PhotoImage(thumb))

        self._draw_thumbnails()

    def _draw_thumbnails(self):
        """绘制缩略图条"""
        self.thumb_canvas.delete("all")

        if not self.selected_order:
            canvas_w = self.thumb_canvas.winfo_width() or 400
            self.thumb_canvas.create_text(
                canvas_w // 2,
                (self.THUMB_SIZE + 12) // 2,
                text="Select images to reorder",
                fill=COLORS["hint"],
                font=FONTS["small"]
            )
            return

        x = self.THUMB_MARGIN
        for i, idx in enumerate(self.selected_order):
            if idx < len(self.thumbnails):
                self.thumb_canvas.create_image(
                    x, 6, image=self.thumbnails[idx], anchor=tk.NW, tags=f"thumb_{i}"
                )
                # 蓝色边框
                self.thumb_canvas.create_rectangle(
                    x - 2, 4,
                    x + self.THUMB_SIZE + 2, 8 + self.THUMB_SIZE,
                    outline=COLORS["thumb_border"], width=2, tags=f"border_{i}"
                )
                x += self.THUMB_SIZE + self.THUMB_MARGIN

    def _update_thumb_selection(self):
        """选择变化时更新缩略图条"""
        currently_selected = set(
            i for i, var in enumerate(self.check_vars) if var.get()
        )

        new_order = [idx for idx in self.selected_order if idx in currently_selected]
        for i in range(len(self.check_vars)):
            if i in currently_selected and i not in new_order:
                new_order.append(i)

        self.selected_order = new_order
        self._draw_thumbnails()

    def _on_thumb_click(self, event):
        """缩略图点击开始"""
        if not self.selected_order:
            return
        idx = (event.x - self.THUMB_MARGIN) // (self.THUMB_SIZE + self.THUMB_MARGIN)
        if 0 <= idx < len(self.selected_order):
            self.drag_data["start_idx"] = idx
            self.drag_data["x"] = event.x
            self.drag_data["item"] = idx

    def _on_thumb_drag(self, event):
        """缩略图拖拽中"""
        if self.drag_data["item"] is None or not self.selected_order:
            return
        target_idx = (event.x - self.THUMB_MARGIN) // (self.THUMB_SIZE + self.THUMB_MARGIN)
        target_idx = max(0, min(target_idx, len(self.selected_order) - 1))

        start_idx = self.drag_data["start_idx"]
        if target_idx != start_idx:
            self.selected_order[start_idx], self.selected_order[target_idx] = \
                self.selected_order[target_idx], self.selected_order[start_idx]
            self.drag_data["start_idx"] = target_idx
            self._draw_thumbnails()

    def _on_thumb_release(self, event):
        """缩略图拖拽结束"""
        if self.drag_data["item"] is not None:
            if self.stitch_result is not None and len(self.selected_order) >= 2:
                self.after(50, self._update_stitch_preview)
        self.drag_data = {"item": None, "x": 0, "start_idx": None}

    # ========== 预览与拼接 ==========

    def _get_selected_infos(self) -> List[ImageInfo]:
        """获取选中的图片列表（按缩略图排序顺序）"""
        return [self.image_infos[idx] for idx in self.selected_order]

    def _show_preview_hint(self, text: str):
        """在预览区显示提示文字"""
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
            fill=COLORS["hint"]
        )
        self.info_label.config(text="")

    def _update_stitch_preview(self):
        """执行拼接并更新预览"""
        self._stop_stitch_animation()

        selected = self._get_selected_infos()
        if len(selected) < 2:
            self._show_preview_hint("Select at least 2 images")
            self.stitch_result = None
            return

        try:
            height_mode = HeightMode(self.height_mode_var.get())
            spacing = self.spacing_var.get()
            sync_mode = SyncMode(self.sync_mode_var.get())
            direction = Direction(self.direction_var.get())

            stitcher = ImageStitcher(
                spacing=spacing,
                height_mode=height_mode,
                sync_mode=sync_mode,
                direction=direction,
            )
            self.stitch_result = stitcher.stitch(selected)

            if self.stitch_result.is_animated and len(self.stitch_result.frames) > 1:
                self._prepare_and_play_animation()
            else:
                self._show_static_preview()

            # 更新信息
            dir_str = "H" if direction == Direction.HORIZONTAL else "V"
            if self.stitch_result.is_animated:
                fmt_str = f"GIF ({len(self.stitch_result.frames)} frames)"
            else:
                fmt_str = "PNG (Static)"
            self.info_label.config(
                text=f"{len(selected)} images  |  {self.stitch_result.width} x {self.stitch_result.height}  |  {dir_str}  |  {fmt_str}"
            )

        except Exception as e:
            self._show_preview_hint(f"Error: {e}")
            self.stitch_result = None

    def _prepare_and_play_animation(self):
        """准备并播放动画预览"""
        if not self.stitch_result:
            return

        self.preview_canvas.update_idletasks()
        canvas_w = self.preview_canvas.winfo_width() or self.PREVIEW_MAX_WIDTH
        canvas_h = self.preview_canvas.winfo_height() or self.PREVIEW_MAX_HEIGHT

        self.stitch_animation_frames = []
        for frame in self.stitch_result.frames:
            scaled = self._scale_frame(frame, canvas_w, canvas_h)
            self.stitch_animation_frames.append(ImageTk.PhotoImage(scaled))

        self.stitch_animation_durations = self.stitch_result.durations.copy()
        self.stitch_current_frame_idx = 0
        self._play_stitch_animation()

    def _show_static_preview(self):
        """显示静态预览"""
        if not self.stitch_result:
            return

        self.preview_canvas.update_idletasks()
        canvas_w = self.preview_canvas.winfo_width() or self.PREVIEW_MAX_WIDTH
        canvas_h = self.preview_canvas.winfo_height() or self.PREVIEW_MAX_HEIGHT

        frame = self._scale_frame(self.stitch_result.frames[0], canvas_w, canvas_h)
        self.preview_image = ImageTk.PhotoImage(frame)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_w // 2, canvas_h // 2,
            image=self.preview_image, anchor=tk.CENTER
        )

    def _scale_frame(self, frame: Image.Image, max_w: int, max_h: int) -> Image.Image:
        """缩放帧以适应预览区域"""
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")
        w, h = frame.size
        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            new_size = (int(w * scale), int(h * scale))
            frame = frame.resize(new_size, Image.Resampling.LANCZOS)
        return frame

    def _play_stitch_animation(self):
        """播放拼接结果动画"""
        if not self.stitch_animation_frames:
            return

        if self.stitch_current_frame_idx >= len(self.stitch_animation_frames):
            self.stitch_current_frame_idx = 0

        canvas_w = self.preview_canvas.winfo_width() or self.PREVIEW_MAX_WIDTH
        canvas_h = self.preview_canvas.winfo_height() or self.PREVIEW_MAX_HEIGHT

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_w // 2, canvas_h // 2,
            image=self.stitch_animation_frames[self.stitch_current_frame_idx],
            anchor=tk.CENTER
        )

        delay = max(self.stitch_animation_durations[self.stitch_current_frame_idx], 10)
        self.stitch_animation_id = self.after(delay, self._play_stitch_animation)
        self.stitch_current_frame_idx += 1

    def _stop_stitch_animation(self):
        """停止动画播放"""
        if self.stitch_animation_id:
            self.after_cancel(self.stitch_animation_id)
            self.stitch_animation_id = None
        self.stitch_animation_frames = []
        self.stitch_current_frame_idx = 0

    # ========== 导出 ==========

    def _export(self):
        """导出拼接结果"""
        if not self.stitch_result:
            messagebox.showwarning("Warning", "Please click Preview first to generate result")
            return

        if self.stitch_result.is_animated:
            fmt = OutputFormat.GIF
            ext = ".gif"
            filetypes = [("GIF Files", "*.gif"), ("All Files", "*.*")]
        else:
            fmt = OutputFormat.PNG
            ext = ".png"
            filetypes = [("PNG Files", "*.png"), ("All Files", "*.*")]

        output_path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=ext,
            filetypes=filetypes,
        )

        if not output_path:
            return

        try:
            # 确保最小帧时长 20ms（GIF 兼容性）
            export_durations = [max(d, 20) for d in self.stitch_result.durations]

            export_result = StitchResult(
                frames=self.stitch_result.frames,
                durations=export_durations,
                is_animated=self.stitch_result.is_animated,
                width=self.stitch_result.width,
                height=self.stitch_result.height,
            )

            exporter = Exporter(format=fmt, loop=0)
            result_path = exporter.export(export_result, output_path)
            messagebox.showinfo("Success", f"Exported to:\n{result_path}")
            self._on_close()

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _on_close(self):
        """窗口关闭处理"""
        self._stop_stitch_animation()
        self.destroy()

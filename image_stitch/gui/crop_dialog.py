"""
图片剪裁对话框模块

支持：
- 鼠标拖拽创建选择区域
- 拖拽选择框内部移动位置
- 拖拽边角/边缘调整大小
- 动画图片的帧播放预览
- 直接保存/另存为裁剪结果
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Callable
from pathlib import Path
from PIL import Image, ImageTk

from ..core.image_loader import ImageInfo
from ..core.cropper import ImageCropper, CropBox
from ..core.exporter import Exporter
from .theme import COLORS, FONTS, SIZES


class CropDialog(tk.Toplevel):
    """
    图片剪裁对话框

    支持：
    - 鼠标拖拽创建选择区域
    - 拖拽选择框内部移动位置
    - 拖拽边角/边缘调整大小
    - 动态图片播放预览
    - 保存/另存为裁剪结果
    """

    # 画布最大尺寸
    CANVAS_MAX_SIZE = 600
    # 控制柄大小
    HANDLE_SIZE = SIZES["handle_size"]
    # 边缘检测范围
    EDGE_THRESHOLD = SIZES["edge_threshold"]

    # 操作模式常量
    MODE_NONE = "none"
    MODE_CREATE = "create"
    MODE_MOVE = "move"
    MODE_RESIZE_NW = "resize_nw"
    MODE_RESIZE_N = "resize_n"
    MODE_RESIZE_NE = "resize_ne"
    MODE_RESIZE_W = "resize_w"
    MODE_RESIZE_E = "resize_e"
    MODE_RESIZE_SW = "resize_sw"
    MODE_RESIZE_S = "resize_s"
    MODE_RESIZE_SE = "resize_se"

    def __init__(
        self,
        parent: tk.Tk,
        image_info: ImageInfo,
        callback: Callable[[ImageInfo, CropBox], None]
    ):
        """
        初始化剪裁对话框

        参数:
            parent: 父窗口
            image_info: 要剪裁的图片信息
            callback: 剪裁完成后的回调函数，接收 (ImageInfo, CropBox) 参数
        """
        super().__init__(parent)
        self.parent = parent
        self.image_info = image_info
        self.callback = callback
        self.cropper = ImageCropper()

        # 剪裁状态
        self.scale = 1.0
        self.canvas_w = 0
        self.canvas_h = 0

        # 选择框状态（显示坐标）
        self.sel_x1 = 0
        self.sel_y1 = 0
        self.sel_x2 = 0
        self.sel_y2 = 0
        self.has_selection = False

        # 拖拽状态
        self.mode = self.MODE_NONE
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_orig_x1 = 0
        self.drag_orig_y1 = 0
        self.drag_orig_x2 = 0
        self.drag_orig_y2 = 0

        # 动画播放状态
        self.crop_animation_id: Optional[str] = None
        self.crop_animation_frames: List[ImageTk.PhotoImage] = []
        self.crop_animation_durations: List[int] = []
        self.crop_current_frame_idx: int = 0

        # 静态图片显示引用（防止被垃圾回收）
        self.display_image: Optional[ImageTk.PhotoImage] = None

        self._setup_window()
        self._create_widgets()
        self._display_image()
        self._bind_events()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        """设置窗口属性"""
        self.title(f"Crop: {Path(self.image_info.path).name}")
        self.transient(self.parent)
        self.grab_set()
        self.configure(bg=COLORS["bg"])

        # 计算窗口大小
        img_w, img_h = self.image_info.width, self.image_info.height
        self.scale = min(self.CANVAS_MAX_SIZE / img_w, self.CANVAS_MAX_SIZE / img_h, 1.0)
        self.canvas_w = int(img_w * self.scale)
        self.canvas_h = int(img_h * self.scale)

        win_w = max(self.canvas_w + 40, 480)
        win_h = self.canvas_h + 160
        self.geometry(f"{win_w}x{win_h}")
        self.resizable(False, False)

    def _create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self, padding=SIZES["padding"])
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 提示标签
        self.hint_label = ttk.Label(
            main_frame,
            text="Drag to select  |  Drag inside to move  |  Drag edges to resize",
            style="Small.TLabel",
        )
        self.hint_label.pack(pady=(0, 6))

        # 画布区域
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_w,
            height=self.canvas_h,
            bg="#2D3748",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            cursor="crosshair"
        )
        self.canvas.pack()

        # 信息标签
        self.info_label = ttk.Label(
            main_frame,
            text=f"Original: {self.image_info.width} x {self.image_info.height}  |  Click and drag to select area",
            style="Info.TLabel",
        )
        self.info_label.pack(pady=(6, 0))

        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(8, 6))

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="Reset", command=self._reset_selection, width=9).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(
            btn_frame, text="Confirm", command=self._confirm_crop,
            width=10, style="Primary.TButton"
        ).pack(side=tk.LEFT, padx=4)

        # 分隔符
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(btn_frame, text="Save", command=self._save_crop, width=9).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="Save As", command=self._save_as_crop, width=9).pack(
            side=tk.LEFT, padx=4
        )

        # 分隔符
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(btn_frame, text="Cancel", command=self._on_close, width=9).pack(
            side=tk.LEFT, padx=4
        )

    def _display_image(self):
        """显示图片（支持动画）"""
        if self.image_info.is_animated and self.image_info.n_frames > 1:
            # 动画图片
            self.crop_animation_frames = []
            for frame in self.image_info.frames:
                if frame.mode != "RGBA":
                    frame = frame.convert("RGBA")
                if self.scale < 1.0:
                    new_size = (int(frame.width * self.scale), int(frame.height * self.scale))
                    frame = frame.resize(new_size, Image.Resampling.LANCZOS)
                self.crop_animation_frames.append(ImageTk.PhotoImage(frame))
            self.crop_animation_durations = self.image_info.durations.copy()
            self.crop_current_frame_idx = 0
            self._play_crop_animation()
        else:
            # 静态图片
            frame = self.image_info.frames[0].copy()
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            if self.scale < 1.0:
                new_size = (int(frame.width * self.scale), int(frame.height * self.scale))
                frame = frame.resize(new_size, Image.Resampling.LANCZOS)
            self.display_image = ImageTk.PhotoImage(frame)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image, tags="bg_image")

    def _play_crop_animation(self):
        """播放剪裁预览动画"""
        if not self.crop_animation_frames:
            return

        if self.crop_current_frame_idx >= len(self.crop_animation_frames):
            self.crop_current_frame_idx = 0

        self.canvas.delete("bg_image")
        self.canvas.create_image(
            0, 0, anchor=tk.NW,
            image=self.crop_animation_frames[self.crop_current_frame_idx],
            tags="bg_image"
        )

        # 确保选择框在最上层
        self.canvas.tag_raise("overlay")
        self.canvas.tag_raise("selection")
        self.canvas.tag_raise("handles")

        delay = max(self.crop_animation_durations[self.crop_current_frame_idx], 20)
        self.crop_animation_id = self.after(delay, self._play_crop_animation)
        self.crop_current_frame_idx += 1

    def _stop_crop_animation(self):
        """停止动画播放"""
        if self.crop_animation_id:
            self.after_cancel(self.crop_animation_id)
            self.crop_animation_id = None

    def _on_close(self):
        """窗口关闭处理"""
        self._stop_crop_animation()
        self.destroy()

    # ========== 事件绑定与处理 ==========

    def _bind_events(self):
        """绑定鼠标事件"""
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)

    def _get_handle_at(self, x: int, y: int) -> str:
        """
        检测鼠标位置对应的操作模式

        参数:
            x, y: 鼠标坐标

        返回:
            操作模式字符串
        """
        if not self.has_selection:
            return self.MODE_CREATE

        hs = self.HANDLE_SIZE
        et = self.EDGE_THRESHOLD
        x1, y1, x2, y2 = self.sel_x1, self.sel_y1, self.sel_x2, self.sel_y2

        # 角落
        if abs(x - x1) <= hs and abs(y - y1) <= hs:
            return self.MODE_RESIZE_NW
        if abs(x - x2) <= hs and abs(y - y1) <= hs:
            return self.MODE_RESIZE_NE
        if abs(x - x1) <= hs and abs(y - y2) <= hs:
            return self.MODE_RESIZE_SW
        if abs(x - x2) <= hs and abs(y - y2) <= hs:
            return self.MODE_RESIZE_SE

        # 边缘
        if abs(x - x1) <= et and y1 < y < y2:
            return self.MODE_RESIZE_W
        if abs(x - x2) <= et and y1 < y < y2:
            return self.MODE_RESIZE_E
        if abs(y - y1) <= et and x1 < x < x2:
            return self.MODE_RESIZE_N
        if abs(y - y2) <= et and x1 < x < x2:
            return self.MODE_RESIZE_S

        # 内部（移动）
        if x1 < x < x2 and y1 < y < y2:
            return self.MODE_MOVE

        # 外部（创建新选择）
        return self.MODE_CREATE

    def _update_cursor(self, mode: str):
        """根据模式更新鼠标光标"""
        cursor_map = {
            self.MODE_NONE: "crosshair",
            self.MODE_CREATE: "crosshair",
            self.MODE_MOVE: "fleur",
            self.MODE_RESIZE_NW: "top_left_corner",
            self.MODE_RESIZE_N: "sb_v_double_arrow",
            self.MODE_RESIZE_NE: "top_right_corner",
            self.MODE_RESIZE_W: "sb_h_double_arrow",
            self.MODE_RESIZE_E: "sb_h_double_arrow",
            self.MODE_RESIZE_SW: "bottom_left_corner",
            self.MODE_RESIZE_S: "sb_v_double_arrow",
            self.MODE_RESIZE_SE: "bottom_right_corner",
        }
        self.canvas.config(cursor=cursor_map.get(mode, "crosshair"))

    def _on_motion(self, event):
        """鼠标悬停"""
        mode = self._get_handle_at(event.x, event.y)
        self._update_cursor(mode)

    def _on_press(self, event):
        """鼠标按下"""
        self.mode = self._get_handle_at(event.x, event.y)
        self.drag_start_x = event.x
        self.drag_start_y = event.y

        if self.mode == self.MODE_CREATE:
            self.sel_x1 = event.x
            self.sel_y1 = event.y
            self.sel_x2 = event.x
            self.sel_y2 = event.y
            self.has_selection = True
        else:
            self.drag_orig_x1 = self.sel_x1
            self.drag_orig_y1 = self.sel_y1
            self.drag_orig_x2 = self.sel_x2
            self.drag_orig_y2 = self.sel_y2

    def _on_drag(self, event):
        """鼠标拖拽"""
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        if self.mode == self.MODE_CREATE:
            self.sel_x2 = max(0, min(event.x, self.canvas_w))
            self.sel_y2 = max(0, min(event.y, self.canvas_h))

        elif self.mode == self.MODE_MOVE:
            w = self.drag_orig_x2 - self.drag_orig_x1
            h = self.drag_orig_y2 - self.drag_orig_y1
            new_x1 = max(0, min(self.drag_orig_x1 + dx, self.canvas_w - w))
            new_y1 = max(0, min(self.drag_orig_y1 + dy, self.canvas_h - h))
            self.sel_x1 = new_x1
            self.sel_y1 = new_y1
            self.sel_x2 = new_x1 + w
            self.sel_y2 = new_y1 + h

        elif self.mode.startswith("resize_"):
            self._resize_selection(dx, dy)

        self._draw_selection()

    def _resize_selection(self, dx: int, dy: int):
        """调整选择框大小"""
        min_size = 20

        x1, y1 = self.drag_orig_x1, self.drag_orig_y1
        x2, y2 = self.drag_orig_x2, self.drag_orig_y2

        if self.mode == self.MODE_RESIZE_NW:
            x1 = max(0, min(x1 + dx, x2 - min_size))
            y1 = max(0, min(y1 + dy, y2 - min_size))
        elif self.mode == self.MODE_RESIZE_N:
            y1 = max(0, min(y1 + dy, y2 - min_size))
        elif self.mode == self.MODE_RESIZE_NE:
            x2 = max(x1 + min_size, min(x2 + dx, self.canvas_w))
            y1 = max(0, min(y1 + dy, y2 - min_size))
        elif self.mode == self.MODE_RESIZE_W:
            x1 = max(0, min(x1 + dx, x2 - min_size))
        elif self.mode == self.MODE_RESIZE_E:
            x2 = max(x1 + min_size, min(x2 + dx, self.canvas_w))
        elif self.mode == self.MODE_RESIZE_SW:
            x1 = max(0, min(x1 + dx, x2 - min_size))
            y2 = max(y1 + min_size, min(y2 + dy, self.canvas_h))
        elif self.mode == self.MODE_RESIZE_S:
            y2 = max(y1 + min_size, min(y2 + dy, self.canvas_h))
        elif self.mode == self.MODE_RESIZE_SE:
            x2 = max(x1 + min_size, min(x2 + dx, self.canvas_w))
            y2 = max(y1 + min_size, min(y2 + dy, self.canvas_h))

        self.sel_x1, self.sel_y1 = x1, y1
        self.sel_x2, self.sel_y2 = x2, y2

    def _on_release(self, event):
        """鼠标释放"""
        if self.sel_x1 > self.sel_x2:
            self.sel_x1, self.sel_x2 = self.sel_x2, self.sel_x1
        if self.sel_y1 > self.sel_y2:
            self.sel_y1, self.sel_y2 = self.sel_y2, self.sel_y1

        if self.sel_x2 - self.sel_x1 < 10 or self.sel_y2 - self.sel_y1 < 10:
            self.has_selection = False

        self.mode = self.MODE_NONE
        self._draw_selection()

    # ========== 绘制相关 ==========

    def _draw_selection(self):
        """绘制选择框和控制柄"""
        self.canvas.delete("selection")
        self.canvas.delete("overlay")
        self.canvas.delete("handles")

        if not self.has_selection:
            self._update_info()
            return

        x1, y1 = min(self.sel_x1, self.sel_x2), min(self.sel_y1, self.sel_y2)
        x2, y2 = max(self.sel_x1, self.sel_x2), max(self.sel_y1, self.sel_y2)

        # 半透明遮罩
        self._draw_overlay(x1, y1, x2, y2)

        # 选择框边框（绿色）
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline=COLORS["crop_border"],
            width=2,
            tags="selection"
        )

        # 控制柄（8个白色小方块）
        hs = self.HANDLE_SIZE // 2
        handle_positions = [
            (x1, y1), ((x1 + x2) // 2, y1), (x2, y1),
            (x1, (y1 + y2) // 2),            (x2, (y1 + y2) // 2),
            (x1, y2), ((x1 + x2) // 2, y2), (x2, y2),
        ]

        for hx, hy in handle_positions:
            self.canvas.create_rectangle(
                hx - hs, hy - hs, hx + hs, hy + hs,
                fill=COLORS["crop_handle"],
                outline=COLORS["crop_border"],
                width=1,
                tags="handles"
            )

        self._update_info()

    def _draw_overlay(self, x1: int, y1: int, x2: int, y2: int):
        """绘制半透明遮罩"""
        overlay_color = COLORS["overlay"]
        stipple = "gray50"

        if y1 > 0:
            self.canvas.create_rectangle(
                0, 0, self.canvas_w, y1,
                fill=overlay_color, stipple=stipple, outline="", tags="overlay"
            )
        if y2 < self.canvas_h:
            self.canvas.create_rectangle(
                0, y2, self.canvas_w, self.canvas_h,
                fill=overlay_color, stipple=stipple, outline="", tags="overlay"
            )
        if x1 > 0:
            self.canvas.create_rectangle(
                0, y1, x1, y2,
                fill=overlay_color, stipple=stipple, outline="", tags="overlay"
            )
        if x2 < self.canvas_w:
            self.canvas.create_rectangle(
                x2, y1, self.canvas_w, y2,
                fill=overlay_color, stipple=stipple, outline="", tags="overlay"
            )

    def _update_info(self):
        """更新信息标签"""
        if not self.has_selection:
            self.info_label.config(
                text=f"Original: {self.image_info.width} x {self.image_info.height}  |  Click and drag to select area"
            )
            return

        x1, y1 = min(self.sel_x1, self.sel_x2), min(self.sel_y1, self.sel_y2)
        x2, y2 = max(self.sel_x1, self.sel_x2), max(self.sel_y1, self.sel_y2)

        real_x1 = int(x1 / self.scale)
        real_y1 = int(y1 / self.scale)
        real_x2 = int(x2 / self.scale)
        real_y2 = int(y2 / self.scale)
        width = real_x2 - real_x1
        height = real_y2 - real_y1

        self.info_label.config(
            text=f"Selection: ({real_x1}, {real_y1}) to ({real_x2}, {real_y2})  |  Size: {width} x {height}"
        )

    # ========== 剪裁操作 ==========

    def _reset_selection(self):
        """重置选择"""
        self.has_selection = False
        self.sel_x1 = self.sel_y1 = self.sel_x2 = self.sel_y2 = 0
        self.canvas.delete("selection")
        self.canvas.delete("overlay")
        self.canvas.delete("handles")
        self._update_info()

    def _get_crop_box(self) -> Optional[CropBox]:
        """获取当前选区的CropBox（实际坐标）"""
        if not self.has_selection:
            return None

        x1, y1 = min(self.sel_x1, self.sel_x2), min(self.sel_y1, self.sel_y2)
        x2, y2 = max(self.sel_x1, self.sel_x2), max(self.sel_y1, self.sel_y2)

        return CropBox(
            int(x1 / self.scale),
            int(y1 / self.scale),
            int(x2 / self.scale),
            int(y2 / self.scale),
        )

    def _confirm_crop(self):
        """确认剪裁（返回到主窗口）"""
        if not self.has_selection:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return

        crop_box = self._get_crop_box()
        if crop_box is None:
            return

        try:
            cropped_info = self.cropper.crop(self.image_info, crop_box)
            self._stop_crop_animation()
            self.callback(cropped_info, crop_box)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Crop failed: {e}")

    def _save_crop(self):
        """保存剪裁结果（覆盖原文件）"""
        if not self.has_selection:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return

        crop_box = self._get_crop_box()
        if crop_box is None:
            return

        original_path = Path(self.image_info.path)
        result = messagebox.askyesno(
            "Confirm Overwrite",
            f"Overwrite the original file?\n\n{original_path.name}\n\nThis cannot be undone."
        )
        if not result:
            return

        try:
            cropped_info = self.cropper.crop(self.image_info, crop_box)
            exporter = Exporter()
            exporter.export_image_info(cropped_info, str(original_path))
            messagebox.showinfo("Success", f"Saved to:\n{original_path}")
            self._stop_crop_animation()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def _save_as_crop(self):
        """另存为剪裁结果"""
        if not self.has_selection:
            messagebox.showwarning("Warning", "Please select a crop area first")
            return

        crop_box = self._get_crop_box()
        if crop_box is None:
            return

        original_path = Path(self.image_info.path)
        default_name = f"{original_path.stem}_cropped{original_path.suffix}"

        filetypes = [
            ("PNG Files", "*.png"),
            ("GIF Files", "*.gif"),
            ("JPEG Files", "*.jpg *.jpeg"),
            ("WebP Files", "*.webp"),
            ("All Files", "*.*"),
        ]

        save_path = filedialog.asksaveasfilename(
            title="Save Cropped Image As",
            initialdir=original_path.parent,
            initialfile=default_name,
            filetypes=filetypes,
            defaultextension=original_path.suffix,
        )

        if not save_path:
            return

        try:
            cropped_info = self.cropper.crop(self.image_info, crop_box)
            exporter = Exporter()
            exporter.export_image_info(cropped_info, save_path)
            messagebox.showinfo("Success", f"Saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

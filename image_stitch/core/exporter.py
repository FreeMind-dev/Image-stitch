"""
导出模块

支持将拼接结果导出为多种格式：
- PNG: 静态图片
- JPEG: 静态图片（有损压缩）
- GIF: 动态图片（256色限制）
- APNG: 动态PNG（全彩色）
- WebP: 动态或静态（高压缩率）

也支持从 ImageInfo 直接导出（用于裁剪保存等场景）。
"""

from enum import Enum
from typing import List, Optional
from pathlib import Path
from PIL import Image

from .stitcher import StitchResult


class OutputFormat(Enum):
    """
    输出格式

    AUTO: 自动检测（静态用PNG，动态用GIF）
    PNG: PNG格式
    JPEG: JPEG格式
    GIF: GIF格式
    APNG: 动态PNG格式
    WEBP: WebP格式
    """
    AUTO = "auto"
    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    APNG = "apng"
    WEBP = "webp"


class Exporter:
    """
    导出器

    将拼接结果导出为指定格式的文件。

    使用示例:
        >>> exporter = Exporter(format=OutputFormat.GIF)
        >>> exporter.export(result, "output.gif")
    """

    def __init__(
        self,
        format: OutputFormat = OutputFormat.AUTO,
        quality: int = 85,
        optimize_palette: bool = True,
        loop: int = 0,
    ):
        """
        初始化导出器

        参数:
            format: 输出格式
            quality: 图片质量（1-100），用于 JPEG/WebP
            optimize_palette: 是否优化 GIF 调色板
            loop: 动画循环次数，0 表示无限循环
        """
        self.format = format
        self.quality = quality
        self.optimize_palette = optimize_palette
        self.loop = loop

    def export(self, result: StitchResult, output_path: str) -> str:
        """
        导出拼接结果

        参数:
            result: StitchResult 对象
            output_path: 输出文件路径

        返回:
            实际输出的文件路径
        """
        output_path = Path(output_path)

        # 确定输出格式
        fmt = self._determine_format(result, output_path)
        self._validate_format(result, fmt)

        # 创建输出目录
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 根据格式导出
        if result.is_animated:
            return self._export_animated(result, output_path, fmt)
        else:
            return self._export_static(result.frames[0], output_path, fmt)

    def _validate_format(self, result: StitchResult, fmt: OutputFormat) -> None:
        """
        验证结果类型与输出格式是否兼容
        """
        if result.is_animated and fmt in (OutputFormat.PNG, OutputFormat.JPEG):
            raise ValueError("动画结果不支持导出为 PNG/JPEG，请使用 GIF、APNG、WebP 或 auto")

    def export_image_info(self, info, output_path: str) -> str:
        """
        从 ImageInfo 直接导出图片（用于裁剪保存等场景）

        将 ImageInfo 转换为 StitchResult 后导出，避免 duck typing 隐患。

        参数:
            info: ImageInfo 对象
            output_path: 输出文件路径

        返回:
            实际输出的文件路径
        """
        result = StitchResult(
            frames=info.frames,
            durations=info.durations,
            is_animated=info.is_animated,
            width=info.width,
            height=info.height,
        )
        return self.export(result, output_path)

    def _determine_format(self, result: StitchResult, output_path: Path) -> OutputFormat:
        """
        确定输出格式

        参数:
            result: StitchResult 对象
            output_path: 输出路径

        返回:
            OutputFormat 枚举值
        """
        if self.format != OutputFormat.AUTO:
            return self.format

        # 根据文件扩展名判断
        suffix = output_path.suffix.lower()
        suffix_map = {
            ".png": OutputFormat.APNG if result.is_animated else OutputFormat.PNG,
            ".gif": OutputFormat.GIF,
            ".webp": OutputFormat.WEBP,
            ".jpg": OutputFormat.JPEG,
            ".jpeg": OutputFormat.JPEG,
        }

        if suffix in suffix_map:
            return suffix_map[suffix]

        # 默认：静态用 PNG，动态用 GIF
        return OutputFormat.GIF if result.is_animated else OutputFormat.PNG

    def _export_static(
        self, image: Image.Image, output_path: Path, fmt: OutputFormat
    ) -> str:
        """
        导出静态图片

        参数:
            image: PIL Image 对象
            output_path: 输出路径
            fmt: 输出格式

        返回:
            实际输出的文件路径
        """
        # 调整扩展名
        if fmt == OutputFormat.PNG:
            output_path = output_path.with_suffix(".png")
            image.save(str(output_path), format="PNG", optimize=True)
        elif fmt == OutputFormat.JPEG:
            output_path = output_path.with_suffix(".jpg")
            # JPEG 不支持透明，转为 RGB
            if image.mode == "RGBA":
                bg = Image.new("RGB", image.size, (255, 255, 255))
                bg.paste(image, mask=image.split()[3])
                image = bg
            image.save(str(output_path), format="JPEG", quality=self.quality, optimize=True)
        elif fmt == OutputFormat.GIF:
            output_path = output_path.with_suffix(".gif")
            image = image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
            image.save(str(output_path), format="GIF", optimize=True)
        elif fmt == OutputFormat.APNG:
            output_path = output_path.with_suffix(".png")
            image.save(str(output_path), format="PNG", optimize=True)
        elif fmt == OutputFormat.WEBP:
            output_path = output_path.with_suffix(".webp")
            image.save(str(output_path), format="WEBP", quality=self.quality)
        else:
            # 默认 PNG
            output_path = output_path.with_suffix(".png")
            image.save(str(output_path), format="PNG", optimize=True)

        return str(output_path)

    def _export_animated(
        self, result: StitchResult, output_path: Path, fmt: OutputFormat
    ) -> str:
        """
        导出动态图片

        参数:
            result: StitchResult 对象
            output_path: 输出路径
            fmt: 输出格式

        返回:
            实际输出的文件路径
        """
        if fmt == OutputFormat.GIF:
            return self._export_gif(result, output_path)
        elif fmt == OutputFormat.APNG:
            return self._export_apng(result, output_path)
        elif fmt == OutputFormat.WEBP:
            return self._export_webp(result, output_path)
        else:
            # 默认 GIF
            return self._export_gif(result, output_path)

    def _export_gif(self, result: StitchResult, output_path: Path) -> str:
        """
        导出 GIF 格式

        参数:
            result: StitchResult 对象
            output_path: 输出路径

        返回:
            实际输出的文件路径
        """
        output_path = output_path.with_suffix(".gif")

        # 转换为调色板模式
        if self.optimize_palette:
            frames = self._optimize_gif_palette_global(result.frames)
        else:
            frames = [
                frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
                for frame in result.frames
            ]

        # 保存 GIF（启用优化减小文件大小）
        frames[0].save(
            str(output_path),
            save_all=True,
            append_images=frames[1:] if len(frames) > 1 else [],
            duration=result.durations,
            loop=self.loop,
            disposal=2,  # 恢复到背景
            optimize=True,
        )

        return str(output_path)

    def _export_apng(self, result: StitchResult, output_path: Path) -> str:
        """
        导出 APNG 格式

        参数:
            result: StitchResult 对象
            output_path: 输出路径

        返回:
            实际输出的文件路径
        """
        output_path = output_path.with_suffix(".png")

        # 确保所有帧为 RGBA
        frames = [
            frame.convert("RGBA") if frame.mode != "RGBA" else frame
            for frame in result.frames
        ]

        # 保存 APNG
        frames[0].save(
            str(output_path),
            format="PNG",
            save_all=True,
            append_images=frames[1:] if len(frames) > 1 else [],
            duration=result.durations,
            loop=self.loop,
            disposal=2,
        )

        return str(output_path)

    def _export_webp(self, result: StitchResult, output_path: Path) -> str:
        """
        导出 WebP 格式

        参数:
            result: StitchResult 对象
            output_path: 输出路径

        返回:
            实际输出的文件路径
        """
        output_path = output_path.with_suffix(".webp")

        # 确保所有帧为 RGBA
        frames = [
            frame.convert("RGBA") if frame.mode != "RGBA" else frame
            for frame in result.frames
        ]

        # 保存 WebP
        frames[0].save(
            str(output_path),
            format="WEBP",
            save_all=True,
            append_images=frames[1:] if len(frames) > 1 else [],
            duration=result.durations,
            loop=self.loop,
            quality=self.quality,
        )

        return str(output_path)

    def _optimize_gif_palette_global(self, frames: List[Image.Image]) -> List[Image.Image]:
        """
        使用全局调色板优化 GIF（多帧采样版本）

        从所有帧中均匀采样，生成能代表整个动画色彩分布的统一调色板，
        避免帧间颜色闪烁，同时保证后续帧颜色不会严重偏移。

        参数:
            frames: RGBA 帧列表

        返回:
            调色板模式的帧列表
        """
        if not frames:
            return []

        # 确保所有帧为 RGBA
        rgba_frames = [
            frame.convert("RGBA") if frame.mode != "RGBA" else frame
            for frame in frames
        ]

        # 均匀采样帧（最多 8 帧），覆盖动画全程的色彩变化
        n = len(rgba_frames)
        if n <= 8:
            sample_indices = list(range(n))
        else:
            step = n / 8
            sample_indices = [int(i * step) for i in range(8)]

        # 将采样帧缩小后拼成马赛克，作为调色板的采样源
        sample_size = 128
        thumbnails = []
        for idx in sample_indices:
            thumb = rgba_frames[idx].convert("RGB").copy()
            thumb.thumbnail((sample_size, sample_size))
            thumbnails.append(thumb)

        # 创建马赛克图像
        total_w = sum(t.width for t in thumbnails)
        max_h = max(t.height for t in thumbnails)
        mosaic = Image.new("RGB", (total_w, max_h), (0, 0, 0))
        x = 0
        for t in thumbnails:
            mosaic.paste(t, (x, 0))
            x += t.width

        # 从马赛克生成全局调色板
        palette_image = mosaic.quantize(
            colors=256,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )

        # 将所有帧转换为使用相同调色板
        optimized = []
        for frame in rgba_frames:
            frame_rgb = frame.convert("RGB")
            quantized = frame_rgb.quantize(
                colors=256,
                dither=Image.Dither.FLOYDSTEINBERG,
                palette=palette_image,
            )
            optimized.append(quantized)

        return optimized

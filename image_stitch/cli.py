"""
命令行接口模块

提供命令行工具入口，支持各种参数配置。
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional

from .core.image_loader import ImageLoader
from .core.stitcher import ImageStitcher, AlignMode, HeightMode, Direction
from .core.exporter import Exporter, OutputFormat
from .core.frame_sync import SyncMode


class SafeArgumentParser(argparse.ArgumentParser):
    """
    在非 UTF-8 终端/管道中安全输出帮助文本。

    Windows CI 的默认编码可能不支持中文，argparse 在打印 help/version
    时会直接抛 UnicodeEncodeError。这里降级为可编码文本，避免进程失败。
    """

    def _print_message(self, message, file=None):
        if not message:
            return

        if file is None:
            file = sys.stdout

        try:
            file.write(message)
        except UnicodeEncodeError:
            encoding = getattr(file, "encoding", None) or "utf-8"
            safe_message = message.encode(encoding, errors="backslashreplace").decode(
                encoding,
                errors="strict",
            )
            file.write(safe_message)


def parse_color(color_str: str) -> Tuple[int, int, int, int]:
    """
    解析颜色字符串

    支持格式:
        - "transparent": 透明
        - "#RRGGBB": 十六进制颜色
        - "#RRGGBBAA": 带透明度的十六进制
        - "R,G,B": RGB 值
        - "R,G,B,A": RGBA 值

    参数:
        color_str: 颜色字符串

    返回:
        (R, G, B, A) 元组
    """
    color_str = color_str.strip().lower()

    if color_str == "transparent":
        return (255, 255, 255, 0)
    elif color_str == "white":
        return (255, 255, 255, 255)
    elif color_str == "black":
        return (0, 0, 0, 255)
    elif color_str.startswith("#"):
        # 十六进制格式
        hex_str = color_str[1:]
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b, 255)
        elif len(hex_str) == 8:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            a = int(hex_str[6:8], 16)
            return (r, g, b, a)
    elif "," in color_str:
        # R,G,B 或 R,G,B,A 格式
        parts = [int(p.strip()) for p in color_str.split(",")]
        if len(parts) == 3:
            return (parts[0], parts[1], parts[2], 255)
        elif len(parts) == 4:
            return (parts[0], parts[1], parts[2], parts[3])

    raise ValueError(f"无法解析颜色: {color_str}")


def create_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器

    返回:
        ArgumentParser 对象
    """
    parser = SafeArgumentParser(
        prog="image-stitch",
        description="横向拼接图片工具，支持静态和动态图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 拼接多张 PNG
  python -m image_stitch img1.png img2.png img3.png -o output.png

  # 拼接 GIF 动画
  python -m image_stitch a.gif b.gif -o combined.gif

  # 静态 + 动态混合
  python -m image_stitch logo.png animation.gif -o result.gif

  # 完整参数
  python -m image_stitch img1.gif img2.gif -o out.gif --align center --spacing 10

  # 启动图形界面
  python -m image_stitch --gui
""",
    )

    # 位置参数
    parser.add_argument(
        "images",
        nargs="*",
        help="要拼接的图片路径（至少2个，GUI模式下可省略）",
    )

    # 输出参数
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径（必需，GUI模式下可省略）",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["auto", "png", "jpeg", "gif", "apng", "webp"],
        default="auto",
        help="输出格式，auto 自动检测（默认: auto）",
    )

    # 高度模式参数
    parser.add_argument(
        "--height-mode",
        choices=["max", "min"],
        default="max",
        help="高度基准模式：max=以最高图片为准放大，min=以最矮图片为准缩小（默认: max）",
    )
    parser.add_argument(
        "--align",
        choices=["top", "center", "bottom"],
        default="center",
        help="垂直对齐方式，仅当不缩放时使用（默认: center）",
    )
    parser.add_argument(
        "--spacing",
        type=int,
        default=0,
        help="图片间距（像素，默认: 0）",
    )
    parser.add_argument(
        "--bg-color",
        default="transparent",
        help="背景颜色，支持 transparent、#RRGGBB、R,G,B 格式（默认: transparent）",
    )

    # 拼接方向参数
    parser.add_argument(
        "--direction",
        choices=["horizontal", "vertical"],
        default="horizontal",
        help="拼接方向：horizontal=水平(默认), vertical=垂直",
    )

    # 动画同步参数
    parser.add_argument(
        "--sync-mode",
        choices=["time_sync", "loop", "longest", "shortest", "lcm"],
        default="time_sync",
        help="帧同步模式：time_sync=独立循环(推荐), loop=简单循环, longest=最长优先, shortest=最短优先, lcm=精确同步（默认: time_sync）",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=300,
        help="最大帧数限制（默认: 300）",
    )

    # 质量参数
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="输出质量 1-100，用于 JPEG/WebP（默认: 85）",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="禁用 GIF 调色板优化",
    )
    parser.add_argument(
        "--loop",
        type=int,
        default=0,
        help="动画循环次数，0 表示无限（默认: 0）",
    )

    # 模式切换
    parser.add_argument(
        "--gui",
        action="store_true",
        help="启动图形界面（默认无参数时启动GUI）",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="强制使用命令行模式",
    )

    # 其他
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细信息",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.1.0",
    )

    return parser


def run_cli(args: argparse.Namespace) -> int:
    """
    运行命令行模式

    参数:
        args: 解析后的命令行参数

    返回:
        退出码（0 表示成功）
    """
    # 验证参数
    if len(args.images) < 2:
        print("错误: 至少需要 2 张图片", file=sys.stderr)
        return 1

    if not args.output:
        print("错误: 必须指定输出路径 (-o/--output)", file=sys.stderr)
        return 1

    # 验证输入文件存在
    for img_path in args.images:
        if not Path(img_path).exists():
            print(f"错误: 文件不存在: {img_path}", file=sys.stderr)
            return 1

    try:
        # 解析参数
        bg_color = parse_color(args.bg_color)
        align = AlignMode(args.align)
        sync_mode = SyncMode(args.sync_mode)
        output_format = OutputFormat(args.format)
        height_mode = HeightMode(args.height_mode)
        direction = Direction(args.direction)

        # 加载图片
        if args.verbose:
            print(f"加载 {len(args.images)} 张图片...")

        loader = ImageLoader()
        images = loader.load_multiple(args.images)

        if args.verbose:
            for info in images:
                print(f"  - {info}")

        # 拼接
        if args.verbose:
            print("拼接中...")

        stitcher = ImageStitcher(
            align=align,
            spacing=args.spacing,
            bg_color=bg_color,
            sync_mode=sync_mode,
            max_frames=args.max_frames,
            height_mode=height_mode,
            direction=direction,
        )
        result = stitcher.stitch(images)

        if args.verbose:
            anim_str = f"动画, {len(result.frames)} 帧" if result.is_animated else "静态"
            print(f"  结果: {result.width}x{result.height}, {anim_str}")

        # 导出
        if args.verbose:
            print(f"导出到: {args.output}")

        exporter = Exporter(
            format=output_format,
            quality=args.quality,
            optimize_palette=not args.no_optimize,
            loop=args.loop,
        )
        output_path = exporter.export(result, args.output)

        print(f"完成: {output_path}")
        return 0

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main() -> int:
    """
    命令行入口

    返回:
        退出码
    """
    parser = create_parser()
    args = parser.parse_args()

    # GUI 模式
    if args.gui:
        try:
            from .gui import run_gui
            return run_gui()
        except ImportError as e:
            print(f"错误: 无法启动 GUI: {e}", file=sys.stderr)
            return 1

    # 命令行模式
    if not args.images:
        parser.print_help()
        return 0

    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())

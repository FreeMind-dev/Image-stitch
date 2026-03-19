"""
包入口模块

默认启动 GUI 模式，使用 --cli 参数切换到命令行模式。

用法:
    # 启动 GUI（默认）
    python -m image_stitch

    # 命令行模式
    python -m image_stitch --cli img1.png img2.png -o output.png

    # 也可以直接指定图片启动命令行模式
    python -m image_stitch img1.png img2.png -o output.png
"""

import sys


def main() -> int:
    """
    主入口函数

    根据参数决定启动 GUI 或命令行模式：
    - 无参数或仅 --gui 参数：启动 GUI
    - 有图片参数或 --cli 参数：命令行模式

    返回:
        退出码
    """
    args = sys.argv[1:]

    # 检查是否强制使用 GUI 模式
    if "--gui" in args:
        from .gui import run_gui
        return run_gui()

    # 只要用户传入了任意非 GUI 参数，都交给 argparse 处理。
    # 这样 --help / --version 以及错误参数都能按 CLI 语义正常返回。
    if args:
        from .cli import main as cli_main
        return cli_main()

    # 默认启动 GUI
    try:
        from .gui import run_gui
        return run_gui()
    except ImportError as e:
        print(f"Error: Cannot start GUI: {e}", file=sys.stderr)
        print("Use --cli for command line mode or install tkinter.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

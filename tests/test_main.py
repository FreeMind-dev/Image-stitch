"""
包入口测试

验证 `python -m image_stitch` 在 CLI 参数场景下会正确路由到 argparse，
避免错误地进入 GUI 分支导致挂起。
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestMainEntrypoint:
    """`python -m image_stitch` 路由测试"""

    def test_help_routes_to_cli(self):
        """--help 应立即输出 CLI 帮助，而不是尝试启动 GUI"""
        result = subprocess.run(
            [sys.executable, "-m", "image_stitch", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "usage: image-stitch" in result.stdout

    def test_version_routes_to_cli(self):
        """--version 应立即输出版本号"""
        result = subprocess.run(
            [sys.executable, "-m", "image_stitch", "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "image-stitch 1.1.0" in result.stdout

    def test_help_routes_to_cli_under_cp1252(self):
        """非 UTF-8 管道编码下，--help 也不应因为中文帮助文本崩溃"""
        env = dict(__import__("os").environ)
        env["PYTHONIOENCODING"] = "cp1252"

        result = subprocess.run(
            [sys.executable, "-m", "image_stitch", "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="cp1252",
            errors="replace",
            env=env,
            timeout=5,
        )

        assert result.returncode == 0
        assert "usage: image-stitch" in result.stdout

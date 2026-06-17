"""
Safe file dialog helpers for the Tk GUI.

Tk's native file dialogs can crash on some Linux/X11 setups with an xcb
assertion. Prefer zenity when it is available, then fall back to Tk for
platforms where the native dialog is stable.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which
from tkinter import filedialog
from typing import Iterable, Optional, Sequence, Union

FileType = tuple[str, str]
PathLike = Union[str, Path]


def ask_open_filenames(
    *,
    title: str,
    filetypes: Sequence[FileType],
    initialdir: Optional[PathLike] = None,
) -> tuple[str, ...]:
    """Ask the user to select one or more files."""
    zenity = which("zenity")
    if zenity:
        result = _run_zenity(
            [
                zenity,
                "--file-selection",
                "--multiple",
                "--separator=\n",
                f"--title={title}",
                *_zenity_file_filters(filetypes),
                *_zenity_initial_file(initialdir=initialdir),
            ]
        )
        if result is not None:
            return tuple(line for line in result.splitlines() if line)
        return ()

    return tuple(
        filedialog.askopenfilenames(
            title=title,
            filetypes=filetypes,
            initialdir=str(initialdir) if initialdir else None,
        )
    )


def ask_save_as_filename(
    *,
    title: str,
    filetypes: Sequence[FileType],
    initialdir: Optional[PathLike] = None,
    initialfile: Optional[str] = None,
    defaultextension: Optional[str] = None,
) -> str:
    """Ask the user for a save path."""
    zenity = which("zenity")
    if zenity:
        filename_args = _zenity_initial_file(
            initialdir=initialdir,
            initialfile=initialfile,
        )
        result = _run_zenity(
            [
                zenity,
                "--file-selection",
                "--save",
                f"--title={title}",
                *_zenity_file_filters(filetypes),
                *filename_args,
            ]
        )
        if result is not None:
            return _append_default_extension(result.strip(), defaultextension)
        return ""

    return filedialog.asksaveasfilename(
        title=title,
        filetypes=filetypes,
        initialdir=str(initialdir) if initialdir else None,
        initialfile=initialfile,
        defaultextension=defaultextension,
    )


def _run_zenity(args: Sequence[str]) -> Optional[str]:
    completed = subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode == 0:
        return completed.stdout
    if completed.returncode == 1:
        return None
    return None


def _zenity_file_filters(filetypes: Iterable[FileType]) -> list[str]:
    return [f"--file-filter={label} | {patterns}" for label, patterns in filetypes]


def _zenity_initial_file(
    *,
    initialdir: Optional[PathLike] = None,
    initialfile: Optional[str] = None,
) -> list[str]:
    if initialdir is None and initialfile is None:
        return []

    directory = Path(initialdir).expanduser() if initialdir else Path.cwd()
    if initialfile:
        filename = directory / initialfile
    else:
        filename = directory

    value = str(filename)
    if initialfile is None and not value.endswith("/"):
        value += "/"
    return [f"--filename={value}"]


def _append_default_extension(path: str, defaultextension: Optional[str]) -> str:
    if not path or not defaultextension:
        return path

    suffix = defaultextension if defaultextension.startswith(".") else f".{defaultextension}"
    if Path(path).suffix:
        return path
    return f"{path}{suffix}"

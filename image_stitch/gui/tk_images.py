"""
Tk image helpers that avoid Pillow's ImageTk extension.

Some Linux/X11 environments fail to load Pillow's _imagingtk bridge. Tk 8.6 can
display PNG data natively, so convert PIL images to in-memory PNGs instead.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Optional
import tkinter as tk

from PIL import Image


def pil_to_photo_image(image: Image.Image, master: Optional[tk.Misc] = None) -> tk.PhotoImage:
    """Convert a PIL image to a Tk PhotoImage without using PIL.ImageTk."""
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return tk.PhotoImage(master=master, data=data, format="png")

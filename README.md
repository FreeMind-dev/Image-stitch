# Image Stitch - Image Stitching Tool

A Python tool for horizontally and vertically stitching static and animated images (GIF/APNG/WebP) with proportional scaling.

**Version**: 1.1.0

## Features

- **Horizontal & Vertical Stitching**: Stitch images left-to-right or top-to-bottom
  - Static + Static → PNG/JPEG
  - Static + Dynamic → GIF/APNG/WebP
  - Dynamic + Dynamic → GIF/APNG/WebP

- **Proportional Scaling**: Automatically scales all images to uniform height (horizontal) or width (vertical) while preserving aspect ratios

- **Independent GIF Looping**: Each GIF sub-image loops at its own pace independently

- **Image Cropping**: Mouse-based crop selection for both static and animated images

- **Dual Interface**: GUI (default) and Command Line (CLI)

- **Cross-platform**: Supports Windows and Ubuntu/Linux

## Installation

### From requirements.txt

```bash
cd /path/to/Image_stitch
pip install -r requirements.txt
```

### From pyproject.toml

```bash
# Standard install
pip install .

# Editable install (for development)
pip install -e .
```

### Dependencies

- Pillow >= 10.0.0
- tkinter (GUI mode, included with standard Python; macOS Homebrew users: `brew install python-tk`)

### Platform Notes

| Platform | GUI | CLI | Notes |
|----------|-----|-----|-------|
| Linux (Ubuntu/Debian) | Yes | Yes | `sudo apt install python3-tk` if tkinter missing |
| Windows | Yes | Yes | Works out of the box with python.org installer |
| macOS | Yes | Yes | Use python.org installer or `brew install python-tk` |

## Quick Start

### GUI Mode (Default)

```bash
# Start GUI (default)
python -m image_stitch

# Or explicitly
python -m image_stitch --gui
```

### Command Line Mode

```bash
# Basic usage: stitch multiple images horizontally
python -m image_stitch img1.png img2.png img3.png -o output.png

# Stitch GIF animations
python -m image_stitch anim1.gif anim2.gif -o combined.gif

# Mixed static + dynamic stitching
python -m image_stitch logo.png animation.gif icon.png -o result.gif

# Vertical stitching
python -m image_stitch top.png bottom.png -o output.png --direction vertical

# Force CLI mode
python -m image_stitch --cli img1.png img2.png -o output.png
```

## Command Line Arguments

```
python -m image_stitch [image paths...] -o output_path [options]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `image paths` | Image files to stitch (at least 2) |
| `-o, --output` | Output file path |

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `-f, --format` | auto | Output format: auto, png, jpeg, gif, apng, webp |
| `--height-mode` | max | Height mode: max (scale up), min (scale down) |
| `--spacing` | 0 | Spacing between images (pixels) |
| `--direction` | horizontal | Stitch direction: horizontal, vertical |
| `--sync-mode` | time_sync | Frame sync: time_sync, loop, longest, shortest, lcm |
| `--max-frames` | 300 | Maximum frame limit |
| `--quality` | 85 | Output quality 1-100 (JPEG/WebP) |
| `--loop` | 0 | Animation loop count, 0=infinite |
| `--bg-color` | transparent | Background: transparent, #RRGGBB, R,G,B |
| `-v, --verbose` | - | Show detailed info |
| `--gui` | - | Launch GUI |
| `--cli` | - | Force CLI mode |

## Usage Examples

### 1. Basic Horizontal Stitching

```bash
# Stitch three PNG images side by side
python -m image_stitch photo1.png photo2.png photo3.png -o result.png -v
```

Output:
```
Loading 3 images...
  - ImageInfo(photo1.png, 100x80, static)
  - ImageInfo(photo2.png, 100x120, static)
  - ImageInfo(photo3.png, 80x100, static)
Stitching...
  Result: 346x120, Static
Done: result.png
```

### 2. GIF Animation Stitching

```bash
# Stitch two GIFs with independent looping
python -m image_stitch cat.gif dog.gif -o pets.gif
```

### 3. Mixed Static + Dynamic

```bash
# Static logo on left, animation on right
python -m image_stitch logo.png animation.gif -o banner.gif
```

### 4. Custom Spacing and Height Mode

```bash
# Use shortest image as base, add 10px spacing
python -m image_stitch img1.png img2.png img3.png \
    -o output.png \
    --height-mode min \
    --spacing 10
```

### 5. Vertical Stitching

```bash
# Stack images top to bottom
python -m image_stitch header.png content.png footer.png \
    -o output.png \
    --direction vertical

# Vertical GIF stitching with spacing
python -m image_stitch anim1.gif anim2.gif \
    -o stacked.gif \
    --direction vertical \
    --spacing 5
```

### 6. Output as APNG (High Quality)

```bash
# APNG supports full color, no 256-color limit
python -m image_stitch anim1.gif anim2.gif -o result.png -f apng
```

## Height Mode

The tool automatically scales all images proportionally to match dimensions:

**Horizontal stitching**: scales to uniform height
**Vertical stitching**: scales to uniform width

| Mode | Description | Use Case |
|------|-------------|----------|
| `max` | Scale to tallest/widest image | Need larger output |
| `min` | Scale to shortest/narrowest image | Need smaller output |

**Example (horizontal)**: Three images with heights 80, 120, 100 pixels:
- `--height-mode max`: All scaled to 120px height
- `--height-mode min`: All scaled to 80px height

**Example (vertical)**: Three images with widths 200, 300, 250 pixels:
- `--height-mode max`: All scaled to 300px width
- `--height-mode min`: All scaled to 200px width

## Vertical Stitching

Vertical mode (`--direction vertical`) stacks images from top to bottom, scaling all images to a uniform width.

Key behaviors:
- All images are proportionally scaled to match widths (controlled by `--height-mode`)
- `--height-mode max`: scale to the widest image's width (default)
- `--height-mode min`: scale to the narrowest image's width
- `--spacing` adds vertical gap between images
- Animated image support works the same as horizontal mode

```bash
# Basic vertical stitch
python -m image_stitch top.png middle.png bottom.png -o column.png --direction vertical

# Vertical with min width and spacing
python -m image_stitch img1.png img2.png -o out.png --direction vertical --height-mode min --spacing 10
```

## Frame Sync Mode

When stitching GIFs with different frame counts/durations:

| Mode | Description | Recommended For |
|------|-------------|-----------------|
| `time_sync` | Independent looping (default) | Most cases |
| `loop` | Simple frame index loop | Quick preview |
| `longest` | Match longest animation | Keep longest intact |
| `shortest` | Match shortest animation | Control duration |
| `lcm` | Use LCM for precise sync | Perfect loop cycle |

**Note**: `time_sync` mode uses the longest GIF's duration as the target duration and resamples at an adaptive frame rate (dynamically adjusted based on output length), ensuring each sub-GIF loops independently and smoothly.

## Output Format Comparison

| Format | Animation | Colors | Transparency | Size | Compatibility |
|--------|-----------|--------|--------------|------|---------------|
| PNG | No | Full | Yes | Medium | Best |
| GIF | Yes | 256 | Yes | Small | Best |
| APNG | Yes | Full | Yes | Medium | Good |
| WebP | Yes | Full | Yes | Smallest | Good |
| JPEG | No | Full | No | Small | Best |

## GUI Features

Launch GUI:
```bash
python -m image_stitch
```

Features:
1. **Add Images**: Click "Add" button or drag & drop files
2. **Reorder**: Use "Up"/"Down" buttons
3. **Crop**: Select image and click "Crop" or double-click
4. **Configure**: Set height mode, spacing, format, sync mode
5. **Preview**: Auto-updates when adding/removing images
6. **Export**: Click "Export" to save result

Keyboard Shortcuts:
- `Ctrl+O`: Add images
- `Ctrl+S`: Stitch (open stitch dialog)
- `Delete`: Remove selected image
- `Double-click`: Crop selected image

## Python API

```python
from image_stitch import ImageLoader, ImageStitcher, Exporter, HeightMode
from image_stitch.core.frame_sync import SyncMode
from image_stitch.core.stitcher import Direction

# Load images
loader = ImageLoader()
images = loader.load_multiple(["img1.png", "img2.gif", "img3.png"])

# Horizontal stitch (proportional scaling to same height)
stitcher = ImageStitcher(
    spacing=10,                    # Spacing between images
    height_mode=HeightMode.MAX,    # Scale to tallest
    sync_mode=SyncMode.TIME_SYNC,  # Independent looping
)
result = stitcher.stitch(images)

# Export
exporter = Exporter()
exporter.export(result, "output.gif")

print(f"Output size: {result.width}x{result.height}")
print(f"Frames: {len(result.frames)}")
```

### Vertical Stitching API

```python
from image_stitch import ImageLoader, ImageStitcher, Exporter, HeightMode
from image_stitch.core.stitcher import Direction

# Load images
loader = ImageLoader()
images = loader.load_multiple(["top.png", "middle.png", "bottom.png"])

# Vertical stitch (proportional scaling to same width)
stitcher = ImageStitcher(
    spacing=5,
    height_mode=HeightMode.MAX,        # Scale to widest
    direction=Direction.VERTICAL,       # Top-to-bottom
)
result = stitcher.stitch(images)

# Export
exporter = Exporter()
exporter.export(result, "column.png")
```

### Cropping API

```python
from image_stitch.core.cropper import ImageCropper, CropBox

# Create cropper
cropper = ImageCropper()

# Define crop area (x1, y1, x2, y2)
box = CropBox(10, 10, 200, 150)

# Crop image (works for both static and animated)
cropped_info = cropper.crop(image_info, box)
```

## Project Structure

```
image_stitch/
├── __init__.py           # Package init
├── __main__.py           # Entry point (GUI default)
├── cli.py                # CLI interface
├── gui.py                # Compatibility entry point
├── gui/
│   ├── __init__.py
│   ├── theme.py          # UI theme configuration
│   ├── main_window.py    # Main application window
│   ├── crop_dialog.py    # Crop selection dialog
│   └── stitch_dialog.py  # Stitch dialog with reordering
├── core/
│   ├── __init__.py
│   ├── image_loader.py   # Image loading (static/dynamic)
│   ├── frame_sync.py     # Frame sync algorithm
│   ├── stitcher.py       # Stitching logic (with scaling)
│   ├── cropper.py        # Image cropping
│   └── exporter.py       # Multi-format export
└── utils/
    └── math_utils.py     # Math utilities (GCD/LCM)
```

## FAQ

### Q: Why does the output GIF have color loss?
A: GIF format only supports 256 colors. For high-quality animation, use APNG or WebP:
```bash
python -m image_stitch a.gif b.gif -o result.png -f apng
```

### Q: Why does the output GIF have more frames?
A: This is normal behavior of the TIME_SYNC algorithm. When GIFs have different total durations, the output uses the longest GIF's duration as the target and resamples at an adaptive frame rate so each sub-GIF loops independently.

### Q: How to keep original size without scaling?
A: If all input images have the same height (horizontal mode) or width (vertical mode), no scaling occurs. Otherwise, images are scaled proportionally to match dimensions.

### Q: GIFs are playing synchronized instead of independently?
A: Use `--sync-mode time_sync` (default in latest version). This mode makes each GIF loop at its own pace.

### Q: How does vertical stitching handle height mode?
A: In vertical mode, `--height-mode` controls the target width instead of height. `max` scales all images to match the widest, `min` scales to the narrowest.

## License

MIT License

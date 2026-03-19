# Changelog

## [1.1.0] - 2025-03-19

### Added
- **Vertical stitching**: `--direction vertical` for top-to-bottom stacking
- `Direction` enum (`HORIZONTAL`, `VERTICAL`) in public API
- `AlignMode.LEFT` / `AlignMode.RIGHT` for vertical alignment control
- `Exporter.export_image_info()` method for direct ImageInfo export
- GUI sync mode selector (was hardcoded to LOOP, now defaults to TIME_SYNC)
- GUI direction selector for horizontal/vertical stitching
- Unified theme system (`gui/theme.py`) for consistent UI styling
- `Ctrl+S` keyboard shortcut to open stitch dialog
- `pyproject.toml` for `pip install .` support
- TIFF format in GUI file dialog
- Unit test suite: 149 tests across 6 modules
- LICENSE file (MIT)
- CHANGELOG.md

### Fixed
- StitchDialog hardcoded `SyncMode.LOOP` → now uses user-selected mode (default `TIME_SYNC`)
- GIF palette optimization: uses multi-frame sampling (8 evenly sampled frames) instead of first-frame only
- CropDialog save/save-as: replaced duck typing with explicit `export_image_info()` method
- README: corrected TIME_SYNC description (uses longest duration, not LCM)
- README: updated project structure to show `gui/` subpackage

### Changed
- Version bumped to 1.1.0
- GUI modernized with unified color scheme and typography
- `_scale_frame` renamed to `_scale_to_height` / `_scale_to_width` for clarity

### Removed
- `numpy` dependency (was declared but never used)

## [1.0.0] - 2025-03-18

### Added
- Initial release
- Horizontal image stitching (static + animated)
- 5 frame sync modes: TIME_SYNC, LOOP, LONGEST, SHORTEST, LCM
- Multi-format export: PNG, JPEG, GIF, APNG, WebP
- Mouse-based crop dialog with 8-direction resize handles
- Animated image preview in GUI
- Draggable thumbnail reordering in stitch dialog
- CLI with comprehensive argument support

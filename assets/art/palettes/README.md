# Palette Guide

Files:

- escape_room_level1_palette.svg: Visual swatch guide for quick review.
- escape_room_level1_palette.gpl: Importable palette file for Aseprite, GIMP, Krita (via palette import workflow), and similar tools.

Import notes:

- Aseprite: Open palette panel -> Load Palette -> select .gpl.
- GIMP: Palettes -> Import -> select .gpl.
- Krita: Settings -> Manage Resources -> Import Bundles/Palettes (tool-dependent).

Usage rules:

- Keep scene-active colors <= 24.
- Reserve high-contrast warm colors for alerts and hazards.
- Keep objective markers in cool blue family for consistency.

Why SVG instead of PNG here:

- SVG stays crisp at any zoom while preserving exact color values.
- You can export a PNG from the SVG in any editor when needed.

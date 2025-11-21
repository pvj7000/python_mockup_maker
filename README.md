# Python Mockup Maker

Batch-generate coffee shop desk mockups for your poster or paper images using Pillow. The script places your artwork onto high-resolution overlays (a table with an espresso cup) and exports web-friendly WEBP previews.

## Features
- Two ready-to-use mockup variants (30×40 cm and 60×80 cm compositions).
- Consistent scaling, rotation, and positioning to match Photoshop layouts.
- Soft multiply blending with preserved handle highlights for realistic shadows.
- Configurable input, overlay, and output directories via command-line flags.
- Verbose logging for troubleshooting.

## Requirements
- Python 3.9+
- [Pillow](https://pillow.readthedocs.io/)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Project structure
```
.
├── make_mockups3.py     # Main script
├── overlays/            # Overlay PNG assets (mockup_30x40_tr.png, mockup_60x80_tr.png)
├── input_img/           # Place your source image files here (filenames starting with "img_")
└── output2/             # Generated mockups are written here
```

## Usage
1. Add your source artwork as WEBP, PNG, or JPG/JPEG files in `input_img/` and prefix the filenames with `img_` (for example, `img_mountain.webp`). The prefix is removed in the final output names.
2. Run the script from the repository root:

```bash
python make_mockups3.py --input input_img --overlays overlays --output output2
```

Command-line options:
- `--input`: Directory containing source image files (default: `input_img`).
- `--overlays`: Directory containing overlay PNG files (default: `overlays`).
- `--output`: Directory to write generated WEBP files (default: `output2`).
- `--verbose`: Enable debug-level logging.

Each source file produces two mockups:
- `small_<name>.webp` (30×40 composition)
- `large_<name>.webp` (60×80 composition)

## Notes and customization
- Canvas and export sizes are defined at the top of `make_mockups3.py` as `CANVAS_SIZE` and `OUTPUT_SIZE`.
- Shadow strength is controlled by `SHADOW_OPACITY` (0–1 range); lower values yield softer shadows.
- Mockup positioning, rotation, and overlay filenames live in the `MOCKUPS` mapping within the script. Adjust these values if you add new overlays or need different placements.

## Licenses
- **Code**: MIT License. Copyright (c) 2025 Philip Vincent Jancsy. See [`LICENSE`](LICENSE).
- **Overlay image assets** (`overlays/`): Creative Commons Attribution 4.0 International (CC BY 4.0). Copyright (c) 2025 Philip Vincent Jancsy. See [`LICENSE_ASSETS`](LICENSE_ASSETS).

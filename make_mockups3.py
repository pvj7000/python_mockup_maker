#!/usr/bin/env python3
"""Generate coffee shop desk mockups for a batch of artwork files."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

from PIL import Image, ImageChops

DEFAULT_INPUT_FOLDER = Path("input_img")
DEFAULT_OVERLAY_FOLDER = Path("overlays")
DEFAULT_OUTPUT_FOLDER = Path("output2")

CANVAS_SIZE = (5400, 7200)
OUTPUT_SIZE = (1500, 2000)
WEBP_QUALITY = 90
SHADOW_OPACITY = 0.3
ALLOWED_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class MockupConfig:
    """Configuration for a single mockup variant."""

    overlay_filename: str
    artwork_width: int
    artwork_height: int
    artwork_x: int
    artwork_y: int
    rotation: float
    output_prefix: str


MOCKUPS: Dict[str, MockupConfig] = {
    "mockup_30x40_tr": MockupConfig(
        overlay_filename="mockup_30x40_tr.png",
        artwork_width=2554,
        artwork_height=3185,
        artwork_x=1341,
        artwork_y=2007,
        rotation=7.43,
        output_prefix="small",
    ),
    "mockup_60x80_tr": MockupConfig(
        overlay_filename="mockup_60x80_tr.png",
        artwork_width=5106,
        artwork_height=6374,
        artwork_x=144,
        artwork_y=410,
        rotation=7.3,
        output_prefix="large",
    ),
}


def _ensure_directory(path: Path) -> None:
    """Create a directory if it does not already exist."""

    path.mkdir(parents=True, exist_ok=True)


def _load_image(path: Path) -> Image.Image:
    """Load an image as RGBA, raising an informative error on failure."""

    try:
        return Image.open(path).convert("RGBA")
    except Exception as exc:  # pragma: no cover - Pillow errors are already informative
        raise ValueError(f"Failed to open artwork '{path}': {exc}") from exc


def _prepare_canvas() -> Image.Image:
    """Return a blank RGBA canvas that matches the overlay size."""

    return Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))


def _rotate_and_scale(artwork: Image.Image, config: MockupConfig) -> Image.Image:
    """Rotate artwork and scale uniformly to the configured bounding box."""

    rotated = artwork.rotate(config.rotation, resample=Image.BICUBIC, expand=True)
    scale_x = config.artwork_width / rotated.width
    scale_y = config.artwork_height / rotated.height
    scale = (scale_x + scale_y) / 2
    return rotated.resize(
        (int(rotated.width * scale), int(rotated.height * scale)), resample=Image.LANCZOS
    )


def _apply_overlay(canvas: Image.Image, overlay: Image.Image) -> Image.Image:
    """Blend an overlay with the canvas using a soft multiply and handle mask."""

    overlay_resized = overlay.resize(CANVAS_SIZE, resample=Image.LANCZOS) if overlay.size != CANVAS_SIZE else overlay

    canvas_rgb = canvas.convert("RGB")
    overlay_rgb = overlay_resized.convert("RGB")

    multiplied = ImageChops.multiply(canvas_rgb, overlay_rgb)
    soft_blend = Image.blend(canvas_rgb, multiplied, SHADOW_OPACITY)

    alpha_channel = overlay_resized.getchannel("A")
    handle_mask = alpha_channel.point(lambda alpha: 255 if alpha >= 250 else 0)

    return Image.composite(overlay_rgb, soft_blend, handle_mask)


def render_mockup(
    artwork: Image.Image,
    config: MockupConfig,
    overlay_dir: Path,
) -> Image.Image:
    """Render a single mockup for the provided artwork."""

    canvas = _prepare_canvas()
    positioned_artwork = _rotate_and_scale(artwork, config)

    desired_center_x = config.artwork_x + config.artwork_width / 2
    desired_center_y = config.artwork_y + config.artwork_height / 2
    paste_x = int(desired_center_x - positioned_artwork.width / 2)
    paste_y = int(desired_center_y - positioned_artwork.height / 2)
    canvas.paste(positioned_artwork, (paste_x, paste_y), positioned_artwork)

    overlay_path = overlay_dir / config.overlay_filename
    try:
        overlay = Image.open(overlay_path).convert("RGBA")
    except Exception as exc:  # pragma: no cover - Pillow errors are already informative
        raise ValueError(f"Failed to open overlay '{overlay_path}': {exc}") from exc

    blended = _apply_overlay(canvas, overlay)
    return blended.resize(OUTPUT_SIZE, resample=Image.LANCZOS)


def _output_name(prefix: str, source: Path) -> str:
    base_name = source.stem[4:] if source.stem.startswith("img_") else source.stem
    return f"{prefix}_{base_name}.webp"


def generate_mockups(
    input_files: Iterable[Path],
    overlay_dir: Path,
    output_dir: Path,
    mockups: Dict[str, MockupConfig] = MOCKUPS,
) -> None:
    """Generate every configured mockup for each provided artwork file."""

    _ensure_directory(output_dir)

    for image_path in input_files:
        if image_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            logging.debug("Skipping unsupported file: %s", image_path.name)
            continue

        logging.info("Processing %s", image_path.name)
        artwork = _load_image(image_path)

        for key, config in mockups.items():
            logging.debug("Rendering mockup variant %s", key)
            final_image = render_mockup(artwork, config, overlay_dir)
            output_path = output_dir / _output_name(config.output_prefix, image_path)
            final_image.save(output_path, "WEBP", quality=WEBP_QUALITY)
            logging.info("Saved %s", output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_FOLDER,
        help="Directory containing source image files (default: input_img)",
    )
    parser.add_argument(
        "--overlays",
        type=Path,
        default=DEFAULT_OVERLAY_FOLDER,
        help="Directory containing overlay PNG files (default: overlays)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FOLDER,
        help="Directory to write generated WEBP mockups (default: output2)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging.",
    )
    return parser.parse_args()


def _gather_input_files(input_dir: Path) -> Iterable[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist")

    return sorted(path for path in input_dir.iterdir() if path.is_file())


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    try:
        input_files = _gather_input_files(args.input)
    except Exception as exc:
        logging.error(exc)
        raise SystemExit(1) from exc

    try:
        generate_mockups(input_files, args.overlays, args.output)
    except Exception as exc:
        logging.error("Mockup generation failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

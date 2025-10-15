#!/usr/bin/env python3
"""
Make Mockups Script

Folder Structure:
-----------------
project_folder/
├── make_mockups3.py         # This script
├── output_webp/             # Contains your input .webp images (filenames starting with "img_")
├── overlays/                # Contains the overlay PNG files:
│      ├── mockup_30x40_tr.png
│      └── mockup_60x80_tr.png
└── output2/                 # The script will create this folder (if it doesn't exist) and save output images here.

How to Run:
-----------
1. Ensure you have Python 3 installed.
2. Install Pillow if needed:
      pip install Pillow
3. Open a terminal, navigate to project_folder, and run:
      python3 make_mockups3.py
"""

import os
from PIL import Image, ImageChops

# Define folder paths
INPUT_FOLDER = "output_webp"    # Folder containing input .webp files (filenames starting with "img_")
OVERLAYS_FOLDER = "overlays"
OUTPUT_FOLDER = "output2"       # Folder to save output images

# Create output folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Canvas size (same as the overlay PNG dimensions, i.e. the Photoshop file dimensions)
CANVAS_SIZE = (5400, 7200)
# Final exported image size and quality settings
OUTPUT_SIZE = (1500, 2000)
WEBP_QUALITY = 90

# Soft blend parameter for shadows (lower value gives a softer, less dark effect)
SHADOW_OPACITY = 0.3  # Value between 0 (no multiply) and 1 (full multiply)

# Define mockup configurations.
# artwork_width and artwork_height refer to the dimensions of the rotated artwork (as in the PS file)
mockups = {
    "mockup_30x40_tr": {
         "overlay_filename": "mockup_30x40_tr.png",
         "artwork_width": 2554,   # Target width of the rotated artwork (in the PS file)
         "artwork_height": 3185,  # Target height of the rotated artwork (in the PS file)
         "artwork_x": 1341,       # X position where the rotated artwork's bounding box should be placed on the canvas
         "artwork_y": 2007,       # Y position for the rotated artwork's bounding box
         "rotation": 7.43         # Rotation angle in degrees (clockwise)
    },
    "mockup_60x80_tr": {
         "overlay_filename": "mockup_60x80_tr.png",
         "artwork_width": 5106,
         "artwork_height": 6374,
         "artwork_x": 144,
         "artwork_y": 410,
         "rotation": 7.3
    }
}

def process_webp_image(webp_path):
    """Process a single webp image to create both mockup variants."""
    try:
        artwork = Image.open(webp_path).convert("RGBA")
    except Exception as e:
        print(f"Error opening {webp_path}: {e}")
        return

    # Remove the "img_" prefix from the filename, if present.
    original_base = os.path.splitext(os.path.basename(webp_path))[0]
    base_name = original_base[4:] if original_base.startswith("img_") else original_base

    # Process each mockup type for this artwork
    for key, config in mockups.items():
        print(f"Processing {original_base} for {key}...")

        # Create a blank canvas (white background) with PS dimensions
        canvas = Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 255))
        
        # --- Rotate and Scale Artwork ---
        # 1. Rotate the original artwork using the specified angle (clockwise) with expand=True.
        rotated_artwork = artwork.rotate(config["rotation"], resample=Image.BICUBIC, expand=True)
        
        # 2. Compute the uniform scale so that the rotated artwork's bounding box
        #    exactly matches the target dimensions.
        scale_x = config["artwork_width"] / rotated_artwork.width
        scale_y = config["artwork_height"] / rotated_artwork.height
        scale = (scale_x + scale_y) / 2  # average scale for uniform scaling
        
        final_artwork = rotated_artwork.resize(
            (int(rotated_artwork.width * scale), int(rotated_artwork.height * scale)),
            resample=Image.LANCZOS
        )
        
        # --- Positioning ---
        # Calculate the center where the PS file expects the rotated artwork.
        desired_center_x = config["artwork_x"] + config["artwork_width"] / 2
        desired_center_y = config["artwork_y"] + config["artwork_height"] / 2
        paste_x = int(desired_center_x - final_artwork.width / 2)
        paste_y = int(desired_center_y - final_artwork.height / 2)
        canvas.paste(final_artwork, (paste_x, paste_y), final_artwork)
        
        # --- Overlay Processing with Soft Multiply Blend ---
        overlay_path = os.path.join(OVERLAYS_FOLDER, config["overlay_filename"])
        try:
            overlay = Image.open(overlay_path).convert("RGBA")
        except Exception as e:
            print(f"Error opening overlay {overlay_path}: {e}")
            continue
        
        # Ensure the overlay is the same size as the canvas.
        if overlay.size != CANVAS_SIZE:
            overlay = overlay.resize(CANVAS_SIZE, resample=Image.LANCZOS)
        
        # Convert canvas and overlay to RGB (for blend operations)
        canvas_rgb = canvas.convert("RGB")
        overlay_rgb = overlay.convert("RGB")
        
        # Compute full multiply blend (often too dark)
        multiplied = ImageChops.multiply(canvas_rgb, overlay_rgb)
        # Create a soft blend by blending the original canvas with the full multiply result
        soft_blend = Image.blend(canvas_rgb, multiplied, SHADOW_OPACITY)
        
        # --- Masking the Handle Area ---
        # The overlay contains a "handle" area that should remain 100% opaque.
        # We use the alpha channel of the overlay: pixels with alpha >= 250 are considered handle.
        alpha_channel = overlay.getchannel("A")
        handle_mask = alpha_channel.point(lambda a: 255 if a >= 250 else 0)
        
        # Composite: in handle areas (mask=255), use the original overlay; elsewhere use the soft blend.
        final_rgb = Image.composite(overlay_rgb, soft_blend, handle_mask)
        
        # Resize the final composite to the export dimensions.
        final_image = final_rgb.resize(OUTPUT_SIZE, resample=Image.LANCZOS)
        
        # Naming convention: For 30x40 mockups use "small" prefix, for 60x80 use "large"
        new_prefix = "small" if key == "mockup_30x40_tr" else "large"
        output_filename = f"{new_prefix}_{base_name}.webp"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        final_image.save(output_path, "WEBP", quality=WEBP_QUALITY)
        print(f"Saved mockup to {output_path}")

def main():
    # List and debug print the files found in the input folder.
    try:
        files = os.listdir(INPUT_FOLDER)
    except Exception as e:
        print(f"Error accessing folder {INPUT_FOLDER}: {e}")
        return

    print("Files in input folder:", files)
    for filename in files:
        if filename.lower().endswith(".webp") and filename.startswith("img_"):
            file_path = os.path.join(INPUT_FOLDER, filename)
            print(f"Processing file: {file_path}")
            process_webp_image(file_path)

if __name__ == "__main__":
    main()

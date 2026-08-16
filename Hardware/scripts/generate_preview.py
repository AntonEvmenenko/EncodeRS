"""
================================================================================
KiCad PCB Render and Stitch Utility
================================================================================

Description:
This script automates the process of rendering 3D views of a KiCad PCB and 
combining them into a single, neatly cropped image. Specifically, it performs 
the following steps:
  1. Renders the top and bottom views of a specified KiCad PCB file using 
     the `kicad-cli` command-line tool.
  2. Stitches the two generated images side-by-side (Top view on the left, 
     Bottom view on the right).
  3. Calculates the exact bounding box of the visible PCB elements (ignoring 
     the transparent background).
  4. Crops the final image so that there is a uniform, user-defined padding 
     (in pixels) on all four sides of the boards.
     
Prerequisites:
  - KiCad (v9.0 or newer) installed, and `kicad-cli` accessible in your 
    system's PATH environment variable.
  - Python 3.x installed.
  - Python dependencies installed. You can install the required packages 
    by running: `pip install -r requirements.txt`
  
How to Use:
  1. Place this script in the same directory as your `.kicad_pcb` file, 
     or provide the full/relative path in the `PCB_FILENAME` parameter.
  2. Edit the "SCRIPT PARAMETERS" section below to match your project details.
     Make sure to change `PCB_FILENAME` to your actual board file name.
  3. Adjust `PADDING_PX` to change the amount of empty space around the final 
     board image. You can also tweak resolution, zoom, or rotation angles.
  4. Run the script from your terminal: 
     `python generate_preview.py`
================================================================================
"""

import subprocess
import sys
from PIL import Image

# ==========================================
# SCRIPT PARAMETERS
# ==========================================

# Files
PCB_FILENAME = "../EncoderRS.kicad_pcb"
OUTPUT_TOP = "preview/top.png"
OUTPUT_BOTTOM = "preview/bottom.png"
OUTPUT_FINAL = "preview/preview.png"

# Padding from the board bounding box to the image edges (in pixels)
PADDING_PX = 50

# Render settings (extracted from the provided commands)
RENDER_WIDTH = 950
RENDER_HEIGHT = 900
RENDER_ZOOM = 0.8
PRESET = "follow_pcb_editor"
QUALITY = "user"

# Rotation angles
ROTATE_TOP = "-50,0,110"
ROTATE_BOTTOM = "130,0,70"

# ==========================================
# MAIN CODE
# ==========================================

def render_image(output_file, rotate):
    """Executes the kicad-cli command to render the PCB."""
    print(f"Rendering {output_file}...")
    cmd = [
        "kicad-cli", "pcb", "render",
        "-w", str(RENDER_WIDTH),
        "-h", str(RENDER_HEIGHT),
        "--zoom", str(RENDER_ZOOM),
        "--preset", PRESET,
        "--quality", QUALITY,
        "--rotate", rotate,
        "--output", output_file,
        PCB_FILENAME
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] {output_file} successfully created.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to render {output_file}. Return code: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] 'kicad-cli' command not found. Ensure KiCad is installed and added to PATH.")
        sys.exit(1)

def main():
    # 1. Generate images
    render_image(OUTPUT_TOP, ROTATE_TOP)
    render_image(OUTPUT_BOTTOM, ROTATE_BOTTOM)

    print("Stitching and processing images...")
    
    # Open the generated images
    try:
        img_top = Image.open(OUTPUT_TOP).convert("RGBA")
        img_bottom = Image.open(OUTPUT_BOTTOM).convert("RGBA")
    except Exception as e:
        print(f"[ERROR] Failed to open images: {e}")
        sys.exit(1)

    # 2. Stitch images together (top.png on the left, bottom.png on the right)
    combined_width = img_top.width + img_bottom.width
    combined_height = max(img_top.height, img_bottom.height)
    
    # Create a blank transparent canvas
    combined = Image.new("RGBA", (combined_width, combined_height), (0, 0, 0, 0))
    
    # Paste the images
    combined.paste(img_top, (0, 0))
    combined.paste(img_bottom, (img_top.width, 0))

    # 3. Calculate the bounding box
    # Use the alpha channel to accurately determine object boundaries
    alpha_channel = combined.split()[3]
    bbox = alpha_channel.getbbox()

    if not bbox:
        print("[ERROR] Failed to determine board boundaries. The image is empty or has no transparent background.")
        sys.exit(1)

    left, upper, right, lower = bbox

    # Add our padding parameter (PADDING_PX) to all sides
    padded_left = left - PADDING_PX
    padded_upper = upper - PADDING_PX
    padded_right = right + PADDING_PX
    padded_lower = lower + PADDING_PX

    # Crop the image using the new bounding box with padding.
    # If the box goes beyond the original image, Pillow will automatically fill those areas with transparency.
    final_image = combined.crop((padded_left, padded_upper, padded_right, padded_lower))

    # Save the result
    final_image.save(OUTPUT_FINAL)
    print(f"[OK] Final image saved as '{OUTPUT_FINAL}' with a padding of {PADDING_PX}px.")

if __name__ == "__main__":
    main()
"""
================================================================================
KiCad to OnShape Texture Generator
================================================================================

Description:
This script automates the creation of texture images (top.png and bottom.png) 
for applying them as decals in OnShape.

Steps:
  1. Calls `kicad-cli` to render the top and bottom sides of the board 
     in strict orthogonal projection.
  2. Loads the resulting images.
  3. Finds the exact boundaries (Bounding Box) of the real pixels 
     using the alpha channel (ignoring the transparent background).
  4. Crops the images strictly to these boundaries with NO padding, 
     so the texture matches the PCB geometry 1:1 in OnShape.

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
  3. Run the script from your terminal: 
     `python generate_decals.py`
================================================================================
"""

import subprocess
import sys
import os
from PIL import Image

# ==========================================
# SCRIPT PARAMETERS
# ==========================================

# Path to your PCB file
PCB_FILENAME = "../EncoderRS.kicad_pcb"
OUTPUT_TOP = "decals/top.png"
OUTPUT_BOTTOM = "decals/bottom.png"

# Resolution of the initial render (higher = more detailed texture)
# kicad-cli will automatically fit the board into this square before we crop it
RENDER_WIDTH = 1200
RENDER_HEIGHT = 1200

# Render settings
QUALITY = "basic"
PRESET = "follow_pcb_editor"

# ==========================================
# MAIN CODE
# ==========================================

def render_and_crop(side, output_file):
    print(f"\nRendering {side} side to {output_file}...")
    
    # Build the command for kicad-cli
    # We use --side (top/bottom) and --background transparent. 
    # IMPORTANT: No --perspective or --rotate flags are used to ensure a flat view.
    cmd = [
        "kicad-cli", "pcb", "render",
        "-w", str(RENDER_WIDTH),
        "-h", str(RENDER_HEIGHT),
        "--side", side,
        "--background", "transparent",
        "--quality", QUALITY,
        "--preset", PRESET,
        "--output", output_file,
        PCB_FILENAME
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Rendering complete. Starting exact crop...")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to render {output_file}.")
        print(f"Return code: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] 'kicad-cli' utility not found. Make sure KiCad is installed and added to PATH.")
        sys.exit(1)

    # Open the image for cropping
    try:
        img = Image.open(output_file).convert("RGBA")
    except Exception as e:
        print(f"[ERROR] Failed to open image: {e}")
        sys.exit(1)

    # Find the boundaries (Bounding Box) using the alpha channel (transparency)
    alpha_channel = img.split()[3]
    bbox = alpha_channel.getbbox()

    if not bbox:
        print(f"[WARNING] Image {output_file} is completely transparent!")
        return

    # Crop the image strictly to the contour (NO padding!)
    # This guarantees the texture width and height perfectly match the PCBA dimensions.
    cropped_img = img.crop(bbox)
    
    # Overwrite the file
    cropped_img.save(output_file)
    print(f"[OK] File {output_file} cropped and saved. Final resolution: {cropped_img.width}x{cropped_img.height}")

def main():
    if not os.path.exists(PCB_FILENAME):
        print(f"[ERROR] PCB file '{PCB_FILENAME}' not found. Please check the PCB_FILENAME parameter.")
        sys.exit(1)
        
    print("Starting texture generation...")
    
    render_and_crop("top", OUTPUT_TOP)
    render_and_crop("bottom", OUTPUT_BOTTOM)
    
    print("\n[SUCCESS] Textures generated successfully!")

if __name__ == "__main__":
    main()
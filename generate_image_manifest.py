import json
import os
from datetime import datetime
from pathlib import Path

from PIL import Image

# --- Configuration ---
# The root directory where your general images (screenshots, diagrams, etc.) are stored.
IMAGE_ROOT_DIR = Path("/mnt/Web/images")
# The name of the output JSON file.
OUTPUT_JSON_FILE = Path("/mnt/Web/image_manifest.json")
# --- End Configuration ---


def get_file_info(image_path):
    """
    Gets basic file information for an image.
    
    Returns:
        dict: File size and last modified timestamp
    """
    try:
        stat_info = image_path.stat()
        return {
            "fileSize": stat_info.st_size,
            "lastModified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
        }
    except Exception:
        return {
            "fileSize": None,
            "lastModified": None
        }


def main():
    all_images_data = []
    processed_count = 0
    skipped_count = 0
    
    print(f"Scanning for images in: {IMAGE_ROOT_DIR.resolve()}")
    
    # Check if the directory exists
    if not IMAGE_ROOT_DIR.exists():
        print(f"Warning: Directory {IMAGE_ROOT_DIR} does not exist. Creating empty manifest.")
        with open(OUTPUT_JSON_FILE, "w") as f:
            json.dump([], f, indent=2)
        print(f"Empty manifest created: {OUTPUT_JSON_FILE.resolve()}")
        return
    
    # Walk through all subdirectories
    for root, _, files in os.walk(IMAGE_ROOT_DIR):
        for filename in files:
            # Support common image formats
            if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg")):
                continue
            
            image_path = Path(root) / filename
            
            try:
                relative_path = image_path.relative_to(IMAGE_ROOT_DIR)
                print(f"Processing: {relative_path}")
                
                # Get image dimensions
                # Note: SVG files might not work with PIL, handle that case
                try:
                    img = Image.open(image_path)
                    width, height = img.size
                    img.close()
                except Exception:
                    # If we can't open it (e.g., SVG), skip it
                    print(f"Warning: Could not read dimensions for {relative_path}, skipping.")
                    skipped_count += 1
                    continue
                
                # Get file metadata
                file_info = get_file_info(image_path)
                
                # Generate slug from relative_path
                slug = str(relative_path.with_suffix('')).replace(os.sep, '-')
                
                image_data = {
                    "relativePath": str(relative_path.as_posix()),
                    "filename": filename,
                    "width": width,
                    "height": height,
                    "slug": slug,
                    "fileSize": file_info["fileSize"],
                    "lastModified": file_info["lastModified"]
                }
                
                all_images_data.append(image_data)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                skipped_count += 1
    
    # Sort by relative path for consistency
    all_images_data.sort(key=lambda x: x["relativePath"])
    
    # Write output
    with open(OUTPUT_JSON_FILE, "w") as f:
        json.dump(all_images_data, f, indent=2)
    
    print(f"\nSuccessfully processed {processed_count} images.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} files due to errors.")
    print(f"Manifest file created: {OUTPUT_JSON_FILE.resolve()}")


if __name__ == "__main__":
    main()

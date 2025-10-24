#!/usr/bin/env python3
"""
Debug script to explore AVIF metadata extraction methods
"""

import sys
from pathlib import Path
import pillow_avif
from PIL import Image
from PIL.ExifTags import TAGS
import json

def explore_avif_metadata(image_path):
    """Explore different methods to extract metadata from AVIF files"""
    print(f"=== Exploring metadata for: {image_path} ===\n")
    
    try:
        img = Image.open(image_path)
        print(f"Image format: {img.format}")
        print(f"Image mode: {img.mode}")
        print(f"Image size: {img.size}")
        print(f"Image class: {type(img)}")
        print()
        
        # Method 1: Try standard getexif() instead of _getexif()
        print("--- Method 1: Standard getexif() ---")
        try:
            exif_dict = img.getexif()
            if exif_dict:
                print(f"Found {len(exif_dict)} EXIF entries:")
                for tag_id, value in exif_dict.items():
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    print(f"  {tag_name} ({tag_id}): {value}")
            else:
                print("No EXIF data found with getexif()")
        except Exception as e:
            print(f"Error with getexif(): {e}")
        print()
        
        # Method 2: Try _getexif() to confirm the error
        print("--- Method 2: Legacy _getexif() ---")
        try:
            exif_dict = img._getexif()
            if exif_dict:
                print(f"Found EXIF data with _getexif()")
            else:
                print("No EXIF data found with _getexif()")
        except Exception as e:
            print(f"Error with _getexif(): {e}")
        print()
        
        # Method 3: Check image info dictionary
        print("--- Method 3: Image info dictionary ---")
        if hasattr(img, 'info') and img.info:
            print("Image info contents:")
            for key, value in img.info.items():
                print(f"  {key}: {value}")
        else:
            print("No info dictionary or empty")
        print()
        
        # Method 4: Try XMP data
        print("--- Method 4: XMP data ---")
        try:
            xmp_data = img.getxmp()
            if xmp_data:
                print("XMP data found:")
                print(f"Type: {type(xmp_data)}")
                if isinstance(xmp_data, dict):
                    print(json.dumps(xmp_data, indent=2, default=str)[:1000] + "...")
                else:
                    print(str(xmp_data)[:1000] + "...")
            else:
                print("No XMP data found")
        except Exception as e:
            print(f"Error accessing XMP data: {e}")
        print()
        
        # Method 5: Check for other attributes
        print("--- Method 5: Available attributes ---")
        attributes = [attr for attr in dir(img) if not attr.startswith('_')]
        print("Available public attributes:")
        for attr in sorted(attributes):
            print(f"  {attr}")
        print()
        
        # Method 6: Try to access EXIF through other means
        print("--- Method 6: Alternative EXIF access ---")
        try:
            # Some formats store EXIF in the info dict under 'exif' key
            if 'exif' in img.info:
                print("Found 'exif' key in image info")
                exif_data = img.info['exif']
                print(f"EXIF data type: {type(exif_data)}")
                print(f"EXIF data length: {len(exif_data) if hasattr(exif_data, '__len__') else 'N/A'}")
            
            # Try accessing tag_v2 (IFD format)
            if hasattr(img, 'tag_v2'):
                print("Found tag_v2 attribute")
                tag_v2 = img.tag_v2
                print(f"tag_v2 type: {type(tag_v2)}")
                if hasattr(tag_v2, 'items'):
                    print("tag_v2 contents:")
                    for key, value in tag_v2.items():
                        tag_name = TAGS.get(key, f"Unknown_{key}")
                        print(f"  {tag_name} ({key}): {value}")
                        
        except Exception as e:
            print(f"Error with alternative EXIF access: {e}")
        
        img.close()
        
    except Exception as e:
        print(f"Error opening image: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_avif_metadata.py <path_to_avif_file>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"File not found: {image_path}")
        sys.exit(1)
    
    explore_avif_metadata(image_path)
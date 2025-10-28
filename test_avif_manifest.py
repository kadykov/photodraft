#!/usr/bin/env python3
"""
Test script to generate manifest for just the sample AVIF file
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from generate_manifest import get_exif_data, format_ifd_rational_value, parse_exif_date, clean_exif_string, ensure_numeric_type, filter_tags, classify_focal_length, calculate_crop_factor
from PIL import Image
import json

def test_avif_manifest_generation():
    """Test manifest generation for the sample AVIF file"""
    image_path = Path("sample-data/2025/05/17/GR002083.avif")
    
    if not image_path.exists():
        print(f"Error: Sample AVIF file not found at {image_path}")
        return
    
    print(f"Testing manifest generation for: {image_path}")
    
    try:
        # Get image dimensions
        temp_img = Image.open(image_path)
        width, height = temp_img.size
        temp_img.close()
        
        # Extract metadata
        exif_data = get_exif_data(image_path)
        
        print(f"\nExtracted EXIF data ({len(exif_data)} fields):")
        for key, value in sorted(exif_data.items()):
            print(f"  {key}: {value}")
        
        # Process the data like the main script would
        date_taken_str = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
        date_taken_iso = parse_exif_date(date_taken_str)
        
        title = exif_data.get("ProcessedTitle", None)
        description = exif_data.get("ProcessedDescription", None)
        tags = exif_data.get("ProcessedTags", [])
        if not isinstance(tags, list):
            tags = []
        
        # Filter out excluded tags
        tags = filter_tags(tags)
        
        lens_model_processed = clean_exif_string(exif_data.get("LensModel", None))
        camera_model_processed = clean_exif_string(exif_data.get("Model", None))
        
        flash_info_raw = exif_data.get("Flash")
        flash_fired_boolean = None
        if flash_info_raw is not None:
            # Handle both integer and string flash values
            if isinstance(flash_info_raw, int):
                flash_fired_boolean = bool(flash_info_raw & 0x1)
            elif isinstance(flash_info_raw, str) and "fired" in flash_info_raw.lower():
                flash_fired_boolean = True
            elif isinstance(flash_info_raw, str) and "not fire" in flash_info_raw.lower():
                flash_fired_boolean = False
        
        # Generate slug from relative_path
        relative_path = image_path.relative_to(Path("sample-data"))
        slug = str(relative_path.with_suffix('')).replace('/', '-')

        # Calculate crop factor and focal length classification
        focal_length = exif_data.get("FocalLength")
        focal_length_35mm = exif_data.get("FocalLengthIn35mmFilm")
        focal_length_category = classify_focal_length(focal_length_35mm)
        crop_factor = calculate_crop_factor(focal_length, focal_length_35mm)

        image_data = {
            "relativePath": str(relative_path.as_posix()),
            "filename": image_path.name,
            "year": 2025, "month": 5, "day": 17,
            "slug": slug,
            "width": width, "height": height,
            "dateTaken": date_taken_iso,
            "title": title, "description": description,
            "tags": tags,
            "cameraModel": camera_model_processed,
            "lensModel": lens_model_processed,
            "flash": flash_fired_boolean,
            "focalLength": ensure_numeric_type(format_ifd_rational_value(focal_length), 'float'),
            "focalLength35mmEquiv": ensure_numeric_type(focal_length_35mm, 'int'),
            "focalLengthCategory": focal_length_category,
            "cropFactor": crop_factor,
            "apertureValue": ensure_numeric_type(format_ifd_rational_value(exif_data.get("FNumber")), 'float'),
            "isoSpeedRatings": ensure_numeric_type(exif_data.get("ISOSpeedRatings"), 'int'),
            "exposureTime": ensure_numeric_type(format_ifd_rational_value(exif_data.get("ExposureTime")), 'float'),
            "creator": exif_data.get("ProcessedCreator", None),
            "copyright": exif_data.get("ProcessedCopyright", None),
            "notes": exif_data.get("ProcessedNotes", None),
        }
        
        print(f"\nGenerated manifest entry:")
        print(json.dumps(image_data, indent=2))
        
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_avif_manifest_generation()